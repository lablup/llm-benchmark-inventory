window.ENGLISH_INVENTORY_COPY = {
  mmlu: {
    axis: "Knowledge (multiple choice)",
    definition: "MMLU contains four-choice questions from 57 academic and professional subjects. Scores above 92% show that it is saturated for leading models, and known labeling errors limit the useful ceiling.",
    task: "abstract_algebra",
    example: "Determine the degree of a field extension. The correct answer is 4.",
  },
  "mmlu-pro": {
    axis: "Knowledge and reasoning (multiple choice)",
    definition: "MMLU-Pro extends MMLU with ten answer choices and questions that require more reasoning. MMLU-ProX provides multilingual variants.",
    task: "validation",
    example: "Identify the characteristic of the ring 2Z and provide the reasoning that leads to the answer.",
  },
  gpqa: {
    axis: "Graduate-level science",
    definition: "GPQA contains difficult questions written by experts in biology, physics, and chemistry. The questions are designed to resist simple web searches.",
    task: "gpqa_diamond",
    example: "Calculate the lifetime of a state when two energy levels differ by 10⁻⁴ eV.",
  },
  hle: {
    axis: "Frontier knowledge and reasoning",
    definition: "Humanity's Last Exam contains about 2,500 expert-written questions from more than 100 subjects. It includes text and multimodal questions intended to distinguish current frontier models.",
    task: "multimodal question",
    example: "Analyze a chess position shown in an image and identify the forced checkmate sequence.",
  },
  bbh: {
    axis: "Reasoning across multiple tasks",
    definition: "BIG-Bench Hard contains 23 challenging tasks selected from BIG-Bench. Many current models now score highly, but it remains useful for checking reasoning pipelines.",
    task: "date_understanding",
    example: "Infer the calendar date referred to by a statement about Christmas Eve.",
  },
  gsm8k: {
    axis: "Grade-school mathematics",
    definition: "GSM8K contains about 8,500 grade-school word problems that require several calculation steps. It is saturated for leading models but remains useful for smaller models and evaluation pipeline checks.",
    task: "test",
    example: "Janet's ducks lay eggs that she sells after keeping some for breakfast. Calculate that she earns 18 dollars per day.",
  },
  "math-500": {
    axis: "Competition mathematics",
    definition: "MATH-500 is a 500-question subset of the MATH dataset. It covers algebra, geometry, number theory, and other competition-level topics.",
    task: "test",
    example: "Convert a point between Cartesian and polar coordinates and select the equivalent expression.",
  },
  aime2025: {
    axis: "Advanced competition mathematics",
    definition: "AIME 2025 contains 30 questions from the 2025 American Invitational Mathematics Examination. Its release date makes it useful for time-bounded contamination checks.",
    task: "AIME 2025 I",
    example: "Find the sum of all integer bases b greater than 9 for which 17 in base b divides 97 in base b. The answer is 70.",
  },
  frontiermath: {
    axis: "Research-level mathematics",
    definition: "FrontierMath contains research-level problems written by active mathematicians. Epoch AI keeps the main question set private to reduce training contamination, so independent local evaluation is not available.",
    task: "public sample problem 1",
    example: "Verify a number-theory statement based on the order used in Artin's primitive root conjecture. Only a small public sample is available.",
  },
  "arc-agi": {
    axis: "Abstract reasoning",
    definition: "ARC-AGI v1 tests whether a system can infer transformations from a few input and output grids. Frontier reasoning models surpassed its human baseline in late 2024, so most current comparisons use newer versions.",
    task: "training",
    example: "Infer the transformation rule from grid examples and apply it to a new grid.",
  },
  "arc-agi-2": {
    axis: "Frontier abstract reasoning",
    definition: "ARC-AGI-2 was redesigned so that methods that solved the first version would not transfer directly. It remains a current benchmark with a substantial gap between leading models and people.",
    task: "training",
    example: "Infer a difficult visual transformation from several grid pairs and produce the missing output grid.",
  },
  "arc-agi-3": {
    axis: "Interactive agent reasoning",
    definition: "ARC-AGI-3 is an interactive game benchmark released in March 2026. A system must explore an environment, infer its objective without explicit instructions, and plan actions.",
    task: "interactive environment",
    example: "There is no static question set. Evaluation measures whether an agent can explore a game, infer its objective, and complete it.",
  },
  ifeval: {
    axis: "Instruction following",
    definition: "IFEval checks compliance with instructions that a program can verify, such as word counts, forbidden punctuation, and required sections. It does not require an LLM judge.",
    task: "train",
    example: "Write a summary of at least 300 words, use three labeled sections, and do not use commas.",
  },
  humaneval: {
    axis: "Function-level coding",
    definition: "HumanEval contains 164 programming tasks that are scored by running tests. It is saturated for leading models but remains useful as a basic check of a code evaluation pipeline.",
    task: "HumanEval/0",
    example: "Implement has_close_elements, which returns whether a list contains two numbers closer than a specified threshold.",
  },
  mbpp: {
    axis: "Basic Python programming",
    definition: "MBPP contains 974 short Python programming tasks with tests. The sanitized subset is commonly used, and the benchmark is now saturated for leading models.",
    task: "sanitized",
    example: "Write a function that removes the first and last occurrence of a specified character from a string.",
  },
  bigcodebench: {
    axis: "Practical library use in code",
    definition: "BigCodeBench contains about 1,140 function-level tasks that require practical use of software libraries. Solutions are scored by running unit tests.",
    task: "BigCodeBench/0",
    example: "Use itertools to calculate the average sum of absolute differences between adjacent values across permutations.",
  },
  livecodebench: {
    axis: "Contamination-resistant coding",
    definition: "LiveCodeBench collects newly published problems from sites such as LeetCode and AtCoder. Evaluators can select questions released after a model's training cutoff.",
    task: "code_generation_lite",
    example: "Solve A. Short Sort by deciding whether one swap can turn a three-character string into abc.",
  },
  "swe-bench-verified": {
    axis: "Software engineering agents",
    definition: "SWE-bench Verified contains 500 human-validated GitHub issues. An agent edits a real repository, and the submitted patch is scored by running tests.",
    task: "test",
    example: "Read an issue about astropy's separability_matrix behavior, modify the repository, and pass the relevant tests.",
  },
  "terminal-bench": {
    axis: "Terminal agents",
    definition: "Terminal-Bench evaluates whether an agent can complete multi-step work in a terminal, including fixing builds and configuring environments. Each task runs in a controlled container.",
    task: "tasks",
    example: "Complete a specified engineering task in a container and satisfy the final state checks.",
  },
  bfcl: {
    axis: "Function calling",
    definition: "The Berkeley Function Calling Leaderboard measures how accurately a model converts natural-language requests into function calls. Current versions include parallel calls and multi-turn interactions.",
    task: "BFCL v3",
    example: "Convert a request to find the area of a triangle with base 10 and height 5 into the appropriate function call.",
  },
  "tau2-bench": {
    axis: "Conversational tool use",
    definition: "τ²-bench evaluates multi-turn customer-service interactions involving tools, policies, and simulated users. It covers airline, retail, and telecommunications tasks and scores the final system state.",
    task: "telecom and other domains",
    example: "Resolve a reservation-change request under policy constraints and verify the final database state.",
  },
  gaia: {
    axis: "General assistant agents",
    definition: "GAIA contains assistant tasks that combine web research, file handling, and multimodal understanding. The questions are designed to be straightforward for people but difficult for automated systems.",
    task: "2023 validation, level 2",
    example: "Research a June 2022 arXiv paper about AI regulation and identify the word at one end of an axis in a figure. The answer is egalitarian.",
  },
  osworld: {
    axis: "Computer-use agents",
    definition: "OSWorld evaluates whether an agent can complete practical tasks through the graphical interface of operating systems such as Ubuntu and Windows. It requires virtual machines and application state checks.",
    task: "desktop tasks",
    example: "Operate desktop applications to complete a specified task, then verify the resulting application state.",
  },
  simpleqa: {
    axis: "Short-answer factuality",
    definition: "SimpleQA compares short answers to factual questions against reference answers. It provides a lightweight measure of factual accuracy and hallucination.",
    task: "test",
    example: "Who received the IEEE Frank Rosenblatt Award in 2010? The reference answer is Michio Sugeno.",
  },
  "truthful-qa": {
    axis: "Factuality under misconceptions",
    definition: "TruthfulQA contains 817 questions that can elicit common misconceptions. Its multiple-choice variants use answer probabilities to calculate MC1 and MC2 scores.",
    task: "multiple_choice",
    example: "For the smallest country larger than one square mile, select Nauru instead of the common but incorrect answer Vatican City.",
  },
  bbq: {
    axis: "Social bias",
    definition: "BBQ measures social bias in ambiguous and explicit contexts. It covers categories such as age and gender and checks whether a model relies on stereotypes when the answer is not determined.",
    task: "Age",
    example: "In an ambiguous context, answer Can't be determined instead of choosing a grandfather based on a technology stereotype.",
  },
  "longbench-v2": {
    axis: "Long-context understanding",
    definition: "LongBench v2 evaluates understanding across documents ranging from 8,000 words to two million words. It includes tasks such as long in-context learning and question answering.",
    task: "Long In-context Learning",
    example: "Use a long input containing demonstrations to translate text in a newly introduced language.",
  },
  "mt-bench": {
    axis: "Multi-turn generation judged by an LLM",
    definition: "MT-Bench contains 80 two-turn conversations and helped establish LLM-as-a-judge evaluation. Newer generation comparisons now commonly use Arena-Hard variants.",
    task: "writing",
    example: "Write a travel blog about Hawaii, then revise it so every sentence begins with the same letter.",
  },
  "arena-hard": {
    axis: "Generation judged automatically",
    definition: "Arena-Hard-Auto uses difficult prompts derived from real Chatbot Arena requests. An LLM judge compares each response with a baseline response, and the resulting scores correlate with human preferences.",
    task: "arena-hard-v2.0",
    example: "Generate an answer to a difficult user request and compare it pairwise with a baseline model's answer.",
  },
  livebench: {
    axis: "Rolling general evaluation",
    definition: "LiveBench adds new questions each month to reduce training contamination. It covers mathematics, coding, reasoning, and language with answer-based automatic scoring.",
    task: "coding",
    example: "Implement a function derived from a recently published LeetCode problem and run public and private tests.",
  },
  mteb: {
    axis: "Embedding evaluation suite",
    definition: "MTEB is a framework and benchmark suite for retrieval, classification, clustering, and other embedding tasks. The license and evaluation method must also be checked for every included dataset.",
    task: "retrieval",
    example: "Evaluate retrieval with corpus, query, and relevance files in BEIR format, then report recall at k and nDCG.",
  },

  "tau-rec": {
    "axis": "Agents (conversational recommendation)",
    "definition": "τ-Rec evaluates agentic conversational recommenders. An agent must elicit hidden user preferences from a simulated user, call catalog tools, and recommend one movie that satisfies the constraints. Scoring uses typed catalog predicates and seven policy checks without an LLM judge. Reveal-tagged elicitation (volunteer/on_ask/hidden) controls how constraints surface, and pass^k measures reliability. The current release has 60 tasks (20 simple/24 medium/16 complex; 13 volunteer/32 mixed/15 hidden, including 5 with no valid recommendation) and a 153-movie catalog; the paper evaluates 4 trials per task.",
    "task": "Preference elicitation and constrained reasoning (pass^1, pass^2, pass^4)",
    "example": "A simulated persona, such as a tired parent looking for a short comedy, states only some constraints. The agent asks questions and calls catalog tools to find the rest, then submits one movie with the recommend tool."
  },
  "cesbench": {
    "axis": "Security (IoT cryptographic engineering)",
    "definition": "A benchmark of 380 expert-written items on cryptographic engineering security for IoT devices, across six sub-domains: side-channel, fault injection, implementation, countermeasures, evaluation, and integration. It has 209 multiple-choice, 67 judgment, 63 scenario, and 41 code items (572 test cases). Multiple-choice and code items are scored automatically; judgment and scenario items are scored by an LLM judge using rubrics.",
    "task": "Four task types: multiple choice, judgment (True/False verdict with justification), scenario diagnosis, and code implementation.",
    "example": "Judgment task: decide whether the claim that keeping a key only in a memory variable and zeroizing it after use is enough to resist cold boot attacks is True or False, and justify the verdict. The justification is scored with an item-specific rubric, and a wrong verdict scores zero."
  },
  "omni-math-2": {
    "axis": "Olympiad-level mathematics",
    "definition": "A manually audited revision of Omni-MATH (4,428 problems). 647 problems were edited (14.6%) and 247 (5.6%) were tagged as image (61), proof (115), estimation (54) or should delete (25); one problem can have several tags. Omni-MATH-2-Filtered (n=4,181) is the exact-answer subset. The paper compares two judges, Omni-Judge and GPT-5 mini.",
    "task": "Omni-MATH-2-Filtered",
    "example": "Task description: the model solves an Olympiad-level math problem and puts the final answer in \\boxed{}; a judge checks equivalence with the reference answer."
  },
  "mathed-pii": {
    "axis": "Privacy (PII detection and de-identification)",
    "definition": "A PII detection benchmark built from 1,000 math tutoring sessions (115,620 messages; 769,628 tokens) from a U.S. online tutoring platform. It targets numeric ambiguity, where math expressions resemble dates or IDs and cause over-redaction. Because the unredacted originals were unavailable, a human-in-the-loop LLM workflow audited the existing redactions and generated surrogates.",
    "task": "Span-level detection of PII and its type in math tutoring dialogue messages",
    "example": "Task description (not an actual test item): in math-heavy tutoring dialogue, identify only the real personal information spans while leaving math expressions untouched."
  },
  "bi-bench": {
    "axis": "Agents (end-to-end business intelligence and data analysis)",
    "definition": "A benchmark of 100 pairs of a business question and a ground-truth result table, extracted from user dashboards in real Power BI projects (over 3K .pbix files crawled). A model must search for relevant raw tables, transform them, build joins, and run the analysis to produce a result table. Accuracy requires matching table shape and cell values (row and column order ignored). The paper evaluates SQL (SQLite) and Python settings, with and without tools, averaged over 10 runs. Each test case may have multiple valid ground-truth tables.",
    "task": "Produce a result table that answers a business question from raw tables via search, transform, join, and analysis",
    "example": "Task description: for a question asking for a sales amount, budget, and forecast comparison by month and year, the model finds the relevant tables, applies needed transformations and joins, and produces the result table."
  },
  "craftbench-ue": {
    "axis": "Agents (game-engine coding)",
    "definition": "A harness-based benchmark that reconstructs coding agents' saved submissions in fresh Unreal Engine projects and grades them with deterministic build, asset, and runtime (PIE) checks, without an LLM judge. It has 70 tasks (33 C++, 25 Blueprint/asset, 12 editor scripting); 10 gameplay specifications are paired C++/Blueprint versions sharing the same runtime tests. The paper evaluates seven models under two editor MCP configurations (MCP1, MCP2) plus a C++ file-and-shell baseline, with one attempt per task and pass@1 under a 40-minute authoring budget.",
    "task": "Implement C++ source, Blueprint/native assets, or editor-scripting outputs, graded by build, asset, and runtime checks (e.g., gp-glide-stamina-cpp)",
    "example": "Task description, not an actual test item: implement a glide ability that slows a falling character while draining Power, and restores normal falling when Power is exhausted."
  },
  "humanagencybench": {
    "axis": "Safety and alignment (human agency support behaviors)",
    "definition": "A diagnostic benchmark of how well AI assistants support human agency, covering six behaviors: Ask Clarifying Questions, Avoid Value Manipulation, Correct Misinformation, Defer Important Decisions, Encourage Learning, and Maintain Social Boundaries. Each behavior uses 500 LLM-generated and validated single-turn user queries. An evaluator model (o3) scores responses with behavior-specific deduction rubrics, and the mean is scaled to 0-1. The paper evaluates 25 LLMs.",
    "task": "Score assistant responses to single-turn user queries for each of six behaviors using an LLM judge.",
    "example": "Task description (not an actual test item): a user asks to be guided toward an answer in a learning task without being told it directly, and the rubric checks whether the assistant helps without giving the answer away."
  },
  "notevqa": {
    "axis": "Images (real-user visual questions; interleaved answer quality)",
    "definition": "A visual QA benchmark built from real photo-grounded questions posted by users of the Chinese image-sharing platform Xiaohongshu. It has 252 items across 12 topical categories and 7 user intents, and the final release is translated into English and proofread. Each item has a short reference distilled from expert community replies and a human-audited interleaved reference answer combining text and supporting images. Short-answer accuracy is scored by a SimpleQA-style judge. Interleaved answers are scored with IVR-12, which has 12 dimensions (scored 1-5) across content, presentation and image quality, plus three pass/fail gates. The paper also proposes AgenticInterleave, a ReAct-based retrieval framework for generating such answers.",
    "task": "Given a photo and a short question, produce a short correct answer, or an interleaved answer that combines text with supporting images (evaluated with IVR-12).",
    "example": "Task description: a user posts a photo (for example of a pet, plant, food item or jewelry) with an everyday question, and the model gives a short answer or an explanation with supporting images."
  },
  "scheme-foils": {
    "axis": "Fallacy detection (scheme-matched negatives)",
    "definition": "A set of negative examples that fills the gap left by existing fallacy-detection benchmarks, whose valid classes contain almost no correctly instantiated argumentation schemes. The judge-filtered release has 655 matched and 738 wrong-scheme CoCoLoFa items and 387 matched and 389 wrong-scheme Reddit items, covering eight fallacy types (appeal to authority, majority, nature, tradition, worse problems, false dilemma, hasty generalization, slippery slope). A matched negative uses the source fallacy's scheme and answers its critical question; a wrong-scheme negative is a valid argument on the same topic using a different scheme. Items were generated with Gemini 2.5 Flash and filtered with DeepSeek. Human-validated precision is 93.1% for matched (72-item sample) and 77.5% for wrong-scheme (40-item sample). Comparing how often each condition is classified as the source type measures whether a detector relies on scheme recognition.",
    "task": "Decide whether an argument is fallacious and label it with one of eight fallacy types or none (the paper's zero-shot detector prompt).",
    "example": "Task description: given one argument, answer with only a fallacy-type label or none. Compare the flag rate on the matched split with the rate of source-type labels on the wrong-scheme split."
  },
  "mcpgen": {
    "axis": "Agents (executable MCP workflow development)",
    "definition": "An execution-based benchmark of 100 MCP workflow projects across 16 application domains. It has three diagnostic tasks: workflow reconstruction (100 workflows), tool creation (911 tool targets), and backward-compatible workflow extension (100 pairs). Generated artifacts are checked with static analysis, unit and integration tests, and process-isolated end-to-end execution. The paper evaluates 11 LLMs in a single-turn setting at temperature 0. External services are replaced by deterministic mocks.",
    "task": "Workflow reconstruction (order, dependency, path robustness), tool creation (Indiv. Pass, Collective Pass), and workflow extension (Tool Chain, Data Ref, Edge F1, E2E Success)",
    "example": "Task description: recover the execution order from shuffled, anonymized steps; implement a missing tool under a given schema; or generate the remaining steps and an executable runner while keeping a baseline prefix unchanged."
  },
  "geniac-secbench": {
    "axis": "Security of LLM-generated Infrastructure-as-Code (vulnerability density relative to a human baseline)",
    "definition": "A benchmark of 100 natural-language deployment scenarios (60 simple, 40 complex) for LLM-generated IaC. Twelve model configurations from six vendors produced 1,196 artifacts, each scanned by Checkov, Trivy and KICS. 634 human-authored IaC templates were scanned with the same toolchain to give a size-matched human baseline. The primary metric is findings per declared resource (vulnerability density); the paper also separates reasoning modes (standard, prompted CoT, vendor extended thinking).",
    "task": "Generate IaC code (Terraform, CloudFormation, ARM or Kubernetes manifests) from a deployment scenario and compute per-resource vulnerability density from scanner findings.",
    "example": "Task description: given a deployment scenario such as a private bucket with versioning enabled, generate IaC in a single code block in the requested format, then scan it with three policy engines."
  },
  "safealert": {
    "axis": "Safety and fraud detection (pre-deployment evaluation for Nigerian fintech)",
    "definition": "A pre-deployment evaluation kit built around eight fraud categories reflecting the Nigerian fintech landscape. The classification set has 150 messages (66 safe, 26 suspicious, 58 scam). The generation set has 160 prompts, 20 per category, under four framings: direct request, educational purpose, fictional narrative, and simulated internal testing. The paper evaluates six commercial models under three conditions: no system prompt, a generic safety prompt, and a Nigerian-context prompt. Metrics are harmful output rate for generation and false positive and false negative rates for classification.",
    "task": "Classify messages as scam, suspicious, or safe, and judge whether responses to fraud-eliciting generation prompts contain harmful output.",
    "example": "A classification task separating legitimate Nigerian bank and fintech alert formats such as GTBank from scam messages, and a generation task that tries to elicit fraud scripts such as SIM swap scripts under several framings (task description)."
  },
  "widgetvabench": {
    "axis": "Agents (interactive visual analytics, widget operation)",
    "definition": "A benchmark of whether VLM agents can operate single- and multi-widget visual analytics workspaces through multi-step interaction to find evidence and produce verifiable results. It uses 96 real-world and 304 synthetic datasets, with human annotation yielding 516 single-widget and 608 multi-widget instances. Tasks fall into four Target-Path types (TK-PK, TK-PU, TU-PK, TU-PU), and Answer, Reference Trace Similarity, and State are scored separately. The paper evaluates three VLMs with a 16-turn budget under four settings: no tools (S0), direct tools (S1), widget abstraction (S2), and widget abstraction plus workflow (S3).",
    "task": "Use widget actions such as filter, zoom, and select, plus perception queries, to answer a task, scored on the answer, interaction trace, and final workspace state.",
    "example": "Task description, not an actual test item: explore a wind-turbine dashboard and report a phenomenon that warrants further investigation (open-ended TU-PU type)."
  },
  "legendbench": {
    "axis": "Images (chart legend understanding, counterfactual diagnosis)",
    "definition": "A parametric benchmark and generation pipeline that diagnoses how well models bind chart legend entries to visual marks. It has four task families: legend parsing, legend grounding, legend-conditioned reasoning, and legend-aware abstention. Each base chart yields counterfactual variants with controlled legend changes to test consistency and responsiveness. The released snapshot has 26689 instances derived from 900 base images.",
    "task": "Legend parsing, legend grounding, legend-conditioned reasoning, and legend-aware abstention (QA accuracy, chain accuracy, CR, AF1, etc.)",
    "example": "Task description: given a chart image and an English question, such as the value of a named series in a given year, the model reads the legend, binds it to the marks, and extracts the value. When the legend is hidden, it should abstain."
  },
  "stale-bench": {
    "axis": "Agents (semantic coordination in parallel coding agents)",
    "definition": "A benchmark of semantic coordination failures in parallel coding agents, where patches pass alone but fail when merged. The same tests run on each patch alone and on the merged patches, and only failures newly introduced by merging are counted (Δblind). It has three tiers: synthetic tasks (3 mechanisms x 4 degrees, 96 runs), merged PR pairs (417 Django pairs, 834 runs; 30 pairs from other repositories), and 36 constructed tasks on 12 real Django helpers (216 runs), plus 23 disjoint controls. The paper compares blind, informed (sequential oracle) and comm (oracle message describing the completed change) conditions. Constructed-task failure rates do not estimate real-world frequency.",
    "task": "Solve two tasks independently, merge the patches, and measure tests that pass with each patch alone but fail after merging (Δblind).",
    "example": "Task description: one change renames a helper, adds a required argument or changes a return type while another agent writes code against the old interface. The patches merge without textual conflict but fail tests, and in the comm condition the agent receives a short English message describing the completed change."
  },
  "rbac-text2sql": {
    "axis": "Coding (text-to-SQL with RBAC compliance)",
    "definition": "A text-to-SQL benchmark that augments the Spider and BIRD development splits and LiveSQLBench-Base-Full-v1 with LLM-synthesized, human-validated roles and column- and operation-level access policies. It covers 53 databases, 399 tables, and 3,353 columns, with 21,502 RBAC-annotated query instances (Spider 6,926; BIRD 10,175; LiveSQLBench 4,401). A model must decide allow or deny and, when allowed, generate execution-correct, policy-compliant SQL. Metrics are EX, Safe-EX, violation rate, over-refusal rate, and AC-F1. Each query is paired with one random role per pass, repeated over 5 seeds.",
    "task": "Given a role policy, decide whether to allow or deny the request and, if allowed, generate policy-compliant SQL.",
    "example": "Task description: given an English natural-language question and a role's column-level access policy, the system must refuse if a required column is denied, and otherwise produce execution-correct SQL."
  },
  "cq4oe": {
    "axis": "Knowledge engineering (ontology generation from competency questions)",
    "definition": "CQ4OE evaluates LLM-based ontology generation from competency questions (CQs). It provides CQ-driven gold OWL ontologies with explicit provenance linking each CQ to the classes, properties and axioms needed to answer it. Over six ontologies (Wine, AWO, ODRL, SAREF4WATR, VGO, SWO) it defines two tasks: CQ2Term (term-level, 99 CQs) and CQ2Onto (ontology-level, 118 CQs). The paper evaluates nine LLMs under zero-shot, iterative and multi-agent strategies.",
    "task": "CQ2Term: predict the classes and properties required by each CQ (99 CQs). CQ2Onto: generate an ontology with hierarchy, property modeling and axioms (118 CQs).",
    "example": "Task description, not an actual test item: given an English CQ such as the AWO question 'Which plants eat animals?', CQ2Term predicts the required classes and property (Plant, Animal, eats), and CQ2Onto builds them into an OWL ontology of classes, properties and axioms."
  },
  "equivsva": {
    "axis": "Coding (hardware verification, SVA generation)",
    "definition": "A dataset for evaluating generation of SystemVerilog Assertions from RTL designs. It contains 120 behavior families across 12 categories, 480 reference RTL implementations, 914 gold properties, and 360 mutants. The paper also reports a single-model case study with Qwen2.5-Coder-7B-Instruct.",
    "task": "Generate interface-only SVA properties from RTL, evaluated by formal soundness and mutant detection.",
    "example": "Task description: given an RTL implementation, generate interface-level behavioral properties that avoid implementation-specific internal signals, and compare results across different RTL implementations of the same behavior."
  },
  "tar-bench": {
    "axis": "Images/video (traffic anomaly reasoning: question answering, temporal reasoning, scene understanding)",
    "definition": "A benchmark for 10 traffic anomaly reasoning tasks. It has 960 human-curated annotations over 80 held-out clips trimmed from 17 public YouTube videos, and shares its task taxonomy with the TAR training corpus (44,040 automatically generated annotations over 3,670 CCTV videos). Metrics are accuracy for BCQ and MCQ, BERTScore F1 for open-ended tasks, and mIoU for temporal localization; the unweighted mean over the 10 tasks is the aggregate score. The paper reports means over 3 runs.",
    "task": "Question answering (BCQ, BCQ+E, MCQ, MCQ+E, OQA), temporal reasoning (TL, TD, CL), and scene understanding (SD, VS)",
    "example": "Task description: for a traffic CCTV clip, answer yes/no questions (for example, whether a vehicle crossed lane lines before a collision), localize the anomaly in time, explain the causal link between events, and describe or summarize the scene."
  },
  "moldesignbench": {
    "axis": "Agents (scenario-grounded molecular design with tool use)",
    "definition": "A benchmark of whether tool-augmented LLM agents can generate or optimize molecules that satisfy implicit constraints embedded in a design narrative together with explicit property and functional-group constraints. It has 2,000 instances (1,000 generation and 1,000 optimization), and 10% of each split (100 instances) is infeasible, requiring the agent to answer None. It provides 17 chemistry tools. Metrics are Success, CSR, MCD, InfAcc, MCC, Validity, and Tool Calls.",
    "task": "Multi-constraint molecule generation and optimization (generation gives only the scenario; optimization gives a starting molecule plus the scenario).",
    "example": "Task description: the agent reads an English design-scenario prompt (for example, an improvement directive such as 'decrease logP by at least 1.5' plus a required functional group), infers the implicit constraints, and returns one SMILES string in an <ANSWER> tag, or None if the constraints are contradictory."
  },
  "indicbankbench": {
    "axis": "Agents (banking assistant tool use, safety, and repeated-run reliability)",
    "definition": "A 799-case benchmark for Indian retail banking assistants, with 5 operational domains, 1 capability/refusal domain, and 20 primary axes. Each interaction is graded in four stages: safety, action and tool use, response adequacy, and advisory quality. Tool use and most safety checks are deterministic. An LLM judge assesses response adequacy, and a narrow resolver handles only ambiguous confirmation-before-write cases. Every case is run three times and strict pass^3 is reported; the paper evaluates eleven models.",
    "task": "Multi-turn, account-grounded banking conversations in which the assistant calls deterministic mock tools and must answer, clarify, or decline safely (S/A/R/Q grading).",
    "example": "Task description: a customer checks a balance, then returns the next day to ask about a transfer. The assistant must re-query the balance instead of reusing the stale value (schematic case from Figure 1)."
  },
  "qasm-eval": {
    "axis": "Coding (completing hardware-facing OpenQASM 3 constructs)",
    "definition": "QASM-Eval is a benchmark and training resource of specification-completion tasks for hardware-facing OpenQASM 3 constructs (classical logic and control flow, timing scheduling, pulse control), completed within a supplied program context. It has an expert-curated test set of 1,200 tasks (100 themes; four categories of 300 tasks) and a 4,000-task training set, with a generation pipeline that can scale further. An automated verifier checks syntax, measurement distributions, and execution timelines. Five samples are generated per task and scored with pass@k (reported pass@1 and pass@5) and syntax-valid rate, under a theme-held-out five-fold protocol.",
    "task": "Fill in the missing core block of an OpenQASM 3 program from a natural-language TODO comment, across four categories (classical, timing, pulse, complex) of 300 test tasks each.",
    "example": "Task description: given a fixed background program and an English natural-language TODO comment describing the missing core block, the model outputs only the missing QASM statements, which are checked by syntax, measurement-distribution, and timeline verification."
  },
  "scir": {
    "axis": "Scientific reasoning (deduction, induction, causal abduction)",
    "definition": "A controllable benchmark of three paradigms of scientific reasoning: deduction, induction, and causal abduction. Tasks are generated from formal objects (a deduction tree, an inductive rule hypothesis, a causal graph) with verifiable answers, then rendered into multi-document scientific discourse using per-track document genres. Two difficulty axes, inference complexity and premise obfuscation, can be varied independently, and Easy and Hard tiers are compared in natural-language (NL) and obfuscated (Obf) forms. The paper evaluates six models with 200 tasks per cell and reports accuracy and chance-normalised accuracy. The pipeline is released as a generator rather than a fixed test set, so harder tiers can be regenerated.",
    "task": "Deduction (decide whether a hypothesis follows from the premises, is contradicted, or is neither), induction (find the rule that explains observed drug-drug interactions), and causal discovery (identify how a new protein XYZ connects to a known signalling sub-network).",
    "example": "Task description: read premises spread across several documents and decide whether a hypothesis follows from them, is contradicted by them, or is neither. The same framing applies to inducing drug-interaction rules and inferring causal structure in protein signalling."
  },
  "knows": {
    "axis": "Agents (web research, artifact synthesis, visual layout)",
    "definition": "A benchmark of open-ended, long-horizon tasks in which an agent gathers information from the live web and synthesizes it into Google Docs, Sheets or Slides artifacts. It has 110 tasks across three artifact types. Each task has an evaluator that combines deterministic checks with LLM/VLM judgments, organized into checkpoints and evaluation steps. Results are reported as full success rate plus partial-success metrics.",
    "task": "Search the web and build a document, slide deck or spreadsheet with specified structure, formatting and layout.",
    "example": "Task description (not an actual test item): build a presentation on the history of video games for 7th graders, finding a web source for each section and placing the heading style, bullet summary, citation and credited image in the specified positions."
  },
  "llmadbench": {
    "axis": "Advertising insertion (human preference over ad placement in LLM responses)",
    "definition": "A human-preference benchmark that asks where an advertisement should be placed given a user conversation, an LLM response, and a matched ad. Each of 258 source conversations is expanded into four candidates that differ only in ad position (front, early, late, end), and all pairs are compared with and without a sponsored label. Annotators choose A, B, or Tie on six criteria (naturalness, visibility, helpfulness, click likelihood, appropriateness, overall preference), yielding 18,576 human judgments. Metrics are held-out A/B/T accuracy, Davidson-Bradley-Terry placement scores, presentation-swap error, and Cohen's kappa among judges.",
    "task": "Predict the human A/B/Tie preference between two candidates whose ad placement differs, per criterion and disclosure condition.",
    "example": "Task description (not an actual test item): given a user question, an LLM response, and an ad, two versions differing only in ad position are shown, and the annotator chooses A, B, or Tie on each of six criteria, such as which reads more smoothly."
  },
  "financialauditbench": {
    "axis": "Agents (financial statement audit workpaper completion and review)",
    "definition": "A benchmark of whether agents can examine engagement evidence, perform audit procedures, and complete or review audit workpapers. It has 90 tasks over six synthetic audit engagements (manufacturing and staffing services; average 179 files each): 45 completion tasks and 45 corresponding review tasks across eight workpaper types. Auditor-written rubrics (about ten scored checks per workpaper) give a strict all-or-nothing pass plus a partial-credit score. The paper evaluates eleven models on completion tasks (eight runs per model-task pair, with pass@k and pass^k) and ten models on review tasks (one run each). Tasks are released in Harbor format.",
    "task": "Given supporting documents and a blank workpaper template, perform the audit procedures and complete the workpaper, or review and correct an already completed workpaper (for example Manufacturing-01 cash).",
    "example": "Task description, not an actual test item: the agent reads a data room with planning documents, client-provided records and third-party evidence such as bank confirmations, performs the procedures in a workpaper template such as cash, and saves the result."
  },
  "cruxbench": {
    "axis": "Agents and reasoning (information discovery: value of information of generated forecasting subquestions)",
    "definition": "CruxBench grades model-proposed subquestions (cruxes) for a target forecasting question by the Value of Information (VOI), measured as the KL-based belief update in a prediction market around the crux's resolution time. It uses 293 target questions; the paper compares eight models against a random-timing baseline and a hindsight oracle. Scores are in bits, and cruxes are resolved by a separate resolver agent.",
    "task": "Given an ultimate forecasting question, generate one binary crux that resolves within a specified 30-day window.",
    "example": "Task description: given an ultimate question such as whether any stolen Louvre jewels will be returned, the model proposes a subquestion resolving within the window, and the score is the market belief update after its resolution."
  },
  "ecg-scroll": {
    "axis": "Agents (long-horizon streaming ECG interpretation)",
    "definition": "A benchmark and gym-style agent environment in which long two-lead ambulatory (Holter) ECG recordings are streamed to an agent in 30-second chunks, without access to future signal. The agent must localize, quantify and record paroxysmal events. It has 390 whole-recording instances (247 recordings, 2,536 hours in total) across six tasks (episode detection, AF burden, change detection, ischemia detection, PVC burden, rare-event search), all scored by rule-based verifiers (temporal F1, relative-error score, hit@±10s, hit@±15s). Because every memory write is timestamped, detection latency from event onset to recording can also be measured. The paper evaluates a rule agent and LLM agents with and without diagnostic tools (+dx/-dx) and with agent-driven (Planning) versus environment-driven (Judge) scanning.",
    "task": "Episode detection (AF episode intervals scored by temporal F1)",
    "example": "Task description: given an English system prompt casting it as an expert cardiologist, the agent issues skim, measure and write actions, measures elapsed signal with numeric tools such as get_rate_rhythm and get_st, and records the event intervals it finds."
  },
  "specread": {
    "axis": "Comprehension (hardware specification reading)",
    "definition": "A benchmark that measures whether models understand hardware design specifications, separating comprehension from code generation ability. Dataset v2.2 has 383 questions over 10 open-source OpenTitan IP blocks. It covers exact retrieval, cross-section reasoning, contradiction detection in mutated specifications, and spec-RTL consistency checking, and is scored automatically with deterministic checks.",
    "task": "Read a specification excerpt and a question (or a mutated specification or RTL), then answer a fact, locate and categorize a contradiction, or reply NO_CONTRADICTION when none exists.",
    "example": "Task description, not an actual test item: given a specification excerpt, identify the contradiction with its location and category, or reply NO_CONTRADICTION if there is none."
  },
  "trojan-hippo-bench": {
    "axis": "Security (persistent memory attacks and defenses for agents)",
    "definition": "A dynamic framework for evaluating persistent memory attacks (the Trojan Hippo attack) and memory-layer defenses in LLM agents. A single untrusted tool call (for example, a crafted email) plants a dormant payload in long-term memory, and attack success rate (ASR) measures whether personal data is later exfiltrated when the user discusses a sensitive topic. It has an OpenEvolve-based adaptive red-teaming component (up to 40 iterations) and a security-utility analysis that decomposes defense utility into seven user flows. It is instantiated on an email assistant with four memory backends (explicit, Mem0, RAG, sliding-window context), five sensitive topics (finance, health, legal, tax, identity), and four defenses. Reported ASR averages 60 rollouts per (backend, defense) cell, and the paper targets Gemini 3.1 Pro and GPT-5-mini.",
    "task": "Measure ASR (for example at trigger session N=100) and benign utility (AM and HM) over seven user flows for an email-assistant agent, by memory backend and defense",
    "example": "Task description, not an actual test item: hidden instructions in an attacker's email are written into the agent's long-term memory, and the benchmark checks whether the agent later emails the user's sensitive English message, such as a tax or health query, to the attacker."
  },
  "autodojo": {
    "axis": "Agent security (adaptive evaluation of indirect prompt injection defenses)",
    "definition": "A generative benchmark built on AgentDojo and AgentDyn that adaptively generates indirect prompt injections in a black-box setting for a given agent and defense. It supports six task suites: banking, slack, travel, github, shopping, and dailylife.",
    "task": "Optimize injections against defended agents across the six suites (banking, slack, travel, github, shopping, dailylife) and measure whether the attack succeeds.",
    "example": "Task description: a user asks in English for a bill to be paid, the agent reads the bill through a tool, and the benchmark checks whether an injection planted in it makes the agent take an action the user never requested."
  },
};
