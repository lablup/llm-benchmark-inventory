#!/usr/bin/env python3
"""llm_batch — paper-playbook 단계 1(API 비용·계정 차단 방지 규칙)을 코드로 강제하는 공용 배치 호출 모듈.

프로젝트 수집기는 "무엇을 보낼지(jobs)"와 "응답을 어떻게 읽을지(parse)"만 쓰고, 나머지는 이 모듈이 맡는다.

규칙(플레이북 단계 1)과 구현 위치
  잔액 먼저                 check_balance() — OpenRouter는 /credits, 다른 제공자는 None(잔액 API 없음)
  예상 비용 > 잔액의 절반    run_batch()가 시작 전에 멈춘다(allow_over_balance=True로만 통과)
  연기 시험(smoke) 10건      run_batch(smoke=10): 앞 10건을 순차 실행 → 빈 응답·parse 실패가 있으면 본 실행 전에 멈춘다
  동시성 ≤ 3, 고정 backoff   concurrency 기본 3(상한 3), 429/5xx/timeout은 2^n초(최대 60초)로 최대 6회
  증분 저장 + 재개           결과는 jsonl 한 줄씩 즉시 기록. 재개 시 response가 null·빈 문자열·error인 행은 완료로 세지 않는다
  reasoning 기본값 끄기      Provider.openrouter()는 reasoning을 끈 채로 보낸다(켜려면 reasoning=... 명시)
  온도 0, 출력 상한 명시     temperature=0.0, max_tokens 필수
  시작 시 현황 출력          jobs / done / pending / est_cost / balance
  실제 비용 기록             <out>.manifest.json 에 건수·비용·설정·입력 sha256, 그리고 verification/cost_log.jsonl 에 한 줄

사용(파이썬)
    import sys; sys.path.insert(0, str(Path.home() / "weekly-planner/scripts"))
    from llm_batch import Provider, run_batch
    p = Provider.openrouter("openai/gpt-5.6-sol-20260709", pin="openai", max_tokens=64,
                            price_in=2e-6, price_out=1e-5, env_file=ROOT / ".env")
    jobs = [{"id": t["id"], "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": t["text"]}]} for t in tasks]
    run_batch(jobs, p, ROOT / "outputs/run1.jsonl", parse=parse_fn, cost_cap_usd=5.0)

사용(명령줄; Codex에서도 같다)
    python3 ~/weekly-planner/scripts/llm_batch.py --jobs jobs.jsonl --out results.jsonl \
        --provider openrouter --model openai/gpt-5.6-sol-20260709 --pin openai --max-tokens 64 \
        [--smoke 10] [--concurrency 3] [--cost-cap 5] [--dry-run] [--balance]
    jobs.jsonl 행: {"id": "...", "messages": [...]}  또는 {"id": "...", "prompt": "...", "system": "..."}

제공자: openrouter(권장) · openai_compatible(Upstage https://api.upstage.ai/v1, OpenAI, vLLM 로컬 등) · anthropic(직접, SDK 필요)
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import fcntl
from functools import wraps
import tempfile
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

TOOL_RESPONSE_SUPPORT = 1  # for_response(job, assistant_message) parser hook
RESPONSES_SUPPORT = 1  # stateless Responses, normalized messages + preserved output items

MAX_CONCURRENCY = 3
RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


# ---------- 비밀키 ----------

def load_secret(name: str, env_file: Path | None = None) -> str:
    """환경변수 → .env 파일(KEY=value, export 허용, 따옴표 허용) 순서. 없으면 예외."""
    val = os.environ.get(name)
    if val:
        return val
    if env_file and Path(env_file).is_file():
        pat = re.compile(rf"^\s*(?:export\s+)?{re.escape(name)}\s*=\s*(.*?)\s*$")
        for line in Path(env_file).read_text(encoding="utf-8").splitlines():
            m = pat.match(line)
            if m:
                v = m.group(1).strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                    v = v[1:-1]
                if v:
                    return v
    raise RuntimeError(f"비밀키 {name}을 환경변수나 {env_file}에서 찾지 못했습니다.")


# ---------- 제공자 ----------

class RetryableError(Exception):
    pass


class FatalError(Exception):
    pass


@dataclass
class Provider:
    name: str
    model: str
    base_url: str = ""
    api_key: str = ""
    max_tokens: int = 256
    temperature: float | None = 0.0
    seed: int | None = None
    response_format: dict | None = None
    extra_body: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
    price_in: float | None = None    # USD / token
    price_out: float | None = None
    price_cached: float | None = None
    price_cache_write: float | None = None
    timeout: float = 120.0
    transport: Callable[["Provider", list[dict]], dict] | None = None  # 시험용 주입

    # -- 생성자들 --
    @classmethod
    def openrouter(cls, model: str, *, pin: str | None = None, reasoning: dict | None = None,
                   key_env: str = "OPENROUTER_API_KEY", env_file: Path | None = None, **kw) -> "Provider":
        extra: dict = {"usage": {"include": True}}
        extra["reasoning"] = reasoning if reasoning is not None else {"enabled": False}  # 기본 OFF
        if pin:
            extra["provider"] = {"order": [pin], "allow_fallbacks": False}
        return cls(name="openrouter", model=model, base_url="https://openrouter.ai/api/v1",
                   api_key=load_secret(key_env, env_file), extra_body=extra,
                   headers={"HTTP-Referer": "https://github.com/songys", "X-Title": "paper-batch"}, **kw)

    @classmethod
    def openai_compatible(cls, model: str, base_url: str, *, key_env: str | None = "OPENAI_API_KEY",
                          env_file: Path | None = None, **kw) -> "Provider":
        key = load_secret(key_env, env_file) if key_env else "EMPTY"
        return cls(name=base_url.split("//")[-1].split("/")[0], model=model, base_url=base_url.rstrip("/"), api_key=key, **kw)

    @classmethod
    def upstage(cls, model: str = "solar-pro3", *, env_file: Path | None = None, **kw) -> "Provider":
        return cls.openai_compatible(model, "https://api.upstage.ai/v1", key_env="UPSTAGE_API_KEY", env_file=env_file, **kw)

    @classmethod
    def anthropic(cls, model: str, *, key_env: str = "ANTHROPIC_API_KEY", env_file: Path | None = None, **kw) -> "Provider":
        return cls(name="anthropic", model=model, base_url="https://api.anthropic.com", api_key=load_secret(key_env, env_file), **kw)

    # -- 호출 --
    @classmethod
    def openai_responses(cls, model: str, *, key_env: str | None = "OPENAI_API_KEY",
                         env_file: Path | None = None, **kw) -> "Provider":
        key = load_secret(key_env, env_file) if key_env else "EMPTY"
        kw.setdefault("temperature", None)
        return cls(name="openai_responses", model=model, base_url="https://api.openai.com/v1",
                   api_key=key, **kw)

    def call(self, messages: list[dict]) -> dict:
        """{"text": str, "usage": dict|None, "cost": float|None, "raw": dict} 를 돌려준다. 재시도 가능한 오류는 RetryableError."""
        if self.transport:
            return self.transport(self, messages)
        if self.name == "anthropic":
            return self._call_anthropic(messages)
        if self.name == "openai_responses":
            return self._call_responses(messages)
        return self._call_chat(messages)

    def responses_body(self, messages: list[dict]) -> dict:
        # Chat 형식의 기록을 변환하고 같은 역할의 저장된 추론·출력 항목을 함께 재전송한다.
        items = []
        for message in messages:
            role = message.get("role")
            if role == "assistant" and "_responses_output" in message:
                items.extend(message["_responses_output"])
            elif role == "tool":
                items.append({"type": "function_call_output", "call_id": message["tool_call_id"],
                              "output": message["content"]})
            elif role in ("system", "developer", "user", "assistant"):
                if message.get("content"):
                    items.append({"role": role, "content": message["content"]})
                for call in message.get("tool_calls") or []:
                    if role != "assistant" or call.get("type") != "function":
                        raise FatalError("Responses: 지원하지 않는 도구 기록")
                    items.append({"type": "function_call", "call_id": call["id"],
                                  "name": call["function"]["name"], "arguments": call["function"]["arguments"]})
            else:
                raise FatalError("Responses: 지원하지 않는 메시지 역할")
        extra = dict(self.extra_body)
        if set(extra) & {"model", "input", "max_output_tokens", "previous_response_id", "store", "stream"}:
            raise FatalError("Responses: 요청·상태 설정을 extra_body에서 덮어쓸 수 없습니다")
        if self.seed is not None or self.response_format is not None:
            raise FatalError("Responses: seed/response_format 변환은 아직 지원하지 않습니다")
        if self.model.startswith("gpt-6") and self.temperature is not None:
            raise FatalError("GPT-6 Responses: temperature=None을 명시하세요")
        tools = []
        for tool in extra.pop("tools", []):
            if tool.get("type") != "function":
                raise FatalError("Responses: 현재 연결은 로컬 function 도구만 지원합니다")
            converted = {"type": "function", **tool.get("function", {k:v for k,v in tool.items() if k != "type"})}
            # Responses의 기본 strict 정규화로 기존 선택 인수가 필수로 바뀌지 않게 한다.
            converted.setdefault("strict", False)
            tools.append(converted)
        choice = extra.get("tool_choice")
        if isinstance(choice, dict) and "function" in choice:
            extra["tool_choice"] = {"type": "function", "name": choice["function"]["name"]}
        body = {"model": self.model, "input": items, "max_output_tokens": self.max_tokens,
                "store": False, "include": ["reasoning.encrypted_content"], **extra}
        if tools:
            body["tools"] = tools
        if self.temperature is not None:
            body["temperature"] = self.temperature
        return body

    def _call_responses(self, messages: list[dict]) -> dict:
        req = urllib.request.Request(
            f"{self.base_url}/responses", data=json.dumps(self.responses_body(messages)).encode(),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", **self.headers}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw = json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            if any(x in detail for x in ("insufficient_quota", "credit_balance_exhausted", "spend_limit_exceeded", "organization_usage_limit_exceeded", "enforced_spend_limit_reached")):
                raise FatalError(f"HTTP {e.code}: {detail[:700]}")
            error = RetryableError if e.code in RETRY_STATUS else FatalError
            raise error(f"HTTP {e.code}: {detail[:300]}")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            raise RetryableError(str(e))
        output = raw.get("output") or []
        texts, calls, refusals = [], [], []
        for item in output:
            if item.get("type") == "function_call":
                calls.append({"id": item.get("call_id"), "type": "function",
                              "function": {"name": item.get("name"), "arguments": item.get("arguments")}})
            elif item.get("type") == "message":
                for content in item.get("content") or []:
                    if content.get("type") == "output_text":
                        texts.append(content["text"])
                    elif content.get("type") == "refusal":
                        refusals.append(content.get("refusal", "refusal"))
        usage = raw.get("usage")
        if usage is not None:
            usage = {**usage, "prompt_tokens": usage.get("input_tokens"),
                     "completion_tokens": usage.get("output_tokens"),
                     "prompt_tokens_details": usage.get("input_tokens_details") or {},
                     "completion_tokens_details": usage.get("output_tokens_details") or {}}
        text = "\n".join(texts)
        message = {"role": "assistant", "content": text or None, "tool_calls": calls,
                   "_responses_output": output}
        if refusals:
            message["refusal"] = "\n".join(refusals)
        reason = (raw.get("incomplete_details") or {}).get("reason")
        finish = "length" if reason == "max_output_tokens" else ("tool_calls" if calls else "stop")
        error = None
        if raw.get("status") != "completed" or raw.get("error"):
            error = f"responses_{raw.get('status', 'unknown')}: {reason or 'response_not_completed'}"
        elif any(item.get("type") not in ("message", "function_call", "reasoning") for item in output):
            error = "responses_unsupported_output"
        if refusals:
            error = "refusal"
        return {"text": text, "usage": usage, "cost": self._cost(usage), "raw": raw,
                "assistant_message": message, "finish_reason": finish, "response_error": error}

    def _call_chat(self, messages: list[dict]) -> dict:
        body: dict[str, Any] = {"model": self.model, "messages": messages, "max_tokens": self.max_tokens, **self.extra_body}
        if self.base_url == "https://api.openai.com/v1" and self.model.startswith("gpt-6"):
            body["max_completion_tokens"] = body.pop("max_tokens")
        if self.temperature is not None:
            body["temperature"] = self.temperature
        if self.seed is not None:
            body["seed"] = self.seed
        if self.response_format:
            body["response_format"] = self.response_format
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions", data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", **self.headers}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                raw = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            if any(x in detail for x in ("insufficient_quota", "credit_balance_exhausted", "spend_limit_exceeded", "organization_usage_limit_exceeded", "enforced_spend_limit_reached")):
                raise FatalError(f"HTTP {e.code}: {detail[:700]}")
            detail = detail[:300]
            if e.code in RETRY_STATUS:
                raise RetryableError(f"HTTP {e.code}: {detail}")
            raise FatalError(f"HTTP {e.code}: {detail}")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            raise RetryableError(str(e))
        if "error" in raw and not raw.get("choices"):
            raise RetryableError(f"API error: {json.dumps(raw['error'])[:300]}")
        text = ((raw.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        usage = raw.get("usage")
        return {"text": text, "usage": usage, "cost": self._cost(usage), "raw": raw}

    def _call_anthropic(self, messages: list[dict]) -> dict:
        try:
            import anthropic  # noqa
        except ImportError:
            raise FatalError("anthropic SDK가 없습니다: pip install anthropic")
        client = anthropic.Anthropic(api_key=self.api_key, timeout=self.timeout, max_retries=0)
        system = "\n".join(m["content"] for m in messages if m["role"] == "system") or None
        msgs = [m for m in messages if m["role"] != "system"]
        kw: dict[str, Any] = {"model": self.model, "max_tokens": self.max_tokens, "messages": msgs, **self.extra_body}
        if system:
            kw["system"] = system
        if self.temperature is not None:
            kw["temperature"] = self.temperature
        try:
            resp = client.messages.create(**kw)
        except anthropic.RateLimitError as e:
            raise RetryableError(str(e))
        except anthropic.APIStatusError as e:
            if e.status_code in RETRY_STATUS:
                raise RetryableError(str(e))
            raise FatalError(str(e))
        except anthropic.APIConnectionError as e:
            raise RetryableError(str(e))
        text = "".join(getattr(b, "text", "") for b in resp.content)
        usage = {"prompt_tokens": resp.usage.input_tokens, "completion_tokens": resp.usage.output_tokens}
        return {"text": text, "usage": usage, "cost": self._cost(usage), "raw": resp.model_dump()}

    def _cost(self, usage: dict | None) -> float | None:
        if not usage:
            return None
        if isinstance(usage.get("cost"), (int, float)):
            return float(usage["cost"])
        if self.price_in is not None and self.price_out is not None:
            if any(type(usage.get(k)) is not int or usage[k] < 0 for k in ("prompt_tokens", "completion_tokens")):
                return None
            details = usage.get("prompt_tokens_details") or {}
            cached = details.get("cached_tokens", 0) or 0
            writes = details.get("cache_write_tokens", 0) or 0
            if any(type(n) is not int or n < 0 for n in (cached, writes)):
                return None
            if self.price_cached is not None and self.price_cache_write is not None:
                uncached = usage.get("prompt_tokens", 0) - cached - writes
                if uncached < 0:
                    return None
                return uncached*self.price_in + cached*self.price_cached + writes*self.price_cache_write + usage.get("completion_tokens", 0)*self.price_out
            return usage.get("prompt_tokens", 0) * self.price_in + usage.get("completion_tokens", 0) * self.price_out
        return None

    def settings(self) -> dict:
        return {"provider": self.name, "model": self.model, "base_url": self.base_url, "max_tokens": self.max_tokens,
                "temperature": self.temperature, "seed": self.seed, "response_format": self.response_format,
                "extra_body": self.extra_body, "price_in": self.price_in, "price_out": self.price_out, "price_cached": self.price_cached, "price_cache_write": self.price_cache_write}


# ---------- 잔액·비용 ----------

def check_balance(p: Provider) -> float | None:
    """남은 금액(USD). OpenRouter만 지원. 나머지는 None(잔액 API 없음 → 콘솔에서 확인)."""
    if p.name != "openrouter":
        return None
    req = urllib.request.Request(f"{p.base_url}/credits", headers={"Authorization": f"Bearer {p.api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode()).get("data", {})
        return float(d.get("total_credits", 0)) - float(d.get("total_usage", 0))
    except Exception as e:  # 잔액 확인 실패는 실행을 막지 않지만 기록한다
        print(f"[llm_batch] 잔액 확인 실패: {e}", file=sys.stderr)
        return None


def _approx_tokens(messages: list[dict]) -> int:
    chars = sum(len(str(m.get("content", ""))) for m in messages)
    return max(1, chars // 3)  # 한국어·영어 섞인 텍스트의 보수적 추정


def estimate_cost(jobs: list[dict], p: Provider, avg_in_tokens: float | None = None, avg_out_tokens: float | None = None) -> float | None:
    if p.price_in is None or p.price_out is None:
        return None
    n = len(jobs)
    tin = avg_in_tokens if avg_in_tokens is not None else (sum(_approx_tokens(j["messages"]) for j in jobs) / n if n else 0)
    tout = avg_out_tokens if avg_out_tokens is not None else p.max_tokens * 0.5
    return n * (tin * p.price_in + tout * p.price_out)


# ---------- 실행 ----------

def normalize_job(j: dict) -> dict:
    if "messages" not in j:
        msgs = []
        if j.get("system"):
            msgs.append({"role": "system", "content": j["system"]})
        msgs.append({"role": "user", "content": j["prompt"]})
        j = {**j, "messages": msgs}
    if "id" not in j:
        raise ValueError("job에 id가 없습니다")
    return j


def load_done(out_path: Path) -> set[str]:
    """완료 집합. response가 null/빈 문자열이거나 error가 있으면 미완료(재개 때 다시 돈다)."""
    done: set[str] = set()
    if not out_path.is_file():
        return done
    for line in out_path.read_text(encoding="utf-8").split("\n"):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (r.get("response") or r.get("tool_calls")) and not r.get("error") and r.get("parsed", True) is not None:
            done.add(str(r["id"]))
    return done


def _one(job: dict, p: Provider, parse: Callable[[str], Any] | None, max_retries: int) -> dict:
    rid = str(job["id"])
    req_sha = hashlib.sha256(json.dumps({"model": p.model, "messages": job["messages"], **p.settings()}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    rec: dict[str, Any] = {"id": rid, "model": p.model, "provider": p.name, "request_sha256": req_sha,
                           "response": None, "parsed": None, "usage": None, "cost_usd": None, "error": None,
                           "attempts": 0, "ts": None, "latency_s": None}
    for k, v in job.items():
        if k not in ("messages", "prompt", "system") and k not in rec:
            rec[k] = v  # 메타 보존
    for attempt in range(1, max_retries + 2):
        rec["attempts"] = attempt
        t0 = time.time()
        try:
            out = p.call(job["messages"])
        except RetryableError as e:
            rec["error"] = f"retryable: {e}"
            if attempt > max_retries:
                break
            time.sleep(min(2 ** attempt, 60))
            continue
        except FatalError as e:
            rec["error"] = f"fatal: {e}"
            break
        rec["latency_s"] = round(time.time() - t0, 2)
        rec["ts"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        rec["response"], rec["usage"] = out["text"], out["usage"]
        if p.extra_body.get("logprobs"):
            rec["raw_response"] = out.get("raw") or {}
        raw = out.get("raw") or {}
        choice = (raw.get("choices") or [{}])[0]
        message = out.get("assistant_message", choice.get("message") or {})
        rec["assistant_message"] = message
        rec["tool_calls"] = message.get("tool_calls") or []
        rec["finish_reason"] = out.get("finish_reason", choice.get("finish_reason"))
        rec["refusal"] = message.get("refusal")
        if p.name == "openai_responses":
            rec["raw_response"] = raw
        rec["response_id"] = raw.get("id")
        rec["returned_model"] = raw.get("model")
        rec["service_tier"] = raw.get("service_tier")
        rec["cost_usd"] = out["cost"] if out["cost"] is not None else p._cost(out["usage"])
        if out.get("response_error"):
            rec["error"] = out["response_error"]
            break
        if not out["text"].strip() and not rec["tool_calls"]:
            rec["error"] = "refusal" if rec.get("refusal") else "empty"  # 빈 응답은 완료가 아니다
            break
        rec["error"] = None
        if parse:
            try:
                if hasattr(parse, "for_response"):
                    rec["parsed"] = parse.for_response(job, message)
                else:
                    rec["parsed"] = (parse.for_job(job, out["text"]) if hasattr(parse, "for_job") else parse(out["text"]))
                if rec["parsed"] is None:
                    raise ValueError("parse returned null")
            except Exception as e:
                rec["error"] = f"parse: {e}"
        break
    return rec


def _single_run(fn):
    @wraps(fn)
    def locked(*args, **kwargs):
        lock_path = Path(tempfile.gettempdir()) / f"paper-llm-batch-{os.getuid()}.lock"
        with lock_path.open("a+") as guard:
            try:
                fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError("다른 공용 LLM 실행이 진행 중입니다")
            try:
                return fn(*args, **kwargs)
            finally:
                fcntl.flock(guard, fcntl.LOCK_UN)
    return locked


@_single_run
def run_batch(jobs: list[dict], p: Provider, out_path: Path, *, parse: Callable[[str], Any] | None = None,
              concurrency: int = 3, smoke: int = 10, max_retries: int = 6, cost_cap_usd: float | None = None,
              balance_fraction: float = 0.5, allow_over_balance: bool = False, resume: bool = True,
              dry_run: bool = False, stage: str = "all", max_failures: int | None = None,
              confirmed_balance_usd: float | None = None, estimated_cost_usd: float | None = None, log: Callable[[str], None] = print) -> dict:
    """jobs를 돌려 out_path(jsonl)에 기록한다. 반환: 요약 dict(manifest와 같음).

    stage: "smoke"(연기 시험만) | "full"(연기 시험 없이) | "all"(연기 시험 → 통과하면 본 실행)
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    jobs = [normalize_job(j) for j in jobs]
    ids = [str(j["id"]) for j in jobs]
    if len(set(ids)) != len(ids):
        raise ValueError("job id가 중복됩니다")
    concurrency = max(1, min(concurrency, MAX_CONCURRENCY))
    max_retries = max(0, min(max_retries, 6))
    if not resume and out_path.exists() and out_path.stat().st_size:
        raise ValueError("기존 응답 파일에 resume=False로 추가할 수 없습니다")
    prior_spent = 0.0
    if resume and out_path.is_file():
        expected = {str(j["id"]): hashlib.sha256(json.dumps({"model": p.model, "messages": j["messages"], **p.settings()}, sort_keys=True, ensure_ascii=False).encode()).hexdigest() for j in jobs}
        for line in out_path.read_text(encoding="utf-8").split("\n"):
            if not line.strip():
                continue
            old = json.loads(line)
            if old.get("id") not in expected or old.get("request_sha256") != expected[old["id"]]:
                raise ValueError("재개 요청 해시 불일치: 입력·모델·설정을 바꾸어 재개할 수 없습니다")
            if old.get("cost_usd") is None:
                raise ValueError("이전 응답 비용 미확인: 비용 확인 후 새 실행을 계획하세요")
            prior_spent += old.get("cost_usd") or 0.0
    done = load_done(out_path) if resume else set()
    pending = [j for j in jobs if str(j["id"]) not in done]
    est = estimated_cost_usd if estimated_cost_usd is not None else estimate_cost(pending, p)
    balance = confirmed_balance_usd if confirmed_balance_usd is not None else (None if dry_run else check_balance(p))
    jobs_sha = hashlib.sha256(json.dumps(jobs, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    log(f"[llm_batch] {p.name}/{p.model}  jobs {len(jobs)} · done {len(done)} · pending {len(pending)} · "
        f"est_cost {'?' if est is None else f'${est:.2f}'} · balance {'?' if balance is None else f'${balance:.2f}'} · "
        f"concurrency {concurrency} · reasoning {p.extra_body.get('reasoning', '(제공자 기본)')}")
    summary = {"provider": p.settings(), "out": str(out_path), "jobs_sha256": jobs_sha, "n_jobs": len(jobs),
               "n_done_before": len(done), "n_pending": len(pending), "est_cost_usd": est, "balance_before": balance,
               "started": started, "stage": stage, "dry_run": dry_run,
               "cost_before_usd": prior_spent, "cost_cap_usd": cost_cap_usd,
               "balance_source": "user_reported" if confirmed_balance_usd is not None else "provider_api_or_unavailable"}
    if not pending:
        log("[llm_batch] 할 일이 없습니다(모두 완료).")
        return _finish(summary, out_path, 0, 0.0, 0, log)
    if balance is not None and est is not None and est > balance * balance_fraction and not allow_over_balance:
        raise SystemExit(f"[llm_batch] 예상 비용 ${est:.2f}가 잔액 ${balance:.2f}의 {balance_fraction:.0%}를 넘습니다. "
                         f"사용자 확인 뒤 allow_over_balance=True로 다시 실행하세요.")
    if cost_cap_usd is not None and est is not None and est > cost_cap_usd:
        log(f"[llm_batch] 경고: 예상 비용 ${est:.2f} > 상한 ${cost_cap_usd:.2f}. 상한에 닿으면 중단합니다.")
    if dry_run:
        log("[llm_batch] dry-run: 호출하지 않습니다. 첫 job 요청 본문:")
        preview = p.responses_body(pending[0]["messages"]) if p.name == "openai_responses" else {
            "model": p.model, "messages": pending[0]["messages"], "max_tokens": p.max_tokens,
            "temperature": p.temperature, **p.extra_body}
        log(json.dumps(preview, ensure_ascii=False, indent=1)[:1500])
        return _finish(summary, out_path, 0, 0.0, 0, log)

    lock = threading.Lock()
    spent = 0.0
    n_ok = n_fail = 0
    stop = threading.Event()

    def record(rec: dict) -> None:
        nonlocal spent, n_ok, n_fail
        with lock:
            with out_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if rec.get("cost_usd") is not None:
                spent += rec["cost_usd"]
            else:
                stop.set()
            if str(rec.get("error") or "").startswith("fatal:"):
                stop.set()
            if rec.get("error"):
                n_fail += 1
                if max_failures is not None and n_fail >= max_failures:
                    stop.set()
            else:
                n_ok += 1
            if cost_cap_usd is not None and spent + prior_spent >= cost_cap_usd:
                stop.set()

    if cost_cap_usd is not None and prior_spent >= cost_cap_usd:
        return _finish(summary, out_path, 0, 0.0, 0, log, aborted="cost_cap")

    # 연기 시험
    if stage in ("smoke", "all") and smoke > 0:
        head, pending = pending[:smoke], pending[smoke:]
        log(f"[llm_batch] 연기 시험 {len(head)}건(순차)…")
        bad = []
        for j in head:
            if stop.is_set():
                break
            rec = _one(j, p, parse, max_retries)
            record(rec)
            if rec["error"]:
                bad.append((rec["id"], rec["error"]))
            log(f"  {rec['id']}: {'OK' if not rec['error'] else rec['error']} · {(rec['response'] or '')[:80]!r}"
                + (f" → {json.dumps(rec['parsed'], ensure_ascii=False)[:80]}" if rec.get("parsed") is not None else ""))
        if stop.is_set():
            return _finish(summary, out_path, n_ok, spent, n_fail, log, aborted="cost_or_provider_stop")
        if bad:
            log(f"[llm_batch] 연기 시험 실패 {len(bad)}건 → 본 실행을 시작하지 않습니다. 형식·프롬프트·parse를 고친 뒤 재실행하세요(완료분은 건너뜀).")
            return _finish(summary, out_path, n_ok, spent, n_fail, log, aborted="smoke_failed")
        if stage == "smoke":
            log("[llm_batch] 연기 시험만 요청됨. 출력을 눈으로 확인한 뒤 stage='full'로 본 실행.")
            return _finish(summary, out_path, n_ok, spent, n_fail, log)
        log(f"[llm_batch] 연기 시험 통과(${spent:.4f}). 본 실행 {len(pending)}건.")

    # 본 실행
    t0 = time.time()
    try:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futs = {}
            it = iter(pending)
            # 동시성 상한만큼만 대기열에 넣어 중단 신호에 빨리 반응
            for j in it:
                futs[pool.submit(_one, j, p, parse, max_retries)] = j
                if len(futs) >= concurrency:
                    break
            while futs:
                for fut in as_completed(list(futs)):
                    futs.pop(fut)
                    record(fut.result())
                    total = n_ok + n_fail
                    if total % 25 == 0:
                        rate = total / max(1e-9, time.time() - t0)
                        log(f"  진행 {total}/{len(pending) + (smoke if stage != 'full' else 0)} · 실패 {n_fail} · ${spent:.3f} · {rate:.1f}/s")
                    if stop.is_set():
                        break
                    nxt = next(it, None)
                    if nxt is not None:
                        futs[pool.submit(_one, nxt, p, parse, max_retries)] = nxt
                if stop.is_set():
                    log(f"[llm_batch] 비용·제공자·실패 제한으로 중단(진행 중인 호출은 기록).")
                    for f in futs:
                        record(f.result())
                    futs.clear()
    except KeyboardInterrupt:
        log("[llm_batch] 중단됨. 기록된 결과는 보존됐고 같은 명령으로 재개됩니다.")
        return _finish(summary, out_path, n_ok, spent, n_fail, log, aborted="interrupted")
    return _finish(summary, out_path, n_ok, spent, n_fail, log, aborted="cost_or_provider_stop" if stop.is_set() else None)


def _finish(summary: dict, out_path: Path, n_ok: int, spent: float, n_fail: int, log, aborted: str | None = None) -> dict:
    summary.update({"finished": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "n_ok_this_run": n_ok,
                    "n_fail_this_run": n_fail, "cost_this_run_usd": round(spent, 6), "cost_total_usd": round(summary.get("cost_before_usd", 0) + spent, 6), "aborted": aborted,
                    "n_done_total": len(load_done(out_path))})
    mp = out_path.with_suffix(out_path.suffix + ".manifest.json")
    mp.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    # 프로젝트 verification/cost_log.jsonl 에 한 줄(있을 때만; 프로젝트 루트 = out_path의 조상 중 verification/ 이 있는 곳)
    for anc in ([] if summary.get("dry_run") else [out_path.parent, *out_path.parents]):
        v = anc / "verification"
        if v.is_dir():
            with (v / "cost_log.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps({k: summary[k] for k in ("started", "finished", "out", "n_ok_this_run", "n_fail_this_run",
                                                          "cost_this_run_usd", "aborted")} | {"model": summary["provider"]["model"]},
                                   ensure_ascii=False) + "\n")
            break
    log(f"[llm_batch] 끝. 이번 실행 성공 {n_ok} · 실패 {n_fail} · ${spent:.4f} · 누적 완료 {summary['n_done_total']}/{summary['n_jobs']}"
        + (f" · 중단 사유 {aborted}" if aborted else "") + f" · manifest {mp.name}")
    return summary


