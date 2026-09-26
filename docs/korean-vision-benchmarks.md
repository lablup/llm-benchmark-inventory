# 한국어 이미지 벤치마크 조사

확인일: 2026-09-26

이 문서는 이미지와 한국어 문장을 함께 입력하는 공개 평가 자료를 정리합니다. 학습 데이터만 공개했거나 이미지 없이 한국어 문장만 평가하는 자료는 제외했습니다. 벤치마크로 사용할 수 있는지 판단하기 위해 데이터 공개 여부, 평가 방법, 라이선스와 실행 코드를 함께 확인했습니다.

## 분류 기준

- **일반**은 장면, 문서, 도표와 한국 문화에 관한 이미지 이해를 평가합니다.
- **위험 탐지**는 유해 이미지를 판단하고 안전하게 답하는지, 편향되거나 필요 이상으로 거부하지 않는지 평가합니다.
- **의료**는 의료 영상을 해석하고 여러 영상을 함께 살펴 한국어 임상 문항에 답하는 능력을 평가합니다.

## 인벤토리에 바로 추가한 자료

### 일반

- **KMMMU**는 한국 공무원 시험, 국가기술자격시험, 국가직무능력표준(NCS) 시험과 학술 올림피아드에서 문항을 수집했습니다. 문항 3,466개와 이미지 3,628개를 제공하며, 이미지 안에 글자가 있는 문항이 2,550개입니다. 한국의 시험 자료를 직접 사용했다는 점에서 번역 벤치마크와 구분됩니다. 데이터는 CC BY-NC 4.0이므로 상업적으로 사용할 수 없습니다. [데이터 카드](https://huggingface.co/datasets/HAERAE-HUB/KMMMU)와 [평가 코드](https://github.com/HAE-RAE/KMMMU)를 제공합니다.
- **HAERAE-VISION**은 한국 온라인 커뮤니티에 올라온 실제 질문을 바탕으로 만듭니다. 같은 이미지에 맥락이 빠진 원래 질문(original)과 대상을 명확히 쓴 질문(explicit)을 함께 제공하므로, 질문의 불명확성(under-specification)이 성능에 미치는 영향을 비교할 수 있습니다. 653개 이미지 질의를 제공하며 데이터는 CC BY 4.0입니다. 공식 채점에는 판정 모델(judge model)이 필요합니다. [데이터 카드](https://huggingface.co/datasets/HAERAE-HUB/HAERAE-VISION)와 [평가 코드](https://github.com/HAE-RAE/HAERAE-VISION)를 제공합니다.
- **KOFFVQA**는 275개 한국어 자유형 시각 질의응답(VQA) 문항을 제공합니다. 각 문항에 세부 채점 기준을 두어 자유형 답변을 부분 점수로 평가합니다. 데이터 카드는 Apache 2.0을 표시하고 있으며 공식 평가 코드는 로컬 모델과 API 모델을 모두 지원합니다. 채점 단계에는 판정 모델이 필요합니다. [데이터 카드](https://huggingface.co/datasets/maum-ai/KOFFVQA_Data), [평가 코드](https://github.com/maum-ai/KOFFVQA), [논문](https://openaccess.thecvf.com/content/CVPR2025W/BEAM/html/Kim_KOFFVQA_An_Objectively_Evaluated_Free-form_VQA_Benchmark_for_Large_Vision-Language_CVPRW_2025_paper.html)을 제공합니다.
- **KRETA**는 한국의 실제 환경에서 촬영한 글자가 많은 이미지로 문자 읽기와 추론을 평가합니다. 2,577개 문항을 15개 분야와 26개 이미지 유형으로 나누고, 직접 읽으면 답할 수 있는 문항(System 1)과 여러 단계의 추론이 필요한 문항(System 2)을 구분합니다. 다만 데이터 카드와 저장소에서 데이터 라이선스를 찾지 못했으므로 이용 전 저자 확인이 필요합니다. [데이터 카드](https://huggingface.co/datasets/tabtoyou/KRETA), [평가 코드](https://github.com/tabtoyou/KRETA), [EMNLP 2025 논문](https://aclanthology.org/2025.emnlp-main.1696/)을 제공합니다.
- **K-DTCBench**는 한국어 문서, 표와 차트를 읽는 240개 객관식 문항으로 구성됩니다. 한국어 문서를 직접 만들었다는 점에서 번역 중심 벤치마크와 구분됩니다. 데이터는 CC BY-NC 4.0이므로 상업적으로 사용할 수 없습니다. [데이터 카드](https://huggingface.co/datasets/NCSOFT/K-DTCBench)와 [기술 설명](https://ncsoft.github.io/ncresearch/95ad8712e60063e9ac97538504ac3eea0ac530af)을 제공합니다.
- **K-MMBench**는 영어 MMBench를 한국어로 번역하고 확장한 4,329개 객관식 문항입니다. 장면, 사물의 속성·위치·관계와 추론을 넓게 확인하는 기준점으로 사용하되, 한국 문화 이해를 직접 평가하는 자료로 해석해서는 안 됩니다. 데이터는 CC BY-NC 4.0입니다. [데이터 카드](https://huggingface.co/datasets/NCSOFT/K-MMBench)와 [기술 설명](https://ncsoft.github.io/ncresearch/95ad8712e60063e9ac97538504ac3eea0ac530af)을 제공합니다.

### 위험 탐지

- **KSAFE-MM**은 한국어와 한국 문화 맥락에서 멀티모달 모델의 안전성을 평가합니다. 일반 위험을 다루는 KSAFE-MM-G 1,650건과 한국 문화에 맞춘 합성 이미지 기반 KSAFE-MM-C 12,485건을 제공합니다. 유해 요청을 따르는 비율뿐 아니라 안전한 요청을 필요 이상으로 거부하는 현상(over-refusal)도 함께 봅니다. 혐오·폭력·성적 내용·자해·개인정보·불법 행위 등 민감한 자료가 포함되므로 접근 통제가 필요합니다. 데이터는 CC BY-NC 4.0입니다. [데이터 카드](https://huggingface.co/datasets/K-intelligence/KSAFE-MM)와 [논문](https://arxiv.org/abs/2605.28013)을 제공합니다.

### 의료

- **KorMedMCQA-V**는 한국 의사시험의 문항 1,534개와 이미지 2,043개를 제공합니다. X선, 컴퓨터단층촬영(CT), 심전도(ECG), 초음파와 내시경을 포함하며, 약 30%의 문항은 여러 이미지를 함께 봐야 합니다. 데이터는 CC BY-NC-SA 4.0이므로 상업적으로 사용할 수 없습니다. [데이터 카드](https://huggingface.co/datasets/seongsubae/KorMedMCQA-V), [평가 코드](https://github.com/baeseongsu/kormedmcqa-v), [리더보드](https://kormedmcqa-v.github.io/)를 제공합니다.
- 이번 조사에서는 공개 데이터, 한국어 임상 문항과 재현 가능한 평가 절차를 모두 갖춘 별도의 한국어 의료 이미지 벤치마크를 추가로 찾지 못했습니다. KoMedQA와 KorMedMCQA는 의료 문항을 제공하지만 이미지 입력을 사용하지 않으므로 텍스트 평가에 남겨둡니다.

## 추가 확인 뒤 등재할 자료

- **VLM-CCA**는 한국 문화 관련 이미지 1,634개와 한국어·영어 질문 9,804개를 제공합니다. 문화 지식, 시간 추론, 편향 탐지와 관점 분석을 함께 다룹니다. 그러나 데이터 카드가 사람 검수와 이미지별 라이선스 정보 추가를 향후 작업으로 명시하고 있습니다. 현재는 CC BY-NC 4.0으로 표시되고 접근 동의도 필요하므로, 검수가 끝났는지 다시 확인한 뒤 등재합니다. [데이터 카드](https://huggingface.co/datasets/SOGANG-ISDS/VLM_CCA)를 확인했습니다.
- **K-SEED**, **K-MMStar**와 **K-LLaVA-W**는 모두 공개되어 있지만 K-MMBench와 평가 범위가 많이 겹치거나 문항 수가 60개로 작습니다. 첫 실행 묶음에는 넣지 않고, NCSOFT 계열 결과를 재현할 때 함께 추가하는 후보로 남깁니다. 각 데이터는 CC BY-NC 4.0입니다. [K-SEED](https://huggingface.co/datasets/NCSOFT/K-SEED), [K-MMStar](https://huggingface.co/datasets/NCSOFT/K-MMStar), [K-LLaVA-W](https://huggingface.co/datasets/NCSOFT/K-LLaVA-W)를 확인했습니다.
- **KoreaGEO Bench**는 한국 거리 이미지에서 위치 노출과 지역 편향을 평가한다는 점에서 위험 탐지 후보입니다. 다만 이번 조사에서는 논문 외에 안정적인 공개 데이터 저장소와 명확한 데이터 라이선스를 확인하지 못했습니다. [논문](https://arxiv.org/abs/2506.03371)을 확인했습니다.

## Benchpress에서 먼저 실행할 묶음

1. KMMMU로 한국 시험 기반의 이미지·도표 추론을 측정합니다.
2. HAERAE-VISION으로 실제 사용자의 불명확한 질문에 대응하는 능력을 측정합니다.
3. K-DTCBench로 한국어 문서, 표와 차트 읽기를 측정합니다.
4. KSAFE-MM으로 유해 요청 대응과 필요 이상의 거부를 분리해 측정합니다.
5. KorMedMCQA-V로 의료 영상과 여러 이미지에 걸친 임상 추론을 측정합니다.
6. 자유형 생성까지 비교할 때 KOFFVQA를 추가하고, 판정 모델과 판정 프롬프트를 결과에 기록합니다.

KRETA는 데이터 라이선스를 확인한 뒤 실행 묶음에 넣습니다. 비상업 조건이 있는 데이터는 내부 연구 평가와 고객에게 전달하는 평가 패키지를 구분해야 합니다.
