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
};
