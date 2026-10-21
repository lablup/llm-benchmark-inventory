# 서빙·자원 감시 기록

시작일: 2026-10-21

서빙·자원 인벤토리(`serving_inventory.csv`)의 도구·보드·계측기는 arXiv 논문으로 발견되는 것이 아니라 GitHub 릴리스, 저장소 커밋, PyPI 배포, 결과 페이지 갱신으로 바뀝니다. 그래서 벤치마크용 arXiv 수집기와 별도로 감시기(`serving_watch.py`)를 둡니다. 감시기는 표를 고치지 않고, 바뀐 것을 기록하고 알리는 일만 합니다(결정 기록 20번).

## 무엇을 보는가

감시 대상은 `serving-watch-sources.json`에 손으로 적습니다. 행 하나에 출처를 여러 개 둘 수 있습니다.

| 종류(kind) | 비교하는 값 | 쓰는 곳 |
|---|---|---|
| `github_release` | 저장소의 최신 릴리스 태그 | vLLM, GuideLLM, AIPerf, SGLang, MLPerf Inference, DCGM Exporter, all-smi |
| `github_commits` | 기본 브랜치의 최신 커밋(경로 지정 가능) | 릴리스를 내지 않는 저장소, 단계적 종료 중인 도구, 결과를 커밋으로 올리는 보드(InferenceX) |
| `github_org_repos` | 조직에서 이름 패턴에 맞는 가장 새 저장소 | MLCommons의 `inference_results_v*`, `endpoints*` (새 라운드 결과) |
| `pypi` | PyPI 최신 버전 | guidellm, aiperf, genai-perf |
| `page` | 페이지에서 스크립트·스타일·태그를 뺀 본문의 해시 | MLPerf Endpoints, Artificial Analysis 방법론, vLLM 대시보드·문서, nvidia-smi 문서 |

`page` 종류는 "무엇이 바뀌었는지"가 아니라 "바뀌었다"만 알려 줍니다. 본문이 200자 미만이면 오류 페이지로 보고 기록하지 않습니다.

## 어떻게 도는가

1. 매일 11:30 KST 정기 실행(`pages.yml`)에서 arXiv 수집 직후 `python3 serving_watch.py --notify`가 돕니다. 네트워크 실패는 논문 조사를 막지 않습니다(`continue-on-error`).
2. 관측값은 `serving-watch.json`에 남습니다. 출처마다 마지막 관측, 관측 시각, 최근 오류, 이전 값 이력(최대 20개)을 보관합니다. 첫 관측은 기준선(baseline)이며 변경으로 세지 않습니다.
3. 지난 실행과 값이 다르면 `changes`에 기록하고, 아직 알리지 않은 변경이 있으면 그날 이슈 하나를 `serving-watch` 라벨로 열어 담당자에게 배정합니다. 이슈에는 행 이름, 변경 종류, 날짜, 이전·이후 값, 출처 링크가 적힙니다.
4. 사람이 출처를 확인하고 필요한 행(운영 상태, 설명, 대표 측정값)과 `최근 확인일`을 고친 뒤 `python3 build_benchmark_inventory.py`와 `python3 build_site_data.py`를 돌립니다.

## 손으로 돌리기

```bash
GH_TOKEN=$(gh auth token) python3 serving_watch.py --dry-run   # 관측만 출력, 저장 없음
GH_TOKEN=$(gh auth token) python3 serving_watch.py             # serving-watch.json 갱신
GH_TOKEN=$(gh auth token) python3 serving_watch.py --notify    # 변경이 있으면 이슈 생성
```

GitHub API는 토큰 없이 시간당 60회라 토큰을 넣는 편이 안전합니다. 감시 출처를 추가·삭제할 때는 `python3 validate_inventory.py`가 행 id를 검사합니다.

## 한계

- 출처는 손으로 적은 것만 봅니다. 새 도구나 보드의 출현은 찾지 못하므로, 그런 발견은 여전히 사람이 합니다.
- 페이지 해시는 광고·날짜 같은 사소한 변경에도 반응할 수 있습니다. 자주 울리는 페이지는 출처를 결과 JSON이나 저장소로 바꾸는 편이 낫습니다.
- `perf.vllm.ai`처럼 서버가 자주 오류를 내는 페이지는 "접근 실패"로만 남고, 이전 관측을 유지합니다.
