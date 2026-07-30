# LLM 벤치마크 인벤토리

![도시와 네트워크를 표현한 파란색 배너](./assets/network.png)

한국어 및 영어 LLM 벤치마크의 평가 범위, 과제 예시, 라이선스와 실행 지원 정보를 정리한 목록입니다.
이 문서는 빠른 탐색을 위한 요약이며, 전체 필드는 원본 CSV에서 확인할 수 있습니다.

- [웹에서 인벤토리 탐색](https://reimagined-adventure-77j6g4k.pages.github.io/)
- [한국어 벤치마크 CSV](./korean_benchmark_inventory.csv)
- [영어 벤치마크 CSV](./english_benchmark_inventory.csv)

## 읽는 방법

- **상업적 이용**은 데이터 카드 등에 표시된 라이선스를 기준으로 `가능`, `불가`, `확인 불가`, `조건 확인 필요`로 정리했습니다.
- 라이선스는 2026-07-28에 각 데이터 카드와 저장소에서 일괄 확인한 것입니다. 이후 바뀔 수 있으므로 실제 이용 전에 원문을 다시 확인해야 합니다.
- 영어 벤치마크의 `대표 예시·설명`은 한국어 독자를 위한 번역·요약이 많습니다. `예시 표기` 열에서 영문 예시와 한국어 요약을 구분했습니다.
- `lm-eval 지원`은 오픈소스 평가 프레임워크 [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness)(EleutherAI)에 해당 태스크가 내장돼 있는지를 뜻합니다. 인벤토리 작성 시 확인한 상태이며 최신 버전에서 달라질 수 있습니다.

## 한국어 벤치마크

총 50개 · 상업적 이용 가능 26개 · 불가 8개 · 확인 불가 10개 · 조건 확인 필요 6개

### 이해·언어

| 벤치마크 | 평가 축 | 설명 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |
|---|---|---|---|---|---|
| [KMMLU](https://huggingface.co/datasets/HAERAE-HUB/KMMLU) | 이해(지식 MCQ) | 한국 국가시험과 자격시험의 원본 문항으로 만든 45과목 4지선다 벤치마크로, test 셋만 35,030문항이다. 영어 MMLU를 번역한 것이 아니라 한국어로 출제된 원본 문항이며, 문항마다 사람의 정답률이 붙어 있다. | **가능** | CC-BY-ND-4.0(원본 무수정만)<br>수정·파생: 불가<br>재배포: 원본 그대로만 | 내장 |
| [KMMLU-Pro](https://huggingface.co/datasets/LGAI-EXAONE/KMMLU-Pro) | 이해(전문지식) | KMMLU의 확장판으로, 한국 전문 자격시험에서 가져온 전문지식 문항 약 2,800개를 담았다(LGAI-EXAONE). | **불가** | CC-BY-NC-ND-4.0<br>수정·파생: 불가<br>재배포: 원본 그대로만<br>학습 코퍼스 포함 금지 조항. HF 게이트(접근 동의 필요) | 없음 |
| [HAE_RAE_BENCH](https://huggingface.co/datasets/HAERAE-HUB/HAE_RAE_BENCH_1.1) | 이해(어휘·문화) | 표준어, 외래어, 희귀어, 일반상식, 역사의 다섯 가지 서브태스크로 한국어 고유 지식을 측정한다. | **조건 확인 필요** | 1.0 미기재 / 1.1 CC-BY-NC-ND<br>수정·파생: 버전별 확인<br>재배포: 버전별 확인<br>버전별 라이선스 상이. 1.0은 미기재, 1.1은 CC-BY-NC-ND | 내장 |
| [Global-MMLU (ko)](https://huggingface.co/datasets/CohereLabs/Global-MMLU) | 이해(국제 비교) | MMLU 57과목을 전문 번역·검수한 다국어판의 한국어 서브셋. 문항마다 문화 민감도 태그가 붙어 있다. | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>구 조직 경로(CohereForAI)는 404. CohereLabs 경로 사용 | 내장 |
| [CLIcK](https://huggingface.co/datasets/EunsuKim/CLIcK) | 문화·언어 MCQ | 한국 시험과 교과서(KIIP 등)에서 가져온 문항 1,995개로 한국 문화와 언어 지식을 묻는다. 11개 하위 범주로 나뉜다. | **확인 불가** | 미확인<br>수정·파생: 확인 불가<br>재배포: 확인 불가<br>카드에 라이선스 미표기. 이용 전 저자 확인 필요 | 내장 |
| [CSAT-QA](https://huggingface.co/datasets/HAERAE-HUB/csatqa) | 독해·문법 MCQ | 수능 국어 기출 5지선다를 문법, 문학, 독해(인문·과학·사회), 쓰기의 6개 카테고리로 나눠 수록했다. 문항마다 사람의 정답률이 함께 실려 있다. | **확인 불가** | 미확인<br>수정·파생: 확인 불가<br>재배포: 확인 불가<br>카드에 라이선스가 없는 데다 수능 기출 기반이라 원저작권 확인 필요 | 내장 |
| [KoBEST](https://huggingface.co/datasets/skt/kobest_v1) | NLU 5종 | 전문가가 만든 한국어 이해 평가 5종. 지문 참/거짓 판단(boolq), 원인·결과 고르기(copa), 상황 이어가기(hellaswag), 부정문 감성 분석(sentineg), 동형어 문맥 구별(wic)로 구성된다. | **가능** | CC-BY-SA-4.0<br>수정·파생: 가능(동일조건)<br>재배포: 조건부 가능 | 내장 |
| [KoBALT-700](https://huggingface.co/datasets/snunlp/KoBALT-700) | 언어학(구문·의미) | 언어학 전문가가 구문, 의미, 화용을 묻도록 만든 한국어 객관식 700문항(snunlp). | **불가** | CC-BY-NC-4.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 없음 |
| [Belebele (kor_Hang)](https://huggingface.co/datasets/facebook/belebele) | 읽기이해 | FLORES-200 지문으로 만든 병렬 읽기이해 객관식 문항으로, 언어마다 900문항씩 있다. 같은 지문을 쓰므로 언어 간 독해력을 직접 비교할 수 있다. | **가능** | CC-BY-SA-4.0<br>수정·파생: 가능(동일조건)<br>재배포: 조건부 가능 | 내장 |
| [PAWS-X (ko)](https://huggingface.co/datasets/google-research-datasets/paws-x) | 문장 의미(패러프레이즈) | 어순이나 개체를 살짝 뒤바꾼 문장쌍이 같은 뜻인지를 판별한다. 표면 단어만 맞춰서는 풀 수 없고 문장 구조를 이해해야 한다. | **조건 확인 필요** | other(커스텀)<br>수정·파생: 조건 확인 필요<br>재배포: 조건 확인 필요<br>라이선스 'other'(커스텀). 재배포 조건 원문 확인 필요 | 내장 |
| [KorQuAD 1.0 (squad_kor_v1)](https://huggingface.co/datasets/KorQuAD/squad_kor_v1) | 독해 QA(추출형) | 위키백과 지문에서 답을 찾아내는 추출형 QA로, SQuAD와 같은 형식이다. | **가능** | CC-BY-ND-4.0(HF 카드 표기. 원 공식 사이트는 CC-BY-ND-2.0-KR)<br>수정·파생: 불가<br>재배포: 원본 그대로만 | 없음 |
| [MultiBLiMP](https://huggingface.co/datasets/jumelet/multiblimp) | 문법성 최소쌍 | 101개 언어의 문법성 최소쌍 벤치마크. 문법에 맞는 문장과 비문의 loglikelihood를 비교한다. 언어 코드 koi는 코미어라서 한국어(kor)는 들어 있지 않다. | **가능** | CC-BY-4.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>한국어 미포함. 'koi'는 코미페르먀크어(ISO 639-3) 오인 주의 | 내장(koi=코미페르먀크어) |
| [KLUE](https://huggingface.co/datasets/klue/klue) | NLU 종합(8태스크) | 한국어 이해 8개 과제를 묶은 공식 벤치마크. 주제 분류, 문장 유사도, 추론, 개체명 인식, 관계 추출, 의존 구문 분석, 기계 독해, 대화 상태 추적으로 구성되며, 번역이 아닌 한국어 원문 코퍼스로 만들었다. | **가능** | CC-BY-SA-4.0<br>수정·파생: 가능(동일조건)<br>재배포: 조건부 가능 | 없음 |
| [KMMLU-Redux](https://huggingface.co/datasets/LGAI-EXAONE/KMMLU-Redux) | 이해(지식 MCQ 재구성판) | KMMLU에서 오류 문항을 걷어내고 국가기술자격시험 중심으로 다시 구성한 개정판(LGAI-EXAONE, 2025-07). KMMLU-Pro와 함께 전문 지식 벤치마크 스위트를 이룬다(arXiv:2507.08924). | **불가** | CC-BY-NC-ND-4.0<br>수정·파생: 불가<br>재배포: 원본 그대로만<br>HF 게이트(접근 동의 필요) | 없음 |

### 추론·수학

| 벤치마크 | 평가 축 | 설명 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |
|---|---|---|---|---|---|
| [MMLU-ProX (ko)](https://huggingface.co/datasets/li-lab/MMLU-ProX) | 이해(추론 강화) | 10지선다로 추론 요구를 높인 MMLU-Pro를 다국어로 확장한 판의 한국어 서브셋. 5-shot CoT로 풀게 한 뒤 '답은 (X)입니다' 형식에서 정답을 정규식으로 추출해 채점한다. | **가능** | MIT<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 내장 |
| [HRM8K](https://huggingface.co/datasets/HAERAE-HUB/HRM8K) | 수학 추론 | GSM8K, KSM, MATH, MMMLU, Omni-MATH 다섯 서브셋을 한·영 병렬로 묶은 약 8,000문항. 수치 정답을 그대로 대조해 채점하므로 LLM judge가 필요 없다(judge-free). | **가능** | MIT<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 내장 |
| [AIME2025-ko](https://huggingface.co/datasets/allganize/AIME2025-ko) | 수학(고난도 경시) | 미국 수학 경시 AIME 2025 I·II 30문항을 한국어로 번역한 데이터셋(Allganize). 영어 원문과 풀이가 나란히 실려 있고, 수치 정답을 대조해 채점한다. | **확인 불가** | 미확정<br>수정·파생: 확인 불가<br>재배포: 확인 불가<br>상속 원본(yentinglin/aime_2025)에 라이선스 필드 부재. 재배포 근거 불분명 | 없음 |
| [ko_hellaswag](https://huggingface.co/datasets/davidkim205/ko_hellaswag) | 상식 추론 | HellaSwag의 한국어 번역판. 상황 서술에 자연스럽게 이어질 문장을 4지선다로 고른다. | **확인 불가** | 미기재<br>수정·파생: 확인 불가<br>재배포: 확인 불가<br>번역본 라이선스 미기재(원본 HellaSwag=MIT) | 없음 |
| [ARC-AGI](https://github.com/fchollet/ARC-AGI) | 추상추론 | 격자 입출력 쌍 몇 개에서 변환 규칙을 알아내 새 입력에 적용하는 추상 추론 벤치마크(Chollet). | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 없음 |
| [LogicKor](https://github.com/instructkr/LogicKor) | 사고력(멀티턴 생성) | 한국어 다분야 사고력 벤치마크로, 멀티턴 질문을 LLM judge가 채점한다. 커뮤니티 표준으로 널리 쓰였지만 지금은 리더보드 운영이 멈췄고 저장소도 읽기 전용이다. | **가능** | CC-BY-SA-4.0(HF 미러 표기)<br>수정·파생: 가능(동일조건)<br>재배포: 조건부 가능<br>원 저장소(instructkr) 라이선스 확인 권장. 리더보드 운영 중단 상태 | 없음 |
| [HRMCR](https://huggingface.co/datasets/HAERAE-HUB/HRMCR) | 추론(다단계 한국 문화) | 음력, 공휴일, 나이 계산처럼 한국 문화 지식이 있어야 풀리는 다단계 추론 벤치마크(HAERAE-HUB, 2025-01). 단계별 풀이가 함께 제공돼 풀이 과정까지 채점할 수 있다. | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 없음 |
| [Ko-PIQA](https://huggingface.co/datasets/HAERAE-HUB/Ko-PIQA) | 상식(물리 추론) | 물리적 상식 추론 벤치마크 PIQA의 한국어판(HAERAE-HUB, 2026-01 공개). 상황에 맞는 해결책을 둘 중에서 고른다. | **확인 불가** | 미표기<br>수정·파생: 확인 불가<br>재배포: 확인 불가<br>카드에 라이선스 미표기. 이용 전 저자 확인 필요 | 없음 |
| [KorNLI·KorSTS](https://huggingface.co/datasets/kakaobrain/kor_nli) | NLU(추론·유사도) | 카카오브레인이 만든 한국어 추론(NLI)과 문장 유사도(STS) 벤치마크. 함의/중립/모순 3분류와 유사도 채점으로 구성되며, 번역 후 전문 검수를 거쳐 구축했다. | **가능** | CC-BY-SA-4.0<br>수정·파생: 가능(동일조건)<br>재배포: 조건부 가능 | 없음 |
| [Ko-CommonGen v2](https://huggingface.co/datasets/nlpai-lab/ko_commongen_v2) | 생성 상식(제약 문장) | 주어진 개념들로 만든 문장 가운데 상식에 맞고 자연스러운 것을 고르는 평가(고려대 nlpai-lab). Open Ko-LLM Leaderboard의 Ko-H5 구성 셋 중 유일하게 공개된 부분이다. | **확인 불가** | 미표기<br>수정·파생: 확인 불가<br>재배포: 확인 불가<br>카드에 라이선스 미표기. 이용 전 저자 확인 필요 | 없음 |

### 전문 도메인

| 벤치마크 | 평가 축 | 설명 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |
|---|---|---|---|---|---|
| [KorMedMCQA](https://huggingface.co/datasets/sean0042/KorMedMCQA) | 도메인(의료 면허) | 의사, 간호사, 약사, 치과의사 국가시험 기출로 만든 객관식 QA. 의료법과 제도를 묻는 문항도 들어 있다. | **불가** | CC-BY-NC-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 내장 |
| [KorMedMCQA-V](https://huggingface.co/datasets/seongsubae/KorMedMCQA-V) | 도메인(의료 멀티모달) | 한국 의사시험의 멀티모달판. 문항 1,534개에 검사 사진 같은 이미지 2,043개가 딸려 있다. | **불가** | CC-BY-NC-SA-4.0<br>수정·파생: 가능(동일조건)<br>재배포: 조건부 가능 | 없음 |
| [KorMedLawQA](https://huggingface.co/datasets/snuh/KorMedLawQA) | 도메인(의료법) | 한국 의료 관련 법령을 소재로 한 객관식 문항에 조문 근거 추론이 딸린 데이터셋(SNUH HARI). 확인한 문항 상당수는 영어로 서술돼 있다. | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>문항 상당수가 영어 서술(한국 법령 소재) | 없음 |
| [korean-legal-qa](https://huggingface.co/datasets/ggh5454/korean-legal-qa-dataset) | 도메인(법률 QA) | 법령 조문과 판례를 연계한 한국어 법률 QA. 조문 번호, 판례 사건번호, 요지 필드가 함께 제공된다. | **가능** | CC-BY-4.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>출처 표기(BY) 필요 | 없음 |
| [KR-Legal-QA](https://huggingface.co/datasets/LDKSolutions/KR-legal-qa-1.8k-jsonl) | 도메인(법률 상담 QA) | 생활법률 상담 형식의 QA 약 1,800건. 제목과 질문, 조문을 근거로 든 답변으로 구성된다. | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 없음 |
| [KCL(LBox)](https://huggingface.co/datasets/lbox/kcl) | 도메인(법률 추론) | 변호사시험 기출로 만든 법률 추론 벤치마크(LBox). 서술형인 kcl_essay에는 채점 루브릭과 근거 판례가 함께 실려 있다. | **불가** | CC-BY-NC-4.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 없음 |

### 지시이행

| 벤치마크 | 평가 축 | 설명 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |
|---|---|---|---|---|---|
| [IFEval-Ko](https://huggingface.co/datasets/allganize/IFEval-Ko) | 지시이행(제어성) | 구글 IFEval의 한국어판. '쉼표를 쓰지 마라', '300단어 이상으로 써라' 같은 검증 가능한 지시 342개를 주고, 지켰는지를 프로그램이 판정하므로 LLM judge가 필요 없다(judge-free). | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 없음(allganize task config 수동 배치. 0.4.12 실측 확인) |

### 생성·평가

| 벤치마크 | 평가 축 | 설명 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |
|---|---|---|---|---|---|
| [KoMT-Bench](https://huggingface.co/datasets/LGAI-EXAONE/KoMT-Bench) | 생성(멀티턴) | MT-Bench의 한국어판(LGAI). 2턴 대화로 생성 능력을 평가하며 채점에 LLM judge가 필요하다. | **조건 확인 필요** | LGPL-3.0 태그<br>수정·파생: 조건 확인 필요<br>재배포: 조건 확인 필요<br>LGPL-3.0 태그. 데이터 라이선스로서의 적합성 확인 권장 | 없음 |
| [K2-Eval](https://huggingface.co/datasets/HAERAE-HUB/K2-Eval) | 생성(한국 지식 적용) | 한국어 고유 지식을 실제로 적용해 서술형 답을 쓰게 하는 생성 평가(HAERAE-HUB). 문항마다 과목과 능력 태그가 붙어 있다. | **가능** | MIT<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 없음 |
| [KUDGE](https://huggingface.co/datasets/HAERAE-HUB/KUDGE) | 메타평가(LLM judge) | LLM judge의 채점 능력 자체를 재는 한국어 메타평가(HAERAE-HUB). 모델 응답에 사람이 매긴 점수와 judge가 매긴 점수가 얼마나 일치하는지를 본다. | **확인 불가** | 미표기<br>수정·파생: 확인 불가<br>재배포: 확인 불가<br>카드에 라이선스 미표기. 이용 전 저자 확인 필요 | 없음 |

### 에이전트·도구 사용

| 벤치마크 | 평가 축 | 설명 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |
|---|---|---|---|---|---|
| [BFCL(Gorilla)](https://huggingface.co/datasets/gorilla-llm/Berkeley-Function-Calling-Leaderboard) | 에이전트(함수 호출) | 자연어 요청을 올바른 함수 호출로 바꾸는 능력을 평가한다. 단일 호출부터 병렬 호출, 멀티턴까지 유형별 서브셋이 있다. | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>executable 서브셋은 코드 실행 환경 필요 | 없음 |

### 검색·RAG·장문

| 벤치마크 | 평가 축 | 설명 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |
|---|---|---|---|---|---|
| [AutoRAGRetrieval](https://huggingface.co/datasets/mteb/AutoRAGRetrieval) | 검색 | 금융, 공공, 의료, 법률, 커머스 도메인의 한국어 기업 PDF로 만든 BeIR 형식 검색 데이터셋. 코퍼스는 문서 720건이다. | **가능** | MIT<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 없음 |
| [MIRACL (ko)](https://huggingface.co/datasets/mteb/MIRACLRetrieval) | 검색(표준 비교) | 위키백과 기반 다국어 표준 검색 벤치마크의 한국어 서브셋. 임베딩 모델을 국제적으로 비교하는 기준점으로 쓰인다. | **가능** | CC-BY-SA-4.0<br>수정·파생: 가능(동일조건)<br>재배포: 조건부 가능 | 없음 |
| [Ko-StrategyQA](https://huggingface.co/datasets/mteb/Ko-StrategyQA) | 검색(멀티홉) | StrategyQA를 한국어로 번역해 만든 멀티홉 검색 데이터셋. 코퍼스 9,251건에 질의 592건이다. | **확인 불가** | 미표기<br>수정·파생: 확인 불가<br>재배포: 확인 불가<br>번역본 라이선스 미표기(원본 StrategyQA=MIT) | 없음 |
| [RAG-Evaluation-Dataset-KO](https://huggingface.co/datasets/allganize/RAG-Evaluation-Dataset-KO) | RAG 종합 | 도메인별로 질문과 정답, 페이지 단위 근거 문서를 묶어 RAG 파이프라인을 끝에서 끝까지 평가한다(Allganize). | **가능** | MIT<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 없음 |
| [Ko-LongRAG](https://huggingface.co/datasets/LGAI-EXAONE/Ko-LongRAG) | 검색·장문 RAG QA | 한국어 장문 컨텍스트 RAG 평가(LGAI-EXAONE, 2025-09). 위키 문단 목록을 주고 단일 문서 또는 여러 문서에 걸친 QA로 답을 찾게 한다. | **불가** | CC-BY-NC-4.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 없음 |

### 안전·사실성

| 벤치마크 | 평가 축 | 설명 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |
|---|---|---|---|---|---|
| [KoBBQ](https://huggingface.co/datasets/naver-ai/kobbq) | 편향(안전) | 편향 벤치마크 BBQ를 한국 문화에 맞게 다시 만든 데이터셋(NAVER AI Lab). 모호한 맥락과 명시적 맥락에서 사회 편향을 드러내는지 묻는 객관식 약 76,000문항이다. | **가능** | MIT<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 없음 |
| [KoSBi(-v2)](https://huggingface.co/datasets/nayohan/KoSBi-v2) | 안전·편향 | 인종, 지역, 성별 같은 사회 집단에 대한 맥락과 문장이 안전한지 유해한지를 분류한다. train 셋 기준 약 54,400건으로 표시돼 있다. | **조건 확인 필요** | MIT 표기(원 NOTICE 확인 필요)<br>수정·파생: 조건 확인 필요<br>재배포: 조건 확인 필요<br>MIT 표기이나 원 저장소 NOTICE 확인 권장 | 없음 |
| [KOLD](https://huggingface.co/datasets/nayohan/KOLD) | 유해성 | 뉴스 기사와 댓글에서 모은 혐오·공격 발화 40,429건. 공격성 여부, 공격 대상, 대상 집단을 계층적으로 라벨링했다. | **확인 불가** | 미확인<br>수정·파생: 확인 불가<br>재배포: 확인 불가<br>카드에 라이선스 미표기. 이용 조건 확인 필요 | 없음 |
| [korean-hate-speech](https://github.com/kocohub/korean-hate-speech) | 유해성 | 연예 뉴스 댓글에 혐오 표현과 사회적 편향을 이중으로 주석한 데이터셋(kocohub). | **가능** | CC-BY-SA-4.0<br>수정·파생: 가능(동일조건)<br>재배포: 조건부 가능 | 없음 |
| [K-HALU](https://github.com/J-Seo/K-HALU) | 환각 | 문서와 진술을 대조해 진술이 문서에 충실한지 판별하는 객관식 벤치마크(ICLR 2025, 고려대). 7개 도메인 2,170문항이고 복수정답 문항이 40%다. | **조건 확인 필요** | AI-Hub 약정<br>수정·파생: 약정 확인<br>재배포: 제3자 재배포 불가<br>코드·샘플은 MIT, full 데이터는 AI-Hub 신청제(승인 계정만 접근, 제3자 재배포 제한) | 없음 |
| [KoSimpleQA](https://github.com/naver-ai/KoSimpleQA) | 사실성(환각) | 짧은 사실 질문에 대한 답을 정답과 대조하는 SimpleQA의 한국어판(NAVER AI Lab). 1,000문항이며 데이터는 GitHub에 공개돼 있다. | **확인 불가** | 미선언<br>수정·파생: 확인 불가<br>재배포: 확인 불가<br>라이선스 미선언. 저자 확인 진행 중(GitHub issue #1) | 없음 |
| [HalluLens](https://github.com/facebookresearch/HalluLens) | 환각 | Meta의 환각 평가 3개 과제. 단답 사실 확인(PreciseWikiQA), 장문 일관성(LongWiki), 존재하지 않는 대상에 대한 답변 거부(NonExistentRefusal)로 구성된다. | **불가** | 데이터 CC-BY-NC-4.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>코드 저장소의 라이선스(MIT/Apache)는 데이터와 별개이므로 혼동 주의 | 없음 |
| [KoTruthfulQA(번역본)](https://github.com/sylinrl/TruthfulQA) | 환각 | TruthfulQA의 한국어 번역판. 흔한 오개념을 답하도록 유도하는 질문으로 사실성을 측정한다. | **조건 확인 필요** | 원본 Apache-2.0<br>수정·파생: 조건 확인 필요<br>재배포: 조건 확인 필요<br>한국어 번역본이 여러 갈래이고 라이선스 미확정. 원본(Apache-2.0)과 별개 판단 필요 | 없음 |

### 코딩

| 벤치마크 | 평가 축 | 설명 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |
|---|---|---|---|---|---|
| [HumanEval](https://github.com/openai/human-eval) | 코딩 | 함수 164개를 구현하게 하고 테스트 실행으로 채점한다. LLM judge가 필요 없다(judge-free). | **가능** | MIT<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>채점에 코드 실행 환경 필요 | 내장 |
| [BigCodeBench](https://github.com/bigcode-project/bigcodebench) | 코딩 | 실용 라이브러리를 호출해 푸는 코딩 문항 약 1,140개를 테스트 실행으로 채점한다. | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>채점에 코드 실행 환경 필요 | 없음 |

## 영어 벤치마크

총 31개 · 상업적 이용 가능 21개 · 불가 0개 · 확인 불가 7개 · 조건 확인 필요 3개

### 이해·언어

| 벤치마크 | 평가 축 | 설명 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |
|---|---|---|---|---|---|
| [MMLU](https://huggingface.co/datasets/cais/mmlu) | 이해(지식 MCQ) | 57과목 4지선다 지식 벤치마크(2020). 수년간 사실상의 표준이었지만 2026년 현재 프런티어 모델이 92%를 넘겨 포화됐고, 문서화된 라벨 오류 때문에 실질 상한은 약 95%다. | **가능** | MIT<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>포화 상태. 프런티어 모델 변별력 상실. 상위권 비교에는 부적합 | 내장 |
| [GPQA (Diamond)](https://huggingface.co/datasets/Idavidrein/gpqa) | 이해(대학원급 과학) | 생물, 물리, 화학의 대학원급 문항. 비전문가가 검색해 가며 풀어도 못 맞히도록 설계한 'Google-proof' 벤치마크로, 프런티어 모델 비교의 표준 축이다. | **가능** | CC-BY-4.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>HF 게이트(자동 승인). 오염 방지 목적이므로 재배포 자제 요청 | 내장(gpqa) |
| [Humanity's Last Exam](https://huggingface.co/datasets/cais/hle) | 이해(프런티어 지식) | 100개가 넘는 학문 분야의 전문가 약 1,000명이 출제한 2,500문항(CAIS·Scale AI, Nature 2026-01 게재). 포화된 지식 벤치마크를 대체하는 프런티어 표준이다. | **조건 확인 필요** | MIT 태그(README 재배포 제한 문구와 충돌. 이용 전 확인)<br>수정·파생: 조건 확인 필요<br>재배포: 조건 확인 필요<br>라이선스 태그와 README 조건 충돌. 재배포 전 법적 확인 필요 | 없음 |

### 추론·수학

| 벤치마크 | 평가 축 | 설명 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |
|---|---|---|---|---|---|
| [MMLU-Pro](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro) | 이해(추론 강화 MCQ) | MMLU를 10지선다로 넓히고 추론 요구를 높인 후속 벤치마크(TIGER-Lab). 한국어 인벤토리의 MMLU-ProX가 이것의 다국어판이다. | **가능** | MIT<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 내장(mmlu_pro) |
| [BIG-Bench Hard](https://huggingface.co/datasets/lukaemon/bbh) | 추론(다과제) | BIG-Bench에서 당시 모델이 인간에 못 미치던 23개 난제만 추린 과제 모음. CoT 프롬프팅 연구의 표준이었지만 지금은 대부분 포화됐다. | **확인 불가** | 미표기<br>수정·파생: 확인 불가<br>재배포: 확인 불가<br>카드에 라이선스 미표기(원 BIG-Bench는 Apache-2.0) | 내장(bbh) |
| [GSM8K](https://huggingface.co/datasets/openai/gsm8k) | 수학(초등 서술형) | 초등 수준의 다단계 서술형 수학 약 8,500문항(OpenAI). 포화됐지만 파이프라인 검증과 소형 모델 평가에는 여전히 쓰인다. 라벨 오류를 수정한 GSM8K-Platinum 파생판이 있으며, HRM8K의 소스 중 하나다. | **가능** | MIT<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>포화 상태. 프런티어 변별력 없음 | 내장(gsm8k·gsm8k_platinum) |
| [MATH-500](https://huggingface.co/datasets/HuggingFaceH4/MATH-500) | 수학(경시 수준) | MATH(Hendrycks) 12,500문항 중 OpenAI가 추론 평가용으로 추린 500문항 부분집합. o1 계열 이후 추론 모델 보고서에서 관행적 표준이 됐다. | **확인 불가** | 미표기(원본 MATH=MIT)<br>수정·파생: 확인 불가<br>재배포: 확인 불가<br>부분집합 자체의 카드 라이선스 미표기 | 내장(hendrycks_math·minerva_math, 500 부분집합은 별도) |
| [AIME 2025](https://huggingface.co/datasets/yentinglin/aime_2025) | 수학(경시 고난도) | 미국 수학 경시 AIME의 2025년 30문항. 매년 새 문항이 나와 학습 오염이 늦다는 이유로 추론 모델 비교의 관행적 표준이 됐다. 한국어판(AIME2025-ko)이 여기서 파생됐다. | **확인 불가** | 미표기(HF 미러에 라이선스 필드 부재)<br>수정·파생: 확인 불가<br>재배포: 확인 불가<br>재배포 근거 불분명. 원 출제기관(MAA) 저작권 확인 필요 | 없음 |
| [FrontierMath](https://epoch.ai/frontiermath) | 수학(연구 수준) | 현역 수학자들이 출제한 연구 수준의 문제(Epoch AI). 학습 오염을 막으려고 문제 자체를 비공개로 관리하며, 평가는 Epoch AI를 거쳐야만 할 수 있다. | **조건 확인 필요** | 비공개 홀드아웃<br>수정·파생: 접근 불가<br>재배포: 불가<br>데이터 접근 불가. 자체 실행 불가, 공표 점수 인용만 가능 | 없음 |
| [ARC-AGI (v1)](https://github.com/fchollet/ARC-AGI) | 추상추론 | 격자 입출력 쌍 몇 개에서 변환 규칙을 알아내는 추상 추론 벤치마크(Chollet, 2019). 2024년 말 추론 모드를 갖춘 프런티어 모델이 인간 기준선을 넘어서면서 사실상 돌파됐다. | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>v1은 돌파된 상태. 현재 변별력은 v2/v3로 이동 | 없음(arc는 별개 AI2-ARC) |
| [ARC-AGI-2](https://github.com/arcprize/ARC-AGI-2) | 추상추론(프런티어) | v1을 깬 기법이 통하지 않도록 다시 설계한 후속판(ARC Prize, 2025). 2026년 4월 기준으로 최고 모델도 인간과 상당한 격차가 남아 있는 현역 변별 벤치마크다. | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 없음 |
| [ARC-AGI-3](https://arcprize.org/) | 에이전트(인터랙티브 추론) | 2026년 3월 공개된 인터랙티브 게임형 벤치마크. 명시적 지시 없이 환경을 탐색하고 목표를 추론해 행동을 계획해야 한다. 기술 보고서 기준으로 인간은 100%를 풀지만 프런티어 모델은 1%에 못 미친다. | **확인 불가** | 공식 사이트 확인 필요(공개 저장소 미확인)<br>수정·파생: 확인 불가<br>재배포: 확인 불가<br>정적 데이터셋이 아닌 대화형 환경. 하니스 통합 방식이 기존과 다름 | 없음 |

### 지시이행

| 벤치마크 | 평가 축 | 설명 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |
|---|---|---|---|---|---|
| [IFEval](https://huggingface.co/datasets/google/IFEval) | 지시이행(제어성) | '쉼표를 쓰지 마라', '단어 수를 지켜라' 같은 검증 가능한 지시를 지켰는지 프로그램이 판정하는 벤치마크(Google). LLM judge가 필요 없으며(judge-free), IFEval-Ko의 원본이다. | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 내장(ifeval) |

### 코딩

| 벤치마크 | 평가 축 | 설명 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |
|---|---|---|---|---|---|
| [HumanEval](https://github.com/openai/human-eval) | 코딩(함수 구현) | 함수 164개를 구현하게 하고 테스트 실행으로 채점한다(OpenAI, 2021). 포화됐지만 코드 평가 파이프라인의 스모크 테스트 기준으로는 남아 있다. | **가능** | MIT<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>포화 상태. 채점에 코드 실행 환경 필요 | 내장(humaneval) |
| [MBPP](https://huggingface.co/datasets/google-research-datasets/mbpp) | 코딩(기초 문제) | 테스트가 딸린 기초 파이썬 974문항(Google). sanitized 서브셋이 표준으로 쓰인다. HumanEval과 함께 포화된 1세대 코드 벤치마크다. | **가능** | CC-BY-4.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>채점에 코드 실행 환경 필요 | 내장(mbpp) |
| [BigCodeBench](https://github.com/bigcode-project/bigcodebench) | 코딩(실용 라이브러리) | 실용 라이브러리를 호출해 푸는 코딩 문항 약 1,140개를 테스트 실행으로 채점한다. HumanEval이 포화된 뒤의 함수 수준 표준이다. | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>채점에 코드 실행 환경 필요 | 없음 |
| [LiveCodeBench](https://huggingface.co/datasets/livecodebench/code_generation_lite) | 코딩(오염 방지 롤링) | LeetCode, AtCoder 등에 새로 출제된 문제를 시기별로 모아 학습 오염을 통제한다. 모델 출시일 이후에 나온 문제만으로 평가할 수 있다는 점이 특징이다. | **조건 확인 필요** | 카드 'cc' 표기(모호. 확인 필요)<br>수정·파생: 조건 확인 필요<br>재배포: 조건 확인 필요<br>라이선스 표기가 'cc'로 불완전. 이용 전 확인. 원 문제 저작권은 출제 플랫폼에 귀속 | 없음 |
| [SWE-bench Verified](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified) | 코딩(에이전틱) | 실제 GitHub 이슈를 저장소 통째로 받아 해결하는 에이전틱 코딩 벤치마크. 사람이 검증한 500문항 부분집합으로, 2025~2026년 에이전트 코딩 비교의 사실상 표준이다. | **확인 불가** | 미표기(수집물. 원 저장소 라이선스 상속)<br>수정·파생: 확인 불가<br>재배포: 확인 불가<br>GitHub 수집물이라 데이터 재배포 조건 불분명. 실행에 컨테이너 환경 필요 | 없음 |

### 에이전트·도구 사용

| 벤치마크 | 평가 축 | 설명 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |
|---|---|---|---|---|---|
| [Terminal-Bench](https://github.com/laude-institute/terminal-bench) | 에이전트(터미널) | 빌드 고치기, 환경 구성하기 같은 복합 작업을 터미널 안에서 해내는지 평가한다(Laude Institute). 2025년 등장한 에이전트 실무 능력 축이다. | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>실행에 컨테이너 환경 필요 | 없음 |
| [BFCL](https://github.com/ShishirPatil/gorilla) | 에이전트(함수 호출) | 자연어 요청을 함수 호출로 얼마나 정확히 바꾸는지 평가한다(UC Berkeley Gorilla). 단일 호출에서 병렬 호출, 멀티턴으로 v3~v4에 걸쳐 확장돼 왔으며 도구 호출 축의 표준이다. | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>executable 서브셋은 코드 실행 환경 필요 | 없음 |
| [τ²-bench](https://github.com/sierra-research/tau2-bench) | 에이전트(대화형 도구) | 고객 응대 시나리오에서 도구와 정책, 사용자를 상대로 한 멀티턴 상호작용을 평가한다(Sierra). 항공, 리테일, 텔레콤 도메인으로 구성되며 대화가 끝난 뒤의 최종 상태로 채점한다. | **가능** | MIT<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>시뮬레이터·사용자 모델 실행 환경 필요 | 없음 |
| [GAIA](https://huggingface.co/datasets/gaia-benchmark/GAIA) | 에이전트(일반 비서) | 웹 검색과 파일 처리, 멀티모달 이해를 조합해야 풀리는 일반 비서 과제(Meta 등). 사람에게는 쉽고 모델에게는 어렵도록 설계됐다. | **확인 불가** | 미표기 + HF 게이트<br>수정·파생: 확인 불가<br>재배포: 확인 불가<br>게이트 접근 동의 필요 | 없음 |
| [OSWorld](https://github.com/xlang-ai/OSWorld) | 에이전트(컴퓨터 사용) | Ubuntu, Windows 같은 실제 OS의 GUI에서 실무 과제를 수행하게 하는 평가(NeurIPS 2024). 컴퓨터 사용(computer-use) 축의 표준이다. | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>VM 실행 환경 필요 | 없음 |

### 안전·사실성

| 벤치마크 | 평가 축 | 설명 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |
|---|---|---|---|---|---|
| [SimpleQA](https://huggingface.co/datasets/basicv8vc/SimpleQA) | 사실성(단답) | 짧은 사실 질문에 대한 답을 정답과 대조한다(OpenAI simple-evals). 환각을 가볍게 재는 표준이며 KoSimpleQA의 원형이다. | **가능** | MIT<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 없음 |
| [TruthfulQA](https://huggingface.co/datasets/truthfulqa/truthful_qa) | 사실성(오개념) | 흔한 오개념을 답하도록 유도하는 817문항. MC1/MC2 방식의 logprob으로 채점한다. 한국어 번역본은 라이선스가 확정되지 않았다(한국어 인벤토리 참조). | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능 | 내장(truthfulqa) |
| [BBQ](https://huggingface.co/datasets/heegyu/bbq) | 편향(안전) | 모호한 맥락과 명시적 맥락에서 사회 편향을 드러내는지 묻는 객관식 벤치마크(NYU). 연령, 성별 등 카테고리별로 편향을 재며 KoBBQ의 원형이다. | **가능** | CC-BY-4.0(미러 카드)<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>원본(nyu-mll) 카드와 대조 확인 권장 | 내장(bbq) |

### 검색·RAG·장문

| 벤치마크 | 평가 축 | 설명 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |
|---|---|---|---|---|---|
| [LongBench v2](https://huggingface.co/datasets/zai-org/LongBench-v2) | 장문 이해 | 8,000단어에서 200만 단어에 이르는 장문을 읽고 여러 과제를 푸는 이해 평가(Tsinghua/Zhipu). 장문 컨텍스트 축의 현행 표준 중 하나다. | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>구경로(THUDM)는 404. zai-org 경로 사용 | 내장(longbench2) |

### 생성·평가

| 벤치마크 | 평가 축 | 설명 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |
|---|---|---|---|---|---|
| [MT-Bench](https://github.com/lm-sys/FastChat/tree/main/fastchat/llm_judge) | 생성(멀티턴 judge) | 2턴 대화로 생성 능력을 평가하는 80문항(LMSYS). LLM-as-judge 방법론을 대중화했다. KoMT-Bench의 원형이며 지금은 Arena-Hard 계열로 세대교체가 진행 중이다. | **가능** | Apache-2.0(FastChat 저장소)<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>judge 모델 필요 | 없음 |
| [Arena-Hard-Auto](https://github.com/lmarena/arena-hard-auto) | 생성(자동 판정) | Chatbot Arena(LMArena)의 실사용 질의에서 추린 고난도 프롬프트에 대한 응답을 LLM judge가 자동 판정한다. 사람 선호와 상관이 높다는 점을 내세우는 현행 생성 비교 표준이다. | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>judge 모델 필요. 데이터 조회는 GitHub 경로가 안정적 | 없음 |

### 기타

| 벤치마크 | 평가 축 | 설명 | 상업적 이용 | 라이선스·이용 조건 | lm-eval |
|---|---|---|---|---|---|
| [LiveBench](https://huggingface.co/datasets/livebench/coding) | 종합(오염 방지 월간 갱신) | 매월 새 문항을 추가해 학습 오염을 통제하는 벤치마크. 수학, 코딩, 추론, 언어의 여러 축을 다루며 객관적인 정답을 기준으로 자동 채점한다. | **확인 불가** | 미표기<br>수정·파생: 확인 불가<br>재배포: 확인 불가<br>문항별 원 출처 저작권 상이. 재배포 전 확인 | 없음 |
| [MTEB](https://github.com/embeddings-benchmark/mteb) | 임베딩 종합 스위트 | 검색, 분류, 클러스터링 등 임베딩 과제 전반을 아우르는 표준 스위트. 이 인벤토리의 AutoRAGRetrieval, MIRACL, Ko-StrategyQA가 이 생태계의 한국어 구성원이다. | **가능** | Apache-2.0<br>수정·파생: 가능(조건 준수)<br>재배포: 조건부 가능<br>스위트 자체는 프레임워크. 개별 데이터셋 라이선스는 각각 확인 | 없음 |

## 데이터 열

| 열 | 설명 |
|---|---|
| `대표 예시·설명` | 실제 또는 대표적인 과제 예시, 번역·요약 설명 |
| `예시 표기` | 한국어 예시·요약, 한국어 번역·요약, 영문 예시(한국어 주석) 구분 |
| `라이선스` | 데이터 카드 또는 원 출처에 표시된 라이선스와 조사 메모 |
| `상업적 이용` | 선언된 라이선스를 기준으로 한 상업적 이용 판단 |
| `수정·파생` | 번역, 변형 및 파생 데이터 제작 가능 여부 |
| `재배포` | 원본 또는 변형본 재배포 가능 여부 |
| `이용 시 유의사항` | 게이트 접근, 원저작권, 실행 환경 및 평가상 주의점 |

## 기여 시 확인 사항

1. 데이터 카드와 공식 저장소의 라이선스를 우선 확인합니다.
2. 데이터 라이선스와 코드·평가 하니스 라이선스를 구분합니다.
3. 번역본·미러·수집물은 원본 라이선스가 자동 승계된다고 가정하지 않습니다.
4. 라이선스를 재확인했으면 문서 상단의 확인 기준일을 갱신합니다.