# ---------- 명령줄 ----------

def _cli() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--jobs", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--provider", choices=["openrouter", "upstage", "openai", "anthropic", "local"], default="openrouter")
    ap.add_argument("--model", required=True)
    ap.add_argument("--base-url", help="local/openai_compatible용")
    ap.add_argument("--pin", help="OpenRouter 제공자 고정(예: openai, anthropic)")
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--json-schema", type=Path, help="response_format json_schema 파일")
    ap.add_argument("--price-in", type=float); ap.add_argument("--price-out", type=float)
    ap.add_argument("--env-file", type=Path, default=Path(".env"))
    ap.add_argument("--smoke", type=int, default=10)
    ap.add_argument("--stage", choices=["smoke", "full", "all"], default="all")
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--cost-cap", type=float)
    ap.add_argument("--allow-over-balance", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--balance", action="store_true", help="잔액만 확인")
    a = ap.parse_args()
    kw = dict(max_tokens=a.max_tokens, temperature=a.temperature, price_in=a.price_in, price_out=a.price_out)
    if a.json_schema:
        kw["response_format"] = {"type": "json_schema", "json_schema": json.loads(a.json_schema.read_text())}
    if a.provider == "openrouter":
        p = Provider.openrouter(a.model, pin=a.pin, env_file=a.env_file, **kw)
    elif a.provider == "upstage":
        p = Provider.upstage(a.model, env_file=a.env_file, **kw)
    elif a.provider == "openai":
        p = Provider.openai_compatible(a.model, "https://api.openai.com/v1", key_env="OPENAI_API_KEY", env_file=a.env_file, **kw)
    elif a.provider == "anthropic":
        p = Provider.anthropic(a.model, env_file=a.env_file, **kw)
    else:
        p = Provider.openai_compatible(a.model, a.base_url or "http://localhost:8000/v1", key_env=None, **kw)
    if a.balance:
        b = check_balance(p)
        print("잔액:", "확인 불가(제공자 콘솔에서 확인)" if b is None else f"${b:.2f}")
        return 0
    jobs = [json.loads(l) for l in a.jobs.read_text(encoding="utf-8").split("\n") if l.strip()]
    run_batch(jobs, p, a.out, concurrency=a.concurrency, smoke=a.smoke, cost_cap_usd=a.cost_cap,
              allow_over_balance=a.allow_over_balance, dry_run=a.dry_run, stage=a.stage)
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
