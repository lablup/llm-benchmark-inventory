# llm-benchmark-inventory 작업 규칙

## 라이선스가 명시되지 않은 벤치마크의 표기 (2026-10-21 결정, DECISIONS.md 18번)

라이선스 열에는 "확인했는데 없음"과 "확인하지 못함"을 구분해 적는다. `확인 불가`, `unknown`은 쓰지 않는다.

| 상황 | `라이선스` 열 | `상업적 이용`·`수정·파생`·`재배포` 열 | 공개 여부 |
|---|---|---|---|
| 논문·데이터 카드·공식 저장소를 확인했는데 라이선스 문구가 없음 | `미표기(확인한 곳)` 예: `미표기(논문·공식 저장소 확인)` | 세 열 모두 `저작권 전부 보유` | 공개 가능 |
| 비공개 저장소 등으로 확인 자체를 못 함 | `미확인` | 세 열 모두 `미확인` | 공개하지 않음(재조사 대상) |

- 라이선스가 없는 공개물은 저작권 전부 보유(all rights reserved) 상태로 간주한다. 그래서 상업적 이용·수정·파생·재배포를 모두 불가로 보고, 이용 전 저자 확인이 필요하다는 뜻으로 `저작권 전부 보유`라고 적는다.
- `lm-eval 지원`도 같은 구분을 쓴다. 공식 저장소에 lm-eval 언급이 없으면 `미표기`, 확인하지 못했으면 `미확인`.
- 자동 조사 파이프라인의 초안 단계는 다섯 필드(라이선스, 상업적 이용, 수정·파생, 재배포, lm-eval 지원)를 `미확인`으로 두고, 공개 단계(`publication_checks.py`)에서 근거로 해소한다. `미표기`는 부재 근거(absence evidence) `{"source_url": 공식 카드 URL, "absent": true}`가 있어야 하며, 코드는 공식 카드와 PDF 본문에 라이선스 단어가 하나라도 있으면 부재 주장을 거부한다. `미확인`이 남은 행은 공개되지 않는다.
- 사람이 표를 고칠 때는 `라이선스` 열만 적고 `python3 build_benchmark_inventory.py`를 돌린다. 파생 세 열은 스크립트가 채운다. 이어서 `python3 build_site_data.py`로 사이트 데이터를 갱신한다.

## 자동 조사가 읽는 범위

- 공식 카드 = README + 저장소 루트의 LICENSE 파일. GitHub는 API의 license 엔드포인트로 파일 이름과 무관하게 감지된 라이선스 파일(SPDX 식별자 포함)을 읽고, Hugging Face 데이터셋은 `LICENSE`, `LICENSE.md`, `LICENSE.txt`와 LICENCE 철자 변형을 차례로 찾는다(`research_pipeline.get_official_resource`).
- LICENSE 파일이 있으면 카드 본문 끝에 `## LICENSE file: 이름 (SPDX …)` 절로 붙고, 메타데이터 `license_file`에 이름·SPDX·sha256이 남는다. 이 경우 부재 주장은 코드가 거부한다.
- 여전히 읽지 않는 것: 루트가 아닌 하위 폴더의 라이선스 파일, 데이터 파일 안에 들어 있는 라이선스 문구, 논문·저장소 밖(학회 사이트, 별도 데이터 호스팅)의 이용 약관. `미표기(논문·공식 저장소 확인)` 행도 이용 전에 이 범위 밖을 한 번 더 본다.

## 서빙·자원 표 갱신 (2026-10-21 결정, DECISIONS.md 20번)

- 서빙·자원 표(`serving_inventory.csv`, `serving_reference_values.csv`)는 자동으로 바뀌지 않는다. 감시기 `serving_watch.py`가 매일 `serving-watch-sources.json`의 출처(GitHub 릴리스·커밋, 조직 저장소, PyPI, 페이지 본문 해시)를 보고 `serving-watch.json`에 기록하며, 변경이 있으면 `serving-watch` 라벨 이슈 하나를 연다.
- 이슈를 받으면 출처를 확인하고 행과 `최근 확인일`을 손으로 고친 뒤 `python3 build_benchmark_inventory.py`, `python3 build_site_data.py`를 돌린다.
- 감시 대상을 더하거나 빼려면 `serving-watch-sources.json`만 고친다. 행 id는 `validate_inventory.py`가 검사한다. 자세한 설명은 `docs/serving-watch.md`.
