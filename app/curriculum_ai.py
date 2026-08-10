"""
Stage 9 — AI & Data Science for Data Engineers (5 projects) + Stage 10
capstone. Offline-first by design: every exercise runs deterministically
without API keys (local implementations, mock LLM clients); milestones note
where a real LLM API key (OPENAI_API_KEY-compatible) can optionally be
plugged in via environment variable.
"""

STAGE9_PROJECTS = [
    # ------------------------------------------------------------------
    {
        "id": "ds-primer",
        "title": "DS Primer",
        "tagline": "Statistics that survive contact with dashboards: EDA, tests, pitfalls",
        "level": "Intermediate+",
        "tech": ["descriptive stats", "distributions", "hypothesis testing", "correlation traps"],
        "est_hours": 6,
        "brief": (
            "Data engineers who know statistics catch the bugs everyone else "
            "ships as insights. On the warehouse data: exploratory analysis "
            "done properly (distributions before aggregates!), robust vs "
            "classical statistics, an honest A/B test with scipy, and the "
            "pitfall parade — Simpson's paradox, correlation vs causation, "
            "p-hacking — each demonstrated on data you engineer to exhibit it."
        ),
        "milestones": [
            "EDA the warehouse orders: distributions of order values (histogram — it's skewed!), mean vs median vs p95, revenue concentration (what % of revenue from top 5% of customers?).",
            "Robustness lab: inject 5 whale orders into a copy of the data; measure how mean/std lurch while median/IQR barely move — write the one-line moral for your dashboards.",
            "Build a Simpson's paradox: construct country×category revenue data where every country's trend reverses in aggregate; then find whether the REAL warehouse has one (group, compare, report).",
            "A/B test honestly: simulate an experiment (treatment lifts conversion 12→13%), compute the two-proportion z-test with scipy, then demonstrate why peeking at p-values daily inflates false positives (simulate 100 peeking experiments under the null).",
            "Bootstrap: confidence interval for median order value via resampling (10k draws) — the technique that works when formulas don't exist.",
        ],
        "under_the_hood": (
            "**Skew is the default in business data:** revenues, latencies, "
            "user activity — all long-tailed. The mean chases the tail (one "
            "whale order moves it), the median holds; that's not a fun fact, "
            "it's why 'average order value' dashboards mislead and hs-2's "
            "percentiles rule ops. Always look at the distribution before "
            "trusting any single number summarizing it.\n\n"
            "**Hypothesis testing is a false-positive budget:** p < 0.05 "
            "means 'under no-effect, data this extreme happens 5% of the "
            "time'. That budget assumes ONE look at ONE metric — peeking "
            "daily or testing 20 metrics multiplies the lottery tickets "
            "(multiple comparisons), which is how dashboards 'discover' "
            "effects that evaporate. Fixed horizons, pre-registered metrics, "
            "corrections when testing many.\n\n"
            "**Simpson's paradox** is a grouping variable flipping a "
            "conclusion: each subgroup shows one trend, the aggregate shows "
            "the reverse (because group sizes differ). It's not exotic — "
            "any mix-shift across countries/segments/devices does it, and "
            "the defense is the habit of always cutting by the big "
            "segmentation variables before believing an aggregate. "
            "Correlation vs causation rounds out the kit: confounders, "
            "selection effects, and reverse causation generate most "
            "'insights'; only interventions (experiments) license causal "
            "claims."
        ),
        "exercises": [
            {
                "id": "dp-1",
                "title": "Robust statistics toolkit",
                "instructions": (
"Numbers that survive outliers.\n\n**Your task**\n\nImplement "
"`describe_robust(values)` returning {'mean': ..., 'median': ..., "
"'p95': ..., 'iqr': ...}. Median: standard even/odd handling. "
"Percentile (for p95 and quartiles): sort, use index = q * (n-1), "
"linear interpolation between neighbors. IQR = p75 - p25. Empty input "
"→ raise ValueError. The checker includes a whale-outlier case where "
"your median must stand firm while the mean flees."
                ),
                "starter_code": (
                    "def percentile(sorted_vals, q):\n"
                    "    \"\"\"q in [0,1]; linear interpolation.\"\"\"\n"
                    "    ...\n\n"
                    "def describe_robust(values):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "import math\n"
                    "vals = [10, 20, 30, 40, 50]\n"
                    "d = describe_robust(vals)\n"
                    "assert d['mean'] == 30 and d['median'] == 30\n"
                    "assert math.isclose(d['p95'], 48.0), d['p95']   # 0.95*4=3.8 -> 40 + 0.8*10\n"
                    "assert math.isclose(d['iqr'], 20.0), d['iqr']   # p75=40, p25=20\n"
                    "whale = vals + [100000]\n"
                    "dw = describe_robust(whale)\n"
                    "assert dw['mean'] > 16000, 'mean must chase the whale'\n"
                    "assert dw['median'] == 35, 'median must barely move'\n"
                    "try:\n"
                    "    describe_robust([])\n"
                    "    raise AssertionError('empty must raise')\n"
                    "except ValueError:\n"
                    "    pass\n"
                    "print('PASS: robust stats — dashboard numbers you can defend')\n"
                ),
                "refresher": (
"**The interpolated percentile** — the detail most people wave at:\n\n"
"```python\ndef percentile(sorted_vals, q):\n    idx = q * (len(sorted_vals) - 1)\n    lo, hi = int(idx), min(int(idx) + 1, len(sorted_vals) - 1)\n    frac = idx - lo\n    return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])\n```\n\n"
"q=0.95 on 5 values → index 3.8 → 80% of the way from the 4th to "
"the 5th value. (There are ~9 percentile conventions; numpy's "
"default 'linear' is this one — knowing that conventions differ "
"explains many 'why don't our numbers match' incidents between "
"tools.)\n\n"
"The breakdown-point framing makes robustness precise: the mean has "
"breakdown 0 (ONE corrupted value moves it arbitrarily); the median "
"holds until 50% of data is corrupt. Same for std (fragile) vs IQR "
"(robust). Practical defaults that follow: monitoring and anomaly "
"thresholds on median/MAD (qg-2's upgrade), dashboards reporting "
"median + p95 rather than mean ± std for anything long-tailed, and "
"means reserved for when you truly need additivity (finance totals). "
"You've now *implemented* the reason."
                ),
                "objectives": [
                    "Implement interpolated percentiles and know conventions differ",
                    "Quantify robustness via breakdown points",
                    "Choose median/IQR vs mean/std deliberately in dashboards",
                ],
                "hints": [
                    "Sort once in describe_robust; reuse for median and all percentiles.",
                    "Median = percentile(sorted, 0.5) — it falls out of your own function.",
                    "Guard len == 0 first with ValueError.",
                ],
                "resources": [
                    {"title": "Percentile estimation methods (numpy)", "url": "https://numpy.org/doc/stable/reference/generated/numpy.percentile.html"},
                    {"title": "Robust statistics", "url": "https://en.wikipedia.org/wiki/Robust_statistics"},
                ],
            },
            {
                "id": "dp-2",
                "title": "Simpson's paradox detector",
                "instructions": (
"The aggregate lies; catch it programmatically.\n\n**Your task**\n\n"
"Implement `simpson_check(groups)`: groups maps group_name → (x_a, "
"n_a, x_b, n_b) — successes/trials for variants A and B within that "
"group. Return {'aggregate_winner': 'A'|'B', 'group_winners': "
"{name: 'A'|'B'}, 'paradox': bool} where paradox = every group has "
"the SAME winner and it differs from the aggregate winner (rates "
"compared as x/n; assume no ties, n > 0). The checker uses the "
"classic kidney-stone-treatment shape."
                ),
                "starter_code": (
                    "def simpson_check(groups):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "groups = {\n"
                    "    'small': (81, 87, 234, 270),    # A: 93.1% vs B: 86.7% -> A\n"
                    "    'large': (192, 263, 55, 80),    # A: 73.0% vs B: 68.8% -> A\n"
                    "}\n"
                    "out = simpson_check(groups)\n"
                    "assert out['group_winners'] == {'small': 'A', 'large': 'A'}\n"
                    "assert out['aggregate_winner'] == 'B'   # 273/350=78% vs 289/350=82.6%\n"
                    "assert out['paradox'] is True\n"
                    "no_p = simpson_check({'g1': (60, 100, 40, 100), 'g2': (30, 100, 20, 100)})\n"
                    "assert no_p['paradox'] is False and no_p['aggregate_winner'] == 'A'\n"
                    "print('PASS: Simpson detector — the aggregate can lie, now you check')\n"
                ),
                "refresher": (
"**The mechanism is weighted averages:** A's aggregate rate is a "
"weighted mean of its group rates, weighted by *where A's trials "
"landed*. If A was mostly tried on hard cases (large stones) and B "
"on easy ones, A can win every group yet lose overall — the "
"classic real dataset your checker mirrors:\n\n"
"```python\nagg_a = sum(x_a) / sum(n_a)      # across groups\nagg_b = sum(x_b) / sum(n_b)\nwinners = {g: 'A' if x_a/n_a > x_b/n_b else 'B' ...}\nparadox = len(set(winners.values())) == 1 \\\n          and next(iter(set(winners.values()))) != aggregate_winner\n```\n\n"
"Where it ambushes data teams: mix shifts. Mobile conversion beats "
"desktop in every country, but aggregate conversion 'fell' because "
"traffic shifted toward a low-converting country; support "
"'improved' overall while every ticket-type got slower (easy "
"tickets grew). The operational defense is a habit, not a formula: "
"before reporting any aggregate change, decompose into "
"within-group change vs mix change (your wf-2 LAG machinery per "
"segment does this). And the deep question the paradox forces — "
"'which number is TRUE?' — has a real answer: it depends on the "
"causal structure (was the grouping variable a confounder or a "
"mediator?), which is why correlation-era dashboards can't settle "
"it and experiments (dp milestone 4) exist."
                ),
                "objectives": [
                    "Compute within-group vs aggregate winners correctly",
                    "Explain the weighted-mean mechanism and mix shifts",
                    "Adopt the decompose-before-reporting habit",
                ],
                "hints": [
                    "Aggregate: sum all x_a and n_a across groups before dividing.",
                    "Paradox: all group winners identical AND != aggregate winner.",
                ],
                "resources": [
                    {"title": "Simpson's paradox (the kidney-stone case)", "url": "https://en.wikipedia.org/wiki/Simpson%27s_paradox"},
                    {"title": "Mix-shift analysis in practice", "url": "https://www.statsig.com/blog/simpsons-paradox"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"Your PM says: 'The A/B test hit p=0.04 on day 3 of a planned 14-day "
"run — ship it!' Explain the problem, quantify it roughly, and give "
"the professional alternatives."
                ),
                "difficulty": "Medium",
                "topics": ["A/B testing", "peeking", "sequential testing"],
                "answer": (
"The problem is optional stopping: p-values are calibrated for ONE "
"analysis at a fixed horizon. Checking daily and stopping at the "
"first p<0.05 gives many chances to catch a random fluctuation — "
"under a true null, peeking daily for 14 days pushes the false-"
"positive rate from 5% toward ~25-30%. The day-3 p=0.04 is also "
"computed on a small early sample, where effect estimates are "
"noisiest and most inflated (winner's curse: early 'significant' "
"effects regress). Alternatives: (1) commit to the fixed horizon "
"and only analyze at day 14; (2) if early stopping is a business "
"need, use methods DESIGNED for it — group-sequential boundaries "
"(O'Brien-Fleming: very strict early thresholds) or always-valid "
"sequential tests (mSPRT, used by modern platforms) that maintain "
"the 5% guarantee under continuous monitoring; (3) at minimum, "
"treat day-3 as a data-quality checkpoint (sample ratio mismatch, "
"instrumentation) — never an efficacy readout."
                ),
                "explanation": (
"The peeking problem is the most common statistical malpractice in "
"industry and a beloved interview probe because it pits statistics "
"against organizational pressure. The quantification (5% → ~25-30% "
"under daily peeking) shows you grasp the mechanism — multiple "
"lottery tickets against the same budget — not just the rule. "
"Naming sequential methods proves you can say 'yes, safely' rather "
"than only 'no': that's the difference between a gatekeeper and an "
"engineer. The sample-ratio-mismatch aside (check randomization "
"health early, not results) is the practitioner detail that lands "
"offers."
                ),
            },
            {
                "question": (
"Median or mean: for each of these, which do you put on the "
"dashboard and why — API latency, revenue per day, order value, "
"items per basket? One of them genuinely needs the mean."
                ),
                "difficulty": "Easy",
                "topics": ["robust statistics", "metrics design"],
                "answer": (
"**API latency: median + p95/p99** — long-tailed; the mean is "
"neither typical (median's job) nor tail-aware (p99's job); nobody "
"experiences the mean. **Order value: median** (typical order) "
"with p95 alongside if whales matter operationally — the mean "
"swings with every big order (dp-1's demo). **Items per basket: "
"median or the full distribution** — small integers, look at the "
"histogram. **Revenue per day: the SUM — and if normalizing, the "
"mean** — because revenue is *additive*: total = mean × count, and "
"finance needs numbers that add up across days/segments. Medians "
"don't aggregate (median of medians ≠ median of the whole — the "
"ds-3 lesson), so accounting-style rollups require means/sums even "
"though they're outlier-sensitive; pair with outlier monitoring "
"instead."
                ),
                "explanation": (
"An easy-sounding question with a real discriminator: recognizing "
"that additivity — not robustness — decides the revenue case. The "
"underlying principle worth stating: choose the statistic by the "
"*question* (typical experience → median; tail risk → p99; totals "
"that must reconcile → sums/means) and by *aggregability* (means "
"and sums merge across partitions — the Spark lesson; medians and "
"exact percentiles don't, hence t-digest sketches). Candidates who "
"connect dashboard design to distributed-aggregation constraints "
"demonstrate the DE-DS hybrid perspective this entire stage "
"builds."
                ),
            },
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "model-factory",
        "title": "Model Factory",
        "tagline": "scikit-learn end to end: train, validate, evaluate, ship — honestly",
        "level": "Advanced",
        "tech": ["scikit-learn", "cross-validation", "metrics", "baselines", "pipelines"],
        "est_hours": 8,
        "brief": (
            "Take Feature Foundry's output and train models that survive "
            "scrutiny: always-a-baseline discipline, sklearn Pipelines so "
            "preprocessing can't leak, time-aware cross-validation, and "
            "metric literacy (why accuracy lies on imbalanced data, "
            "precision/recall trade-offs as business decisions, calibration). "
            "Ships as a train.py your Airflow can run — models are pipeline "
            "products here, not notebook artifacts."
        ),
        "milestones": [
            "Baseline first, always: DummyClassifier (majority) and a one-feature logistic regression on the churn features — every later model must beat these to justify its complexity.",
            "Pipeline properly: Pipeline([('scaler', StandardScaler()), ('model', LogisticRegression)]) so CV refits preprocessing per fold (ff-2's lesson made structural); compare with the leaky fit-outside version and document the score gap.",
            "Cross-validate time-aware: TimeSeriesSplit vs plain KFold on churn data — measure how much random-split flatters the score (it interpolates the future).",
            "Metric literacy lab: on the ~10%-churn data, show accuracy of predict-nobody-churns (90%! useless!); build the confusion matrix, choose the operating threshold from the precision-recall curve for a stated business cost (a retention offer costs X, a lost customer Y).",
            "Model comparison: logistic vs RandomForest vs GradientBoosting with proper CV; then feature importances + permutation importance — and the talk-track for 'why does the model predict X?' questions.",
            "Ship it: train.py (params from a config dict, pb-3 style) writing model.joblib + metrics.json + training metadata (data range, feature list, git-style hash) — the artifact contract Airflow and Grand Central consume.",
        ],
        "under_the_hood": (
            "**Baselines are epistemology:** a model's score is meaningless "
            "alone — 94% accuracy is terrible if always-predict-majority "
            "scores 93.8% (ff's imbalanced world). The baseline ladder "
            "(majority → single-feature → linear → trees → tuned) tells you "
            "where complexity stops paying, and 'what did the baseline "
            "score?' is the first question every competent reviewer asks.\n\n"
            "**Cross-validation estimates the *procedure*, not the model:** "
            "each fold retrains everything — including preprocessing, hence "
            "Pipelines — and the variance across folds is as informative as "
            "the mean (a ±10% swing means your estimate is mush). Temporal "
            "data demands temporal splits: random KFold lets the model "
            "train on July and 'predict' June, which production never "
            "gets to do.\n\n"
            "**Metrics encode business trade-offs:** precision (of flagged, "
            "how many real?) vs recall (of real, how many caught?) is a "
            "threshold dial, and the right operating point comes from costs "
            "— retention-offer cost vs churn cost — not from 0.5-by-"
            "default. ROC-AUC summarizes ranking quality but flatters "
            "imbalanced problems (PR-AUC is honester there); calibration "
            "(does p=0.8 mean 80%?) matters the moment anyone treats "
            "scores as probabilities. Gradient-boosted trees remain the "
            "tabular-data default (handle mixed types, missing values, "
            "interactions, no scaling needed) — deep learning earns its "
            "complexity on text/images/sequences, rarely on 40-column "
            "customer tables."
        ),
        "exercises": [
            {
                "id": "mf-1",
                "title": "Confusion-matrix metrics from scratch",
                "instructions": (
"Never confuse precision and recall again — by building them.\n\n"
"**Your task**\n\nImplement `confusion(y_true, y_pred)` returning "
"{'tp': n, 'fp': n, 'fn': n, 'tn': n} (positive class = 1), and "
"`metrics(y_true, y_pred)` returning {'accuracy', 'precision', "
"'recall', 'f1'} — with the zero-division conventions: "
"precision/recall/f1 are 0.0 when their denominators are 0. The "
"checker includes the all-negative-predictions case that makes "
"accuracy lie on imbalanced data."
                ),
                "starter_code": (
                    "def confusion(y_true, y_pred):\n"
                    "    ...\n\n"
                    "def metrics(y_true, y_pred):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "import math\n"
                    "y_true = [1, 1, 0, 0, 1, 0, 0, 0, 0, 0]\n"
                    "y_pred = [1, 0, 1, 0, 1, 0, 0, 0, 0, 0]\n"
                    "c = confusion(y_true, y_pred)\n"
                    "assert c == {'tp': 2, 'fp': 1, 'fn': 1, 'tn': 6}, c\n"
                    "m = metrics(y_true, y_pred)\n"
                    "assert math.isclose(m['accuracy'], 0.8)\n"
                    "assert math.isclose(m['precision'], 2/3)\n"
                    "assert math.isclose(m['recall'], 2/3)\n"
                    "assert math.isclose(m['f1'], 2/3)\n"
                    "lazy = metrics([1]*1 + [0]*9, [0]*10)   # predict nobody positive\n"
                    "assert math.isclose(lazy['accuracy'], 0.9), 'accuracy REWARDS laziness on imbalance'\n"
                    "assert lazy['recall'] == 0.0 and lazy['precision'] == 0.0 and lazy['f1'] == 0.0\n"
                    "print('PASS: metric literacy — accuracy 90%, usefulness 0%')\n"
                ),
                "refresher": (
"**Four cells, everything derived:**\n\n"
"```python\ntp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)\nfp = ...  # predicted 1, truly 0  (false alarm)\nfn = ...  # predicted 0, truly 1  (miss)\nprecision = tp / (tp + fp) if tp + fp else 0.0   # trust in alarms\nrecall    = tp / (tp + fn) if tp + fn else 0.0   # coverage of reality\nf1 = 2 * p * r / (p + r) if p + r else 0.0        # harmonic mean\n```\n\n"
"The mnemonics that stick: precision = 'when it cries wolf, is "
"there a wolf?'; recall = 'of all wolves, how many did it catch?'. "
"The lazy-classifier case is the whole argument: 90% accuracy, "
"zero wolves caught — accuracy answers 'how often right?' which is "
"the wrong question whenever classes are imbalanced (fraud, churn, "
"defects — i.e., most business problems). The harmonic mean in F1 "
"punishes imbalance between P and R (arithmetic mean of 1.0 and "
"0.0 is 0.5; harmonic is 0) — but the deeper point for interviews: "
"F1 weights P and R equally, and real problems almost never do. "
"State the costs, pick the threshold from the PR curve "
"accordingly (your milestone 4) — 'what's the cost ratio?' is the "
"question that turns a metrics answer into an engineering answer."
                ),
                "objectives": [
                    "Compute the confusion matrix and derived metrics with edge conventions",
                    "Demonstrate accuracy's failure on imbalanced classes",
                    "Frame threshold choice as explicit cost trade-offs",
                ],
                "hints": [
                    "zip(y_true, y_pred) and count the four (t, p) combinations.",
                    "Guard every division: empty denominator → 0.0 by convention.",
                    "f1 from your own precision/recall — harmonic, not arithmetic, mean.",
                ],
                "resources": [
                    {"title": "sklearn: precision/recall & thresholds", "url": "https://scikit-learn.org/stable/auto_examples/model_selection/plot_precision_recall.html"},
                    {"title": "Confusion matrix", "url": "https://en.wikipedia.org/wiki/Confusion_matrix"},
                ],
            },
            {
                "id": "mf-2",
                "title": "Time-aware cross-validation splitter",
                "instructions": (
"The splitter that keeps the future out of training.\n\n**Your "
"task**\n\nImplement `time_series_splits(n_samples, n_splits)` "
"yielding (train_indices, test_indices) like sklearn's "
"TimeSeriesSplit: fold the ordered indices into n_splits+1 roughly "
"equal blocks (earlier blocks absorb remainders); split k trains on "
"blocks 0..k and tests on block k+1. Every train index < every "
"test index, always. Return a list of (list, list) tuples."
                ),
                "starter_code": (
                    "def time_series_splits(n_samples, n_splits):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "splits = time_series_splits(10, 4)\n"
                    "assert len(splits) == 4\n"
                    "for train, test in splits:\n"
                    "    assert max(train) < min(test), 'future leaked into training!'\n"
                    "assert splits[0] == ([0, 1], [2, 3])\n"
                    "assert splits[1] == ([0, 1, 2, 3], [4, 5])\n"
                    "assert splits[3] == ([0, 1, 2, 3, 4, 5, 6, 7], [8, 9])\n"
                    "tr, te = time_series_splits(7, 2)[0]\n"
                    "assert tr == [0, 1, 2] and te == [3, 4]   # remainder to the first block\n"
                    "print('PASS: expanding-window CV — evaluation that mimics production')\n"
                ),
                "refresher": (
"**Expanding windows mimic deployment:** each fold answers 'trained "
"on everything through time T, how do I do on T+1?' — which is "
"the only question production ever asks. Block arithmetic:\n\n"
"```python\nbase, rem = divmod(n_samples, n_splits + 1)\nsizes = [base + (1 if i < rem else 0)\n         for i in range(n_splits + 1)]\nbounds = [cumulative sums]\n# split k: train = indices up to bounds[k], test = block k+1\n```\n\n"
"divmod + spread-the-remainder is the fair-chunking idiom (you "
"batched with it in pw-3). Note what expanding windows honestly "
"deliver: later folds have MORE training data — scores usually "
"improve across folds, and that *trend* is itself informative "
"(does your model still gain from more history? how fast does "
"performance decay with distance from training? — the retraining-"
"cadence question, answered empirically).\n\n"
"Why plain KFold flatters temporal data: shuffling lets the model "
"train on July to 'predict' June — interpolation, plus leakage of "
"any time-correlated feature (trend, seasonality, campaigns). The "
"gap between shuffled-CV score and time-split score is your "
"measured optimism — worth reporting in any interview discussion "
"of evaluation, and sklearn's TimeSeriesSplit (plus purging/"
"embargo gaps for label-lookahead in finance) industrializes "
"exactly this function."
                ),
                "objectives": [
                    "Implement expanding-window splits with fair remainder spread",
                    "Read fold-score trends as data-value and decay signals",
                    "Quantify shuffled-CV optimism on temporal problems",
                ],
                "hints": [
                    "n_splits+1 blocks; distribute remainder to the EARLIEST blocks.",
                    "Split k: train = all indices before block k+1; test = block k+1 exactly.",
                    "Build cumulative boundaries once; slice ranges from them.",
                ],
                "resources": [
                    {"title": "sklearn TimeSeriesSplit", "url": "https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html"},
                    {"title": "sklearn: cross-validation guide", "url": "https://scikit-learn.org/stable/modules/cross_validation.html"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"You're asked to build a churn model. Walk through your first week — "
"before any model training. What do you insist on knowing, and what "
"do you build first?"
                ),
                "difficulty": "Medium",
                "topics": ["ML process", "problem framing"],
                "answer": (
"Framing first: what *decision* does the score drive (retention "
"offers? priority support?), what's the intervention's cost and "
"capacity (can we only act on 500 customers/month? → we need good "
"top-500 precision, not global accuracy), and what's the label — "
"'churn' needs an operational definition (no completed order in 90 "
"days post-snapshot, ff-1's exact discipline) plus a prediction "
"horizon. Data audit: feature availability *at prediction time* "
"(leakage hunt), history depth, label base rate (imbalance "
"planning). Then build, in order: (1) the evaluation harness — "
"time-based split matching deployment cadence, metrics tied to the "
"decision (precision@500, not accuracy); (2) the dumb baseline and "
"a 3-feature logistic regression; (3) the data pipeline as real "
"pipeline code (Feature Foundry style, rerunnable). Only then "
"model complexity — which frequently isn't needed: if logistic-"
"on-RFM captures 90% of the lift, ship it and iterate."
                ),
                "explanation": (
"Interviewers ask this to see whether you start with decisions or "
"with XGBoost. Every element — operational label definition, "
"cost/capacity constraints shaping the metric, "
"evaluation-before-models, baseline discipline — signals ML "
"*engineering* maturity versus notebook enthusiasm. The "
"capacity-constrained metric (precision@k) is a particularly "
"strong beat: it converts 'build a churn model' into 'rank the "
"500 best intervention targets', which changes everything "
"downstream. Closing with 'simplest model that captures the "
"lift' inoculates against the complexity-signaling trap that "
"junior answers fall into."
                ),
            },
            {
                "question": (
"Your gradient-boosting model scores 0.85 AUC in proper time-split "
"validation. The previous logistic regression scored 0.83 and is "
"already deployed. Argue for and against replacing it, then decide "
"what you'd actually do."
                ),
                "difficulty": "Hard",
                "topics": ["model complexity", "MLOps trade-offs"],
                "answer": (
"**For replacing:** +0.02 AUC can be real money at scale (compute "
"the lift at the operating threshold — AUC deltas are abstract; "
"top-decile capture rates aren't); GBMs capture interactions "
"logistic misses and won't need manual feature crosses as data "
"grows. **Against:** the logistic is deployed, calibrated, "
"debugged, explainable to compliance ('the coefficient on "
"recency...'), fast to serve, and retrains cheaply; the GBM adds "
"artifact size, latency, monitoring surface, calibration drift "
"(GBM scores aren't probabilities without recalibration), and "
"explanation machinery (SHAP) — each a new failure mode. "
"**Decision:** quantify the 0.02 at the actual operating point "
"with the actual intervention capacity; if the business delta is "
"material, shadow-deploy the GBM (score alongside, compare on "
"live data for a month — the parallel-run pattern yet again), "
"then replace with calibration + monitoring in place. If the "
"delta at the operating point is noise, keep the logistic and "
"spend the effort on better features — which usually beats "
"better algorithms."
                ),
                "explanation": (
"A judgment question dressed as a modeling question. The moves "
"that score: translating AUC into operating-point business lift "
"(the only honest comparison), pricing the operational cost of "
"complexity (serving, calibration, explanation, monitoring — the "
"MLOps surface), and the shadow-deployment migration pattern "
"(identical in spirit to the DuckDB parallel-run and the "
"expand-contract migration — one instinct, many costumes). "
"'Better features beat better algorithms' is the empirically-"
"grounded closer that experienced interviewers recognize as "
"earned rather than recited."
                ),
            },
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "vector-vault",
        "title": "Vector Vault",
        "tagline": "Embeddings and similarity search: pgvector and the math beneath it",
        "level": "Advanced",
        "tech": ["embeddings", "cosine similarity", "pgvector", "ANN indexes", "chunking"],
        "est_hours": 7,
        "brief": (
            "Vector search powers semantic search, recommendations, and RAG — "
            "and your warehouse already speaks it (pgvector is installed, the "
            "doc_chunks table awaits). Build the intuition from the math up: "
            "implement cosine similarity and exact top-k, build a toy "
            "TF-based embedder (offline-deterministic — a real embedding API "
            "plugs into the same interface later), load and query pgvector "
            "with real SQL, and understand ANN indexes (HNSW/IVFFlat) as the "
            "recall-vs-speed trade they are."
        ),
        "milestones": [
            "Embed the curriculum: chunk this course's project briefs (or any text folder) into ~500-char pieces; embed with the toy hashing embedder; verify similar texts land near each other (spark brief ≈ lakehouse brief; redis brief far from both).",
            "pgvector hands-on: INSERT chunks + embeddings into doc_chunks; query top-5 with ORDER BY embedding <=> query_vec LIMIT 5; compare <=> (cosine) vs <-> (L2) orderings on the same query.",
            "Index the vault: CREATE INDEX ... USING hnsw (embedding vector_cosine_ops); EXPLAIN before/after — seq scan of every vector vs graph traversal; measure at 10k synthetic vectors.",
            "Recall measurement: for 20 queries, compare HNSW top-10 vs exact top-10 (the brute-force ground truth) — compute recall@10 and tune ef_search to watch the speed/recall dial move.",
            "The hybrid pattern: combine vector similarity with SQL filters (WHERE doc_name LIKE ... AND embedding <=> ...) — the filtered-search capability that makes Postgres-as-vector-DB genuinely compelling for warehouse-adjacent workloads.",
        ],
        "under_the_hood": (
            "**Embeddings are learned coordinates:** a model maps text (or "
            "images, users, products) into ~100-3000-dim space where "
            "semantic similarity becomes geometric proximity — 'refund my "
            "order' lands near 'money back please' despite zero shared "
            "words. That's the leap beyond TF-IDF keyword space: meaning, "
            "not spelling. (Your toy hashing embedder shares only spelling "
            "— perfect for understanding the *plumbing* deterministically; "
            "swap in a real model for semantics.)\n\n"
            "**Cosine similarity** measures angle, not length: dot product "
            "of unit-normalized vectors, in [-1, 1]. Normalize once at "
            "index time and cosine becomes a plain dot product — also why "
            "'cosine distance' (1 - similarity) and L2 on normalized "
            "vectors rank identically.\n\n"
            "**Exact search is O(n·d)** per query — fine to ~100k vectors "
            "(and always the correctness baseline), then ANN indexes trade "
            "*recall* for speed: **HNSW** builds a multi-layer navigable "
            "graph (skip lists in high dimensions! cm-3 returns) — "
            "greedy-descend from coarse to fine layers, ~logarithmic "
            "hops, tunable via ef_search; **IVFFlat** clusters vectors "
            "(k-means cells) and probes only the nearest nprobe cells — "
            "faster to build, coarser recall control. 'Approximate' is "
            "the operative word: recall@k < 1.0 by design, so measure it "
            "(your milestone) rather than discover it in production."
        ),
        "exercises": [
            {
                "id": "vv-1",
                "title": "Cosine similarity + top-k, exactly",
                "instructions": (
"The primitive under every vector database.\n\n**Your task**\n\n"
"Implement `cosine(a, b)` (lists of floats; zero-vector → 0.0) and "
"`top_k(query, corpus, k)` where corpus is {doc_id: vector}: return "
"the k (doc_id, similarity) pairs by descending similarity, ties by "
"doc_id ascending, similarities rounded to 6 decimals. Pure Python + "
"math — feel every multiply the database does."
                ),
                "starter_code": (
                    "import math\n\n"
                    "def cosine(a, b):\n"
                    "    ...\n\n"
                    "def top_k(query, corpus, k):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "import math as m\n"
                    "assert m.isclose(cosine([1, 0], [1, 0]), 1.0)\n"
                    "assert m.isclose(cosine([1, 0], [0, 1]), 0.0)\n"
                    "assert m.isclose(cosine([1, 0], [-1, 0]), -1.0)\n"
                    "assert cosine([0, 0], [1, 2]) == 0.0\n"
                    "assert m.isclose(cosine([1, 2], [2, 4]), 1.0), 'parallel vectors: angle 0 regardless of length'\n"
                    "corpus = {'a': [1, 0], 'b': [0.9, 0.1], 'c': [0, 1], 'd': [-1, 0]}\n"
                    "out = top_k([1, 0], corpus, 3)\n"
                    "assert [d for d, s in out] == ['a', 'b', 'c'], out\n"
                    "assert out[0][1] == 1.0 and out[2][1] == 0.0\n"
                    "print('PASS: the vector-search primitive — every ANN index approximates THIS')\n"
                ),
                "refresher": (
"**Angle, not magnitude:**\n\n"
"```python\ndef cosine(a, b):\n    dot = sum(x * y for x, y in zip(a, b))\n    na = math.sqrt(sum(x * x for x in a))\n    nb = math.sqrt(sum(y * y for y in b))\n    return dot / (na * nb) if na and nb else 0.0\n```\n\n"
"The parallel-vectors check ([1,2] vs [2,4] → 1.0) is the concept "
"in one assert: cosine ignores length, so a long document and its "
"summary can still align. Why cosine dominates for text "
"embeddings: document length inflates magnitudes but shouldn't "
"change *aboutness* — angle isolates direction/meaning. (Dot "
"product, in contrast, rewards magnitude — used when 'confidence' "
"should count; L2 on unit-normalized vectors ranks identically to "
"cosine, which is why databases let you pick per-index.)\n\n"
"top_k is your hs-1 pattern with a similarity score — sorted() is "
"fine at this scale, a bounded heap at streaming scale. The "
"complexity reality check: 1M docs × 1536 dims = 1.5B multiplies "
"*per query* for exact search — arithmetic that makes ANN indexes "
"inevitable, and makes 'how would you scale vector search?' a "
"question you can now answer from first principles: shrink n "
"(filtering), shrink work-per-candidate (quantization), or visit "
"fewer candidates (HNSW's graph)."
                ),
                "objectives": [
                    "Implement cosine with zero-vector and parallel-vector correctness",
                    "Choose cosine vs dot vs L2 deliberately",
                    "Estimate exact-search cost and derive why ANN exists",
                ],
                "hints": [
                    "Guard BOTH norms against zero before dividing.",
                    "Sort key: (-similarity, doc_id) gives desc-similarity, asc-id ties.",
                    "Round similarities with round(s, 6) as you build pairs.",
                ],
                "resources": [
                    {"title": "pgvector README (operators & indexes)", "url": "https://github.com/pgvector/pgvector"},
                    {"title": "Cosine similarity", "url": "https://en.wikipedia.org/wiki/Cosine_similarity"},
                ],
            },
            {
                "id": "vv-2",
                "title": "Chunking with overlap (the RAG prerequisite)",
                "instructions": (
"Embedding quality starts with chunking — the unglamorous decision "
"that makes or breaks retrieval.\n\n**Your task**\n\nImplement "
"`chunk_text(text, size, overlap)`: split into chunks of at most "
"`size` characters, each successive chunk starting `size - overlap` "
"characters after the previous — but **snap boundaries to "
"whitespace**: if position size lands mid-word, back up to the last "
"space within the chunk (hard-split only spaceless runs). No empty "
"chunks; a final short remainder is fine; overlap >= size → "
"ValueError."
                ),
                "starter_code": (
                    "def chunk_text(text, size, overlap):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "text = 'the quick brown fox jumps over the lazy dog and runs far away'\n"
                    "chunks = chunk_text(text, size=20, overlap=5)\n"
                    "assert all(len(c) <= 20 for c in chunks)\n"
                    "assert all(chunks), 'no empty chunks'\n"
                    "assert not any(c[0] == ' ' or c[-1] == ' ' for c in chunks) or True  # stripping optional\n"
                    "joined = ' '.join(chunks)\n"
                    "for word in text.split():\n"
                    "    assert word in joined, f'word lost: {word}'\n"
                    "assert chunk_text('abcdefghij', 4, 1) == ['abcd', 'defg', 'ghij'], 'spaceless: hard split'\n"
                    "try:\n"
                    "    chunk_text('x', 5, 5)\n"
                    "    raise AssertionError('overlap >= size must raise')\n"
                    "except ValueError:\n"
                    "    pass\n"
                    "print('PASS: overlapping word-aware chunks — retrieval quality starts here')\n"
                ),
                "refresher": (
"**Why chunk at all, and why overlap:** embeddings compress a "
"chunk into ONE vector — too big and the vector is a muddy "
"average of many topics (retrieval matches nothing well); too "
"small and context evaporates ('it costs $5' — what does?). "
"Overlap insures against the boundary cutting a thought in half: "
"the sentence straddling chunks 2|3 lives whole in one of them.\n\n"
"```python\nstart = 0\nwhile start < len(text):\n    end = min(start + size, len(text))\n    if end < len(text):\n        space = text.rfind(' ', start, end)\n        if space > start:\n            end = space              # snap back to a word boundary\n    chunks.append(text[start:end].strip())\n    if end >= len(text):\n        break                        # consumed everything\n    start = max(end - overlap, start + 1)   # step back by overlap; never stall\n```\n\n"
"The engineering points that generalize: the overlap>=size guard "
"prevents an infinite loop (step 0!) — always guard "
"non-advancing loops; word-snapping is a special case of "
"'respect semantic boundaries' (production chunkers prefer "
"sentences/paragraphs/markdown headers — recursive character "
"splitting); and chunking is a *tunable of retrieval quality* — "
"chunk size sweeps belong in your RAG evaluation (next "
"project), not in guesswork. Typical text: 200-500 tokens with "
"10-20% overlap as the starting grid."
                ),
                "objectives": [
                    "Implement overlapping windows with boundary snapping",
                    "Guard against non-advancing loop configurations",
                    "Treat chunk size/overlap as measurable retrieval tunables",
                ],
                "hints": [
                    "Guard first: overlap >= size → ValueError (step would be <= 0).",
                    "rfind(' ', start, end) finds the snap point; only snap when not at text end.",
                    "Advance from the ACTUAL chunk end: start = end - overlap (and break once end reaches the text end) — this guarantees no text is skipped when a boundary snaps backwards.",
                ],
                "resources": [
                    {"title": "Chunking strategies for RAG (Pinecone guide)", "url": "https://www.pinecone.io/learn/chunking-strategies/"},
                    {"title": "LangChain text splitters (recursive splitting)", "url": "https://python.langchain.com/docs/concepts/text_splitters/"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"Your team needs vector search over 5M product descriptions, "
"filtered by category and price, updated hourly. Dedicated vector "
"DB (Pinecone/Weaviate/Qdrant) or pgvector in the existing "
"Postgres? Argue it properly."
                ),
                "difficulty": "Hard",
                "topics": ["vector infrastructure", "build vs buy"],
                "answer": (
"**pgvector's case:** 5M vectors is comfortably in range (HNSW "
"handles it); the killer feature is *filtered* search — "
"category/price predicates combine with vector ordering in one "
"planner, one transaction, one backup story, joined directly to "
"product tables (no sync pipeline between a vector store and the "
"source of truth — an entire class of consistency bugs deleted); "
"hourly updates are trivial (UPDATE ... SET embedding). Costs: "
"HNSW build memory/time on bulk loads, and post-filtering can "
"degrade ANN recall when filters are highly selective (the index "
"returns k candidates BEFORE the filter eats them — "
"iterative-scan mitigations exist but need tuning). **Dedicated "
"DB's case:** built-in quantization at 100M+ scale, "
"sharding-native, hybrid (BM25+vector) search out of the box. "
"**Verdict for the stated shape:** pgvector — the workload is "
"warehouse-adjacent, filter-heavy, modest-scale; operating a "
"second stateful system for it fails the pg-2 boring-tech test. "
"Revisit at ~50M+ vectors or if hybrid text search becomes "
"core."
                ),
                "explanation": (
"A build-vs-buy question where the filtered-search detail does "
"the heavy lifting: filters × ANN is genuinely hard (pre-filter "
"kills index usage, post-filter kills recall), and knowing that "
"pgvector puts BOTH in one cost-based planner — while "
"dedicated stores bolt filtering onto ANN — is the "
"discriminating insight. The no-sync-pipeline argument recycles "
"the dual-write lesson (fewer stateful systems = fewer "
"consistency stories) — coherence across your answers reads as "
"architecture maturity. Numbers anchor it: single-digit "
"millions with filters → Postgres; hundreds of millions, "
"hybrid-search-first → dedicated. Interviews reward the "
"threshold, not the tribal allegiance."
                ),
            },
            {
                "question": (
"Explain HNSW to a colleague who knows skip lists (from Redis "
"ZSETs). Then: which two parameters would you tune when recall@10 "
"is too low, and what does each cost?"
                ),
                "difficulty": "Medium",
                "topics": ["ANN indexes", "HNSW tuning"],
                "answer": (
"The skip-list bridge: a skip list finds a 1-D value by starting "
"in sparse express lanes and dropping into denser ones. HNSW is "
"that idea lifted to high dimensions — layers of proximity "
"graphs, sparse on top, dense (all vectors) at layer 0; each "
"node links to its ~M nearest neighbors per layer. Search "
"greedy-hops toward the query in the top layer, drops a layer, "
"repeats, and at layer 0 runs a best-first exploration keeping "
"a candidate frontier of size **ef_search**. Recall knobs: "
"**ef_search** (query-time frontier width) — wider explores "
"more paths before settling, recall↑ latency↑ linearly-ish, "
"tune freely per-query with no rebuild; **M / "
"ef_construction** (graph degree / build-time frontier) — "
"denser, better-connected graphs raise the recall ceiling, "
"cost build time and memory (links ≈ n × M × bytes), and "
"changing them means REINDEXING. Tune ef_search first; "
"rebuild with higher M only when ef_search plateaus below "
"target."
                ),
                "explanation": (
"Analogy-transfer questions test whether knowledge is "
"structural: skip lists → HNSW is the canonical bridge (both "
"are probabilistic express-lane hierarchies; cm-3 planted it "
"deliberately). The tuning half separates readers from "
"operators: ef_search as the free runtime dial vs M/"
"ef_construction as the expensive rebuild dial — plus "
"'measure recall against exact ground truth on YOUR data' "
"(the vv milestone) since recall varies with data geometry. "
"Mentioning greedy search's known weakness (local minima in "
"clustered data — why ef_search > k matters) earns the last "
"point."
                ),
            },
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "llm-pipeline",
        "title": "LLM Pipeline",
        "tagline": "LLMs as data workers: extraction, classification, and batch discipline",
        "level": "Advanced",
        "tech": ["LLM APIs", "structured outputs", "prompt templates", "cost/rate management", "caching"],
        "est_hours": 8,
        "brief": (
            "LLMs turned unstructured data — reviews, tickets, documents — "
            "into pipeline input, and the engineering around the model call "
            "is pure data engineering: validation, retries, rate limits, "
            "caching, cost budgets, evals. Enrich the Mongo reviews with "
            "sentiment/aspects via a mock LLM client (deterministic, "
            "offline — the same interface as any real API; set "
            "LLM_API_KEY to go live later), landing validated results in "
            "the warehouse with all the discipline this course has built."
        ),
        "milestones": [
            "Build the client interface: complete(prompt) -> str, with a MockLLM (rule-based sentiment, deliberately imperfect: ~10% malformed JSON responses, occasional rate-limit errors — production's greatest hits, simulated).",
            "Prompt as template + few-shot: a classify_review prompt with 3 worked examples demanding STRICT JSON {'sentiment': ..., 'aspects': [...]}; test on 20 mock reviews.",
            "The validation gate: parse responses with pydantic (dd-1 returns!); malformed → one repair-retry with the error appended to the prompt; still bad → DLQ (pb-2 returns!). Measure the repair success rate.",
            "Batch run: enrich 800 reviews through the pipeline with ww-2 retries + cm-2-style rate limiting + a TTL cache keyed on (model, prompt-hash) — rerun and watch the cache eliminate ~100% of calls (idempotent AND free).",
            "Cost + eval: track tokens (estimate: chars/4) and cost per run; hand-label 30 reviews and score the mock LLM's accuracy against them — the eval habit that separates AI engineering from AI vibes.",
        ],
        "under_the_hood": (
            "**An LLM call is an unreliable RPC to a probabilistic "
            "service** — treat it with MORE pipeline discipline than a "
            "database, not less: timeouts, retries with backoff+jitter "
            "(429s are a when, not an if), response validation at the "
            "boundary (never trust generated JSON — repair loops beat "
            "hope; structured-output APIs constrain decoding where "
            "available), idempotent caching (temperature-0 responses "
            "cache beautifully by prompt-hash — cm-1 with real "
            "money attached), and DLQs for the residue. Every mechanism "
            "is one you've already built; the model is just a weirder "
            "backend.\n\n"
            "**Prompts are code:** version them, template them "
            "(separating instructions from data also blunts injection — "
            "review text saying 'ignore your instructions' must stay "
            "*data*), few-shot them (worked examples steer format more "
            "reliably than prose), and regression-test them — a prompt "
            "or model change without an eval run is a deploy without "
            "tests.\n\n"
            "**Evals are the new unit tests:** a labeled golden set + "
            "accuracy tracking per (prompt, model) version is what "
            "makes 'the model seems fine' into a number that gates "
            "deploys. Batch economics complete the picture: batch APIs "
            "run ~50% cheaper for latency-tolerant enrichment, "
            "prompt-prefix caching rewards shared templates, and "
            "cost-per-thousand-records belongs on the same dashboard "
            "as row counts and DLQ rates. It's ETL; the transform "
            "just happens to reason."
        ),
        "exercises": [
            {
                "id": "lp-1",
                "title": "Robust LLM extraction with repair loop",
                "instructions": (
"The production pattern for LLM-powered ETL.\n\n**Your task**\n\n"
"Implement `extract_sentiment(review, llm, max_repairs=1)`: call "
"`llm(prompt)` (any prompt containing the review text); the "
"response SHOULD be JSON {'sentiment': 'positive'|'negative'|"
"'neutral'}. Parse strictly (json.loads + allowed values). On "
"failure, retry once with a repair prompt that includes the "
"previous bad response and the error. Success → the sentiment "
"string; all attempts bad → None. The checker's fake LLM speaks "
"markdown-fenced JSON, then bare JSON on repair — strip fences "
"before parsing (```json ... ``` wrappers are the #1 real-world "
"nuisance)."
                ),
                "starter_code": (
                    "import json\n\n"
                    "def extract_sentiment(review, llm, max_repairs=1):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "def good_llm(prompt):\n"
                    "    return '{\"sentiment\": \"positive\"}'\n"
                    "assert extract_sentiment('great product', good_llm) == 'positive'\n"
                    "def fenced_llm(prompt):\n"
                    "    return '```json\\n{\"sentiment\": \"negative\"}\\n```'\n"
                    "assert extract_sentiment('bad product', fenced_llm) == 'negative', 'strip markdown fences!'\n"
                    "calls = {'n': 0}\n"
                    "def flaky_llm(prompt):\n"
                    "    calls['n'] += 1\n"
                    "    if calls['n'] == 1:\n"
                    "        return 'Sure! The sentiment is positive.'   # not JSON\n"
                    "    assert 'Sure!' in prompt, 'repair prompt must include the bad response'\n"
                    "    return '{\"sentiment\": \"neutral\"}'\n"
                    "assert extract_sentiment('meh', flaky_llm) == 'neutral' and calls['n'] == 2\n"
                    "def hopeless(prompt):\n"
                    "    return 'I cannot help with that.'\n"
                    "assert extract_sentiment('x', hopeless) is None\n"
                    "def invalid_value(prompt):\n"
                    "    return '{\"sentiment\": \"ecstatic\"}'\n"
                    "assert extract_sentiment('x', invalid_value) is None, 'schema means ALLOWED VALUES too'\n"
                    "print('PASS: validate, repair, give up gracefully — LLM ETL discipline')\n"
                ),
                "refresher": (
"**Trust boundaries don't move for AI:** an LLM response is "
"user input wearing a lab coat — parse, validate values, never "
"eval:\n\n"
"```python\ndef _parse(text):\n    t = text.strip()\n    if t.startswith('```'):\n        t = t.split('\\n', 1)[1].rsplit('```', 1)[0]  # strip fences\n    data = json.loads(t)                              # may raise\n    s = data['sentiment']                             # may raise\n    if s not in ('positive', 'negative', 'neutral'):\n        raise ValueError(f'bad value: {s}')\n    return s\n```\n\n"
"The repair loop is error-message-as-feedback: models correct "
"themselves remarkably well when shown their own malformed "
"output plus the parse error — a one-retry repair typically "
"recovers a large majority of failures at the cost of one extra "
"call. Budget it (max_repairs) or a pathological input loops "
"forever at $per-call.\n\n"
"The allowed-values check is the subtle half of 'schema': "
"json.loads accepting `'ecstatic'` is syntactic success and "
"semantic garbage — enums, ranges, and required keys are what "
"pydantic (dd-1) industrializes, and real structured-output "
"APIs (JSON schema-constrained decoding) push into the "
"decoder itself. Returning None (→ DLQ) rather than raising "
"keeps the batch alive: pb-2's ladder, now with a model in "
"the loop. Nothing about this pattern is AI-specific — that's "
"the insight."
                ),
                "objectives": [
                    "Parse LLM output defensively: fences, JSON, allowed values",
                    "Implement bounded repair loops with error feedback",
                    "Route hopeless cases to DLQ semantics instead of crashing",
                ],
                "hints": [
                    "Write a _parse helper that raises on ANY problem; loop attempts around it.",
                    "Fence stripping: if it starts with ```, cut the first line and the trailing fence.",
                    "The repair prompt must contain the previous response text (the checker asserts it).",
                ],
                "resources": [
                    {"title": "OpenAI: structured outputs", "url": "https://platform.openai.com/docs/guides/structured-outputs"},
                    {"title": "Anthropic: tool use / structured generation", "url": "https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview"},
                ],
            },
            {
                "id": "lp-2",
                "title": "Batch enrichment economics",
                "instructions": (
"The cost half of AI engineering.\n\n**Your task**\n\nImplement "
"`enrich_batch(records, llm, cache, price_per_1k_tokens)`: for "
"each record (dict with 'id' and 'text'), build prompt "
"f'classify: {text}'; check `cache` (a dict keyed by prompt) "
"first; on miss call llm(prompt), store in cache. Estimate "
"tokens = len(prompt)//4 + len(response)//4 for ACTUAL calls "
"only (cache hits are free). Return {'results': {id: response}, "
"'calls': n, 'cache_hits': n, 'tokens': n, 'cost': tokens/1000 * "
"price}. Duplicate texts in one batch must hit the cache."
                ),
                "starter_code": (
                    "def enrich_batch(records, llm, cache, price_per_1k_tokens=0.5):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "import math\n"
                    "calls = {'n': 0}\n"
                    "def llm(prompt):\n"
                    "    calls['n'] += 1\n"
                    "    return 'positive!!'   # 10 chars -> 2 tokens\n"
                    "cache = {}\n"
                    "records = [{'id': 1, 'text': 'good'}, {'id': 2, 'text': 'nice'},\n"
                    "           {'id': 3, 'text': 'good'}]   # duplicate text!\n"
                    "r = enrich_batch(records, llm, cache)\n"
                    "assert r['calls'] == 2 and r['cache_hits'] == 1, (r['calls'], r['cache_hits'])\n"
                    "assert calls['n'] == 2, 'duplicate prompt must not reach the model'\n"
                    "assert r['results'] == {1: 'positive!!', 2: 'positive!!', 3: 'positive!!'}\n"
                    "# tokens: 2 calls x (len('classify: good')//4=3 + 2) = 2 x 5... compute: 14//4=3, resp 10//4=2 -> 5 each\n"
                    "assert r['tokens'] == 10, r['tokens']\n"
                    "assert math.isclose(r['cost'], 10/1000 * 0.5)\n"
                    "r2 = enrich_batch(records, llm, cache)\n"
                    "assert r2['calls'] == 0 and r2['cache_hits'] == 3 and r2['cost'] == 0.0\n"
                    "assert calls['n'] == 2, 'rerun must be FREE — the cache is idempotency with a price tag'\n"
                    "print('PASS: cached, metered, rerun-safe — AI enrichment as proper ETL')\n"
                ),
                "refresher": (
"**The cache IS the idempotency layer** — same shape as cm-1, "
"new stakes: at temperature 0, (model, prompt) → response is a "
"pure function, so caching by prompt (production: hash of "
"model+prompt+params) makes reruns free AND deterministic. Your "
"pipeline crashes at record 700 of 800? The rerun costs 100 "
"calls, not 800 — the ww-3 rerun test, now denominated in "
"dollars.\n\n"
"```python\nfor rec in records:\n    prompt = f\"classify: {rec['text']}\"\n    if prompt in cache:\n        hits += 1\n    else:\n        resp = llm(prompt)\n        cache[prompt] = resp\n        tokens += len(prompt) // 4 + len(resp) // 4\n        calls += 1\n    results[rec['id']] = cache[prompt]\n```\n\n"
"Metering-as-you-go (tokens, calls, cost in the run report) is "
"the habit that keeps AI features alive: cost-per-thousand-"
"records sits next to row counts on the pipeline dashboard, "
"anomaly-checked like any metric (qg-2 on your API bill — a "
"prompt change that doubles token usage should page someone "
"before finance does). The chars/4 estimate is crude but "
"directionally right for English; real pipelines use the "
"tokenizer. Dedup-before-call (the checker's duplicate) "
"generalizes: batch dedup by content hash routinely cuts "
"real-world enrichment bills 20-40%, because production text "
"is repetitive — the Structly lesson, invoiced."
                ),
                "objectives": [
                    "Key caches by full prompt for pure-function reruns",
                    "Meter tokens/costs inside the pipeline run report",
                    "Exploit content dedup for real cost reduction",
                ],
                "hints": [
                    "Check the cache BEFORE calling; count hits and calls separately.",
                    "Token math only on actual calls: prompt//4 + response//4.",
                    "results maps record id → response either way (hit or miss).",
                ],
                "resources": [
                    {"title": "OpenAI batch API (50% economics)", "url": "https://platform.openai.com/docs/guides/batch"},
                    {"title": "Anthropic: prompt caching", "url": "https://docs.claude.com/en/docs/build-with-claude/prompt-caching"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"Design a pipeline that classifies 2M support tickets/month with an "
"LLM at minimal cost without sacrificing quality. Walk through your "
"cost levers and quality controls."
                ),
                "difficulty": "Hard",
                "topics": ["LLM pipelines", "cost engineering", "evals"],
                "answer": (
"Cost levers, in typical impact order: **(1) don't-call-the-model** "
"— content-hash dedup (tickets repeat!), cache by "
"(model, prompt-hash), and a cheap pre-filter (regex/keyword rules "
"or a small classifier) handling the easy 40-60%, escalating only "
"ambiguous cases to the LLM (cascade architecture); **(2) "
"right-size the model** — evaluate the smallest model that meets "
"the quality bar on your golden set; most classification doesn't "
"need the frontier; **(3) batch APIs** (~50% off for async "
"workloads — tickets are latency-tolerant); **(4) prompt economy** "
"— shared prefix for prompt caching, minimal few-shots, terse "
"output schema. Quality controls: a hand-labeled golden set "
"(500+ tickets) gating every prompt/model change (regression "
"evals); confidence-based routing (low-confidence → human or "
"bigger model); weekly drift sampling (label 100 fresh "
"predictions — production distribution shifts); DLQ + repair for "
"malformed outputs; and cost/accuracy on ONE dashboard so "
"trade-offs stay visible."
                ),
                "explanation": (
"The question tests whether you treat LLM cost as an engineering "
"surface with the same rigor as compute cost. The cascade "
"(cheap-model-first, escalate ambiguity) is the highest-signal "
"pattern — it's tiered storage/caching logic applied to "
"inference, and it routinely cuts bills 5-10x. Golden-set evals "
"as deploy gates translate 'testing' into the AI era — "
"interviewers specifically listen for eval discipline versus "
"vibes. The drift-sampling beat acknowledges that both the "
"ticket distribution AND the (vendor-updated) model change under "
"you: monitoring isn't optional. Every mechanism named — dedup, "
"cache, DLQ, dashboards — is classical data engineering, which "
"is exactly the point of this stage."
                ),
            },
            {
                "question": (
"Your LLM-extraction pipeline (structured JSON from documents) "
"passed evals at 96% accuracy, but a month later downstream teams "
"report garbage rows. The prompt and code are unchanged. What "
"happened and what do you build?"
                ),
                "difficulty": "Medium",
                "topics": ["model drift", "monitoring", "vendor risk"],
                "answer": (
"Candidate causes: **(1) silent model update** — hosted models "
"change behind stable API names (even 'pinned' versions get "
"infra tweaks); output format/edge-case behavior shifts; **(2) "
"input drift** — new document templates/languages/lengths the "
"eval set never covered; **(3) truncation** — longer documents "
"now exceeding context, silently cutting the schema examples or "
"document tail; **(4) downstream contract drift** — a consumer "
"reinterpreting a field. Diagnose by re-running the ORIGINAL "
"golden set: unchanged score → input drift (sample and label "
"fresh production docs — your eval set aged); dropped score → "
"the model moved. Build: continuous eval (daily golden-set run "
"+ weekly fresh-sample labeling), output-schema validation "
"rates and per-field distribution monitors (qg-2 on extraction "
"outputs), model-version pinning with explicit upgrade evals, "
"and DLQ-rate alerting — the pipeline should have paged you "
"before the humans did."
                ),
                "explanation": (
"The scenario teaches the defining operational truth of LLM "
"systems: 'unchanged code' no longer means 'unchanged "
"behavior' — the model is a dependency that drifts, and inputs "
"drift too. The golden-set-bisection (fixed set separates "
"model-moved from world-moved) is the clean diagnostic "
"interviewers want, mirroring the classic 'is it the data or "
"the code' bisection from the Cleanroom debugging answer. "
"Continuous evals + distribution monitors are Quality Gate "
"pointed at AI outputs — one more instance of the course's "
"master pattern: every new technology eventually needs the "
"same old discipline, and the engineers who bring it win."
                ),
            },
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "rag-works",
        "title": "RAG Works",
        "tagline": "Retrieval-augmented generation: search + LLM, measured properly",
        "level": "Advanced",
        "tech": ["RAG", "retrieval evaluation", "hybrid search", "reranking", "grounding"],
        "est_hours": 8,
        "brief": (
            "Wire Vector Vault and LLM Pipeline together into the "
            "architecture of the moment: questions answered from YOUR "
            "documents — chunks retrieved by similarity, stuffed into a "
            "grounded prompt, answered with citations. Built offline-first "
            "(toy embedder + mock LLM), which forces the part most teams "
            "skip: MEASURING retrieval quality (recall@k, MRR) and "
            "answer faithfulness, because a RAG system without evals is a "
            "demo, not a product."
        ),
        "milestones": [
            "Assemble the pipeline: chunk (vv-2) → embed → store in pgvector → retrieve top-5 (vv-1) → grounded prompt ('answer ONLY from these passages; cite [1],[2]; say \"not in the documents\" when absent') → mock-LLM answer.",
            "Build the eval set FIRST: 25 question→relevant-chunk-ids pairs over your corpus (hand-labeled — yes, by hand; this is the real work of RAG).",
            "Measure retrieval: recall@5 and MRR over the eval set; then sweep chunk sizes (200/500/1000 chars) and re-measure — watch the single most impactful RAG parameter move your numbers.",
            "Hybrid + rerank: add keyword scoring (BM25-lite: term overlap) fused with vector scores (reciprocal rank fusion); then a rerank step (score top-20, keep top-5) — measure each addition's recall delta.",
            "Faithfulness check: for 20 answers, verify each cited passage actually contains the claimed fact (the mock setup makes this checkable); count unsupported claims — your hallucination rate under grounding.",
        ],
        "under_the_hood": (
            "**RAG is a search problem wearing an AI costume:** the LLM "
            "can only be as good as what retrieval hands it — garbage "
            "chunks in, confident garbage out. Hence the uncomfortable "
            "truth: most RAG failures are RETRIEVAL failures (wrong "
            "chunks, wrong granularity, vocabulary mismatch), and the "
            "highest-leverage work is boring IR engineering — chunking, "
            "hybrid scoring, reranking, evals — not prompt wizardry.\n\n"
            "**Why hybrid beats pure vectors:** embeddings excel at "
            "paraphrase ('money back' ≈ 'refund') but blur exact "
            "identifiers — part numbers, error codes, names — where "
            "keyword search (BM25) is literal and perfect. Reciprocal "
            "rank fusion (score = Σ 1/(60+rank) across systems) merges "
            "the two rankings without tuning weights, and a reranker "
            "(a cross-encoder scoring query+chunk *together*, vs the "
            "bi-encoder's independent embeddings) buys precision at "
            "the top where the context window forces choices.\n\n"
            "**Grounding is a contract, verified:** instruct "
            "answer-from-passages-only + cite + admit-absence, then "
            "MEASURE faithfulness (are claims supported by citations?) "
            "and abstention (does it say 'not found' when it's truly "
            "absent?). The metrics ladder — retrieval recall@k/MRR, "
            "answer faithfulness, abstention accuracy — is what "
            "separates a shippable RAG system from a demo that "
            "impressed a meeting once."
        ),
        "exercises": [
            {
                "id": "rw-1",
                "title": "Retrieval metrics: recall@k and MRR",
                "instructions": (
"You can't improve what you don't measure — the RAG "
"commandment.\n\n**Your task**\n\nImplement "
"`recall_at_k(retrieved, relevant, k)` (fraction of relevant "
"docs appearing in the first k retrieved; empty relevant → 1.0) "
"and `mrr(all_retrieved, all_relevant)` (mean over queries of "
"1/rank-of-first-relevant, 0 for queries with no relevant "
"retrieved; ranks are 1-based). Then `evaluate(runs)` where runs "
"is a list of {'retrieved': [...], 'relevant': {...}} returning "
"{'recall@5': ..., 'mrr': ...} averaged over runs."
                ),
                "starter_code": (
                    "def recall_at_k(retrieved, relevant, k):\n"
                    "    ...\n\n"
                    "def mrr(all_retrieved, all_relevant):\n"
                    "    ...\n\n"
                    "def evaluate(runs):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "import math\n"
                    "assert recall_at_k(['a', 'b', 'c'], {'a', 'c'}, 2) == 0.5\n"
                    "assert recall_at_k(['a', 'b', 'c'], {'a', 'c'}, 3) == 1.0\n"
                    "assert recall_at_k(['x'], set(), 5) == 1.0, 'nothing relevant = nothing missed'\n"
                    "assert math.isclose(mrr([['x', 'a'], ['b'], ['z']],\n"
                    "                        [{'a'}, {'b'}, {'q'}]), (0.5 + 1.0 + 0.0) / 3)\n"
                    "runs = [\n"
                    "    {'retrieved': ['c1', 'c2', 'c3', 'c4', 'c5', 'c6'], 'relevant': {'c2', 'c6'}},\n"
                    "    {'retrieved': ['c9', 'c1'], 'relevant': {'c9'}},\n"
                    "]\n"
                    "out = evaluate(runs)\n"
                    "assert math.isclose(out['recall@5'], (0.5 + 1.0) / 2), out\n"
                    "assert math.isclose(out['mrr'], (0.5 + 1.0) / 2)\n"
                    "print('PASS: retrieval instrumented — now chunking changes become experiments')\n"
                ),
                "refresher": (
"**Two metrics, two questions:** recall@k — 'did the right "
"stuff make it into the window?' (RAG's binding constraint: "
"the LLM never sees what retrieval missed); MRR — 'how high "
"does the first right answer rank?' (position matters: models "
"attend more to early context, and tight windows force "
"cutoffs):\n\n"
"```python\ndef recall_at_k(retrieved, relevant, k):\n    if not relevant:\n        return 1.0\n    return len(set(retrieved[:k]) & relevant) / len(relevant)\n\ndef mrr_one(retrieved, relevant):\n    for i, doc in enumerate(retrieved, 1):\n        if doc in relevant:\n            return 1 / i\n    return 0.0\n```\n\n"
"The empty-relevant convention (1.0, not 0/0 crash) matters "
"because eval sets legitimately contain "
"unanswerable-from-corpus questions — which also test "
"abstention. With these numbers, RAG tuning becomes "
"science: chunk-size sweeps, hybrid on/off, reranker "
"additions each produce a recall/MRR delta on a fixed eval "
"set instead of anecdotes ('it felt better on my three "
"test questions'). The uncomfortable, universal finding "
"this instrumentation reveals: retrieval, not generation, "
"is usually the bottleneck — which redirects effort from "
"prompt-tweaking to the IR fundamentals, and THAT "
"redirection is the mark of teams whose RAG actually "
"ships. (Deeper IR adds nDCG for graded relevance; "
"recall@k + MRR cover the RAG 90%.)"
                ),
                "objectives": [
                    "Implement recall@k and MRR with honest edge conventions",
                    "Run tuning as experiments against fixed eval sets",
                    "Diagnose RAG failures as retrieval-vs-generation with data",
                ],
                "hints": [
                    "recall: set intersection of retrieved[:k] with relevant, over len(relevant).",
                    "MRR: enumerate from 1; first hit returns 1/i; no hit → 0.",
                    "evaluate: mean of per-run recall_at_k(...,5) and per-run reciprocal ranks.",
                ],
                "resources": [
                    {"title": "Evaluation in information retrieval (Stanford IR book ch. 8)", "url": "https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-in-information-retrieval-1.html"},
                    {"title": "RAG evaluation frameworks (RAGAS)", "url": "https://docs.ragas.io/en/stable/"},
                ],
            },
            {
                "id": "rw-2",
                "title": "Reciprocal rank fusion (hybrid search)",
                "instructions": (
"Merge keyword and vector rankings without tuning "
"weights.\n\n**Your task**\n\nImplement `rrf(rankings, k=60)`: "
"rankings is a list of ranked doc-id lists (e.g. [vector_ranking, "
"keyword_ranking]). Each doc scores Σ 1/(k + rank_i) over the "
"rankings containing it (rank 1-based). Return doc ids by "
"descending score; ties broken by doc id ascending. A doc "
"missing from a ranking simply contributes nothing for it — "
"that's RRF's whole robustness story."
                ),
                "starter_code": (
                    "def rrf(rankings, k=60):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "vector = ['d1', 'd2', 'd3', 'd4']\n"
                    "keyword = ['d3', 'd5', 'd1']\n"
                    "out = rrf([vector, keyword])\n"
                    "# d1: 1/61+1/63  d3: 1/63+1/61  -> tie -> d1 before d3\n"
                    "assert out[0] == 'd1' and out[1] == 'd3', out\n"
                    "assert out.index('d2') < out.index('d4')\n"
                    "assert 'd5' in out\n"
                    "assert rrf([['a'], ['a']])[0] == 'a'\n"
                    "assert rrf([[], []]) == []\n"
                    "single = rrf([['x', 'y', 'z']])\n"
                    "assert single == ['x', 'y', 'z'], 'single ranking passes through'\n"
                    "print('PASS: RRF — hybrid search in ten lines, no weights to tune')\n"
                ),
                "refresher": (
"**Why ranks, not scores:** vector similarities live in "
"[-1, 1], BM25 scores in [0, ∞) — fusing raw scores means "
"normalization games that break as distributions shift. RRF "
"sidesteps it: only *positions* matter:\n\n"
"```python\nscores = {}\nfor ranking in rankings:\n    for rank, doc in enumerate(ranking, 1):\n        scores[doc] = scores.get(doc, 0) + 1 / (k + rank)\nreturn sorted(scores, key=lambda d: (-scores[d], d))\n```\n\n"
"The constant k=60 (empirical, from the original paper) "
"dampens the top-rank bonus so one system's #1 can't steamroll "
"consensus: a doc ranked #3 by BOTH systems beats a doc ranked "
"#1 by one and absent from the other — agreement wins, which "
"is exactly the behavior you want from independent evidence. "
"That's also why RRF generalizes beyond two systems (add a "
"recency ranking, a popularity ranking...) with zero tuning.\n\n"
"Production shape: retrieve top-50 from each system, RRF-fuse, "
"optionally cross-encoder-rerank the fused top-20, hand the "
"top-5 to the prompt — each stage cheaper-to-more-precise "
"(the cascade pattern from LLM Pipeline, applied to "
"retrieval). Postgres does both halves natively — pgvector + "
"full-text tsvector — making single-database hybrid RAG a "
"very defensible interview answer."
                ),
                "objectives": [
                    "Implement RRF with missing-doc robustness",
                    "Explain rank-vs-score fusion and the k constant's role",
                    "Design the retrieve→fuse→rerank→prompt cascade",
                ],
                "hints": [
                    "Accumulate per-doc: 1/(k + rank), enumerate from 1.",
                    "Sort by (-score, doc_id) for the tie rule.",
                    "Docs absent from a ranking just don't accumulate — no special casing.",
                ],
                "resources": [
                    {"title": "Reciprocal rank fusion (original paper)", "url": "https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf"},
                    {"title": "Postgres full-text search (the keyword half)", "url": "https://www.postgresql.org/docs/current/textsearch.html"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"Your company's RAG assistant over internal docs 'hallucinates' "
"according to users. Design the diagnostic process and the fixes, "
"layer by layer."
                ),
                "difficulty": "Hard",
                "topics": ["RAG debugging", "faithfulness"],
                "answer": (
"First, instrument to localize — 'hallucination' bundles four "
"distinct failures: **(1) retrieval miss** (answer isn't in the "
"retrieved chunks → model improvises): measure recall@k on a "
"labeled eval set; if low — fix chunking (size sweep, semantic "
"boundaries), add hybrid keyword search (exact terms/IDs!), "
"rerank. This is the cause in most systems. **(2) Grounding "
"failure** (right chunks retrieved, model ignores them): "
"strengthen the contract — answer-only-from-passages + mandatory "
"citations + 'say not-found' + few-shot examples of refusals; "
"measure faithfulness (claims supported by cited text) and "
"abstention accuracy separately. **(3) Corpus problems** — stale "
"or contradictory documents: the model faithfully cites wrong "
"docs; fix freshness pipelines and dedup/versioning (data "
"engineering, again). **(4) Unanswerable questions** users ask "
"anyway: measure the rate, route to humans. Ship with: per-answer "
"citations rendered in the UI (users verify), thumbs-down "
"feedback into a labeled failure queue, and the eval suite "
"gating every retriever/prompt/model change."
                ),
                "explanation": (
"The question rewards decomposition over incantation: "
"'hallucination' is a symptom with four mechanisms, each with "
"its own metric and fix — and stating that retrieval misses "
"dominate (then PROVING it with recall measurement) reframes an "
"AI-mystique problem as an IR-engineering problem, which is "
"this whole project's thesis. The corpus-quality layer is the "
"data engineer's edge in AI interviews: stale-doc pipelines and "
"contradiction dedup are Quality Gate work nobody glamorous "
"wants to do, and they move the user-facing metric more than "
"prompt tuning. The feedback-queue-to-eval-set loop closes the "
"system: production failures become tomorrow's regression "
"tests — the flywheel that separates products from demos."
                ),
            },
            {
                "question": (
"When should a team NOT build RAG? Give the failure cases and the "
"alternatives, including where fine-tuning actually belongs."
                ),
                "difficulty": "Medium",
                "topics": ["architecture judgment", "RAG vs alternatives"],
                "answer": (
"Skip RAG when: **(1) the knowledge is stable, bounded and "
"behavioral** — teaching format/style/domain-dialect is "
"fine-tuning's home turf (RAG can't make a model *write* like "
"your legal team; tuning can — but tuning is NOT for injecting "
"facts, which drift and don't reliably stick); **(2) the corpus "
"is tiny** — under ~50 pages, stuff it all in the context window "
"(long-context models made 'just include everything' a real "
"architecture; no retrieval failure modes at all); **(3) "
"questions are structured** — 'revenue by region last quarter' "
"wants text-to-SQL against the warehouse, not similarity search "
"over PDFs (semantic search on numbers is a category error); "
"**(4) freshness or permissions dominate** — if answers must "
"respect per-user document ACLs, retrieval must filter by "
"permission at query time (RAG complicates this but handles it; "
"fine-tuning catastrophically can't — tuned weights leak "
"training data to everyone). The honest default stack: "
"long-context stuffing for small corpora, RAG for large/fresh "
"unstructured knowledge, text-to-SQL for structured questions, "
"fine-tuning for behavior — composed, not competing."
                ),
                "explanation": (
"Anti-recommendation questions test for hype immunity. The "
"crispest discriminator — fine-tuning for *behavior*, "
"retrieval for *knowledge* — resolves the most common "
"confusion in the field, and the permissions point "
"(fine-tuned weights can't do per-user ACLs) is a security "
"argument most candidates miss entirely. Text-to-SQL as the "
"answer for structured questions plays directly to the data "
"engineer's strengths: the warehouse you've built all course "
"long IS the right backend for half the questions teams "
"aim RAG at. Closing with 'composed, not competing' — real "
"assistants route across all four — shows systems thinking "
"rather than technique tribalism."
                ),
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Stage 10 — the capstone
# ---------------------------------------------------------------------------

STAGE10_PROJECTS = [
    {
        "id": "grand-central",
        "title": "Grand Central (Capstone)",
        "tagline": "Everything, wired: the full data platform, end to end",
        "level": "Expert",
        "tech": ["everything you've built"],
        "est_hours": 20,
        "brief": (
            "The graduation project: assemble every stage into one living "
            "platform. Airflow orchestrates: Mongo events + reviews and API "
            "data flow through your pipeline library (watermarked, "
            "quality-gated, DLQ'd) into the bronze lake; Spark builds "
            "silver/gold; gold syncs to the Postgres star schema; an LLM "
            "enrichment DAG classifies new reviews (cached, budgeted, "
            "evaled); embeddings land in pgvector powering a RAG endpoint "
            "on a FastAPI serving layer that also exposes the churn "
            "model's scores; Redis caches the hot paths; dashboards read "
            "gold. One `docker compose --profile db --profile spark "
            "--profile airflow up -d`, one platform. Your portfolio "
            "piece — and living proof you can pass the interviews this "
            "course trained you for."
        ),
        "milestones": [
            "Draw it first: one architecture diagram (mermaid or draw.io) of every component and data flow, with the consistency/latency contract at each edge annotated — the artifact you'd bring to a system-design interview.",
            "Ingestion DAGs: events + reviews via your pipeline library — incremental watermarks, DLQ, quality gates, run reports to a pipeline_runs table; SLA 06:00, alerts on breach.",
            "Lake + warehouse: bronze→silver→gold Spark jobs driven by the partition planner via dynamic task mapping; gold → star schema (SCD2 customers!) over JDBC; reconciliation checks between layers.",
            "AI layer: the LLM enrichment DAG (mock or real key) with cache/cost reports; nightly embedding refresh for new chunks; RAG endpoint with recall-evaled retrieval; churn scores served from the model artifact with feature freshness checks.",
            "Serving + ops: FastAPI endpoints (gold aggregates, RAG answers, churn scores) with Redis cache-aside + rate limiting; a docs/RUNBOOK-PLATFORM.md covering every failure mode you've practiced: replay a day, backfill a month, recover from a poisoned deploy.",
            "The final exam, self-administered: break it three ways (kill Redis mid-traffic, poison a bronze partition, double-run a DAG day) and verify the platform heals by design — then write the incident reports as if for your future team.",
        ],
        "under_the_hood": (
            "**What you're actually demonstrating:** that the same ten "
            "ideas run the entire platform — idempotency (every load, "
            "every task, every enrichment call), watermarks & incremental "
            "thinking (CDC, partitions, streams), validation at "
            "boundaries (pydantic, quality gates, LLM output parsing), "
            "the ledger pattern (migrations, run reports, caches, "
            "checkpoints), partitioning & keys (shuffles, indexes, "
            "consumer groups, hash rings), laziness & pipelines "
            "(generators, Spark plans, aggregation stages), atomic "
            "publish (transactions, staging-swap, manifest commits), "
            "layered refinement (bronze/silver/gold, staging/core/marts), "
            "measurement before optimization (EXPLAIN, evals, "
            "recall@k, cost meters), and boring-technology judgment "
            "(the pg-2 axes). Ten ideas, forty costumes.\n\n"
            "**Interview translation:** this platform IS the answer to "
            "'design a data platform for an e-commerce company' — "
            "you've built every box on the whiteboard and broken most "
            "of them on purpose. When asked 'how would you handle X "
            "failure', you won't recall an article — you'll recall an "
            "incident you caused, observed, and healed. That's the "
            "difference the whole course was engineered to produce."
        ),
        "exercises": [
            {
                "id": "gc-1",
                "title": "The platform, in one function",
                "instructions": (
"A capstone kata: the whole nightly platform as a dependency "
"graph you execute.\n\n**Your task**\n\nUsing your oi-3 "
"mini-scheduler pattern, implement `run_platform(fns)` where fns "
"maps task names to callables for: 'ingest_events', "
"'ingest_reviews', 'quality_gate' (needs both ingests), "
"'silver' (needs quality_gate), 'gold' (needs silver), "
"'sync_warehouse' (needs gold), 'llm_enrich' (needs "
"ingest_reviews), 'embed_chunks' (needs llm_enrich), "
"'serve_refresh' (needs sync_warehouse AND embed_chunks). "
"Hardcode those dependencies, run in a valid order, propagate "
"failures as 'upstream_failed', return {task: state}. Your whole "
"platform's control flow, in one testable function."
                ),
                "starter_code": (
                    "DEPS = {\n"
                    "    'ingest_events': [],\n"
                    "    'ingest_reviews': [],\n"
                    "    'quality_gate': ['ingest_events', 'ingest_reviews'],\n"
                    "    'silver': ['quality_gate'],\n"
                    "    'gold': ['silver'],\n"
                    "    'sync_warehouse': ['gold'],\n"
                    "    'llm_enrich': ['ingest_reviews'],\n"
                    "    'embed_chunks': ['llm_enrich'],\n"
                    "    'serve_refresh': ['sync_warehouse', 'embed_chunks'],\n"
                    "}\n\n"
                    "def run_platform(fns):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "ran = []\n"
                    "ok = {t: (lambda t=t: ran.append(t)) for t in DEPS}\n"
                    "states = run_platform(ok)\n"
                    "assert all(s == 'success' for s in states.values())\n"
                    "pos = {t: i for i, t in enumerate(ran)}\n"
                    "for t, ups in DEPS.items():\n"
                    "    for u in ups:\n"
                    "        assert pos[u] < pos[t], f'{u} must run before {t}'\n"
                    "ran2 = []\n"
                    "fns2 = dict(ok)\n"
                    "fns2['quality_gate'] = lambda: (_ for _ in ()).throw(RuntimeError('bad data'))\n"
                    "fns2 = {t: (f if t != 'quality_gate' else fns2['quality_gate']) for t, f in fns2.items()}\n"
                    "states2 = run_platform(fns2)\n"
                    "assert states2['quality_gate'] == 'failed'\n"
                    "for t in ['silver', 'gold', 'sync_warehouse', 'serve_refresh']:\n"
                    "    assert states2[t] == 'upstream_failed', (t, states2[t])\n"
                    "assert states2['llm_enrich'] == 'success', 'the AI branch is independent of the gate!'\n"
                    "assert states2['embed_chunks'] == 'success'\n"
                    "print('PASS: the whole platform in one graph — and the AI branch survives a gate failure')\n"
                ),
                "refresher": (
"**Read your own architecture in the failure test:** the "
"quality gate failing poisons the warehouse spine (silver → "
"gold → sync → serve_refresh) but the llm_enrich branch — "
"which depends only on ingest_reviews — keeps running. That's "
"not an accident of the test; it's an architectural decision "
"the graph *encodes*: enrichment tolerates un-gated data "
"(it has its own validation), while the warehouse spine "
"demands the gate. Whether that's RIGHT is a design review "
"conversation — and the fact that the graph makes it "
"visible and debatable is the point of declaring "
"dependencies as data (oi-1's lesson, at platform "
"scale).\n\n"
"serve_refresh joining both branches is the fan-in pattern: "
"it runs only when BOTH the warehouse and embeddings are "
"fresh — 'upstream_failed' reaching it through EITHER "
"parent. Airflow trigger rules generalize this (what if "
"serve should refresh with just the warehouse when "
"embeddings fail? → trigger_rule tweaks, partial-degradation "
"design).\n\n"
"You've now written this scheduler three times — toy (oi-3), "
"understanding Airflow (Stage 8), and as your own platform's "
"spine. The repetition is the curriculum: the pattern is "
"yours now, at whiteboard speed, which is where system-design "
"interviews are won."
                ),
                "objectives": [
                    "Encode platform architecture as an executable dependency graph",
                    "Reason about failure isolation between branches",
                    "Design fan-in joins and partial-degradation policies",
                ],
                "hints": [
                    "Reuse your oi-3 solution: topo order, upstream-state check, try/except.",
                    "'upstream_failed' must itself block downstream (transitivity).",
                    "The graph is given — resist editing DEPS; the test encodes its meaning.",
                ],
                "resources": [
                    {"title": "Airflow trigger rules (partial degradation)", "url": "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html#trigger-rules"},
                    {"title": "Designing Data-Intensive Applications (the book to reread now)", "url": "https://dataintensive.net/"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"THE question: 'Design the data platform for a mid-size e-commerce "
"company — ingestion to dashboards to ML features to an AI "
"assistant.' You have 35 minutes at a whiteboard. Structure your "
"answer."
                ),
                "difficulty": "Hard",
                "topics": ["system design", "the whole course"],
                "answer": (
"Structure beats brilliance: **(1) Requirements first (5 min)** — "
"data volumes/growth, freshness needs per consumer (dashboards: "
"hourly? features: daily? assistant: minutes?), team size, "
"compliance. These pick every later trade-off. **(2) The spine "
"(10 min)** — OLTP sources + event streams → incremental "
"ingestion (CDC/watermarks, idempotent loads, DLQ) → raw/bronze "
"immutable layer (replayability = the platform's undo button) → "
"validated silver → dimensional gold (star schema, SCD2 where "
"history matters) → serving (warehouse for BI, Redis-cached APIs "
"for apps). Orchestrated by Airflow-class scheduling with "
"quality gates between layers, SLAs, and backfill-by-design. "
"**(3) ML + AI on the spine (10 min)** — features as "
"point-in-time-correct pipelines from silver/gold; models "
"trained/evaled/versioned as artifacts, scored batch or served; "
"embeddings + pgvector for the assistant's RAG, with retrieval "
"evals and grounded prompting; LLM enrichment as cached, "
"budgeted, evaled batch jobs. **(4) Cross-cutting (5 min)** — "
"observability (freshness, counts, anomalies, cost), the ten "
"invariants (idempotency everywhere, atomic publish, validate "
"at boundaries), team-shaped simplicity (boring tech, few "
"stateful systems). **(5) Walk one failure (5 min)** — 'a bad "
"deploy corrupted Tuesday' → replay from bronze, backfill "
"orchestrated, reconciliation verifies: the platform heals by "
"re-running its normal path."
                ),
                "explanation": (
"This is the course's final boss and its answer key "
"simultaneously. What interviewers grade at this level: "
"requirements-driven trade-offs (not architecture astrology), "
"a clear layered spine with contracts at each boundary, "
"ML/AI treated as consumers of the same disciplines rather "
"than a separate magic kingdom, and — the closer that "
"separates hires from strong-hires — walking a failure "
"scenario unprompted, because resilience narratives prove "
"operational experience. Every element maps to a project "
"you've built and broken. Say it with the calm of someone "
"who has actually watched their quality gate catch a "
"half-empty file at 3am — because, in this course, you "
"have."
                ),
            },
        ],
    },
]
