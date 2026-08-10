"""
Stage 2 — Interview Algorithms (3 projects).

New-format projects: exercises carry their enrichment inline (refresher,
objectives, hints, resources) and each project has an `interview` section:
LeetCode-standard Q&A with worked answers and explanations.
"""

STAGE2_PROJECTS = [
    # ------------------------------------------------------------------
    {
        "id": "structly",
        "title": "Structly",
        "tagline": "Hashmaps, sets and the patterns behind half of LeetCode",
        "level": "Intermediate",
        "tech": ["dict/set internals", "hashing", "frequency maps", "complexity"],
        "est_hours": 5,
        "brief": (
            "Data-engineering interviews lean hard on hash-based patterns: dedup, "
            "frequency counting, lookups, grouping. Build a small 'toolkit' module in "
            "workspace/structly/ implementing the classics from scratch, benchmarked "
            "against naive versions so big-O stops being theory. Every pattern here "
            "reappears later at scale: dedup becomes DISTINCT, grouping becomes "
            "groupBy, hash lookup becomes a broadcast join."
        ),
        "milestones": [
            "Implement two_sum, group_anagrams and first_unique_char in a toolkit.py module with docstrings stating time/space complexity.",
            "Benchmark two_sum O(n) vs the O(n²) brute force on 10k/100k items with time.perf_counter — plot or print the scaling.",
            "Implement dedup_preserve_order(items) and compare set-based vs list-scan versions the same way.",
            "Write pytest tests covering edge cases: empty input, single element, all-duplicates.",
            "Read your own code and annotate WHERE the hash table does the work in each function — one comment per function.",
        ],
        "under_the_hood": (
            "**How Python dicts actually work.** A dict is an open-addressing hash "
            "table: `hash(key) % table_size` picks a slot; collisions probe to the "
            "next slot. Average O(1) lookup/insert, resize at ~2/3 full. Sets are "
            "dicts without values. That's why `x in my_set` is O(1) but `x in "
            "my_list` is O(n) — the single most exploitable fact in interviews.\n\n"
            "**Why hashable means immutable.** A key that changes after insertion "
            "would be filed under its old hash — unfindable. So lists can't be keys; "
            "tuples can. `dict` preserves insertion order (guaranteed since 3.7), "
            "which dedup_preserve_order exploits.\n\n"
            "**The scaling thread:** a database index is a B-tree or hash table on "
            "disk; Spark's shuffle hash-partitions keys across machines; Redis IS a "
            "giant hash table over the network. Master the in-memory version and "
            "the distributed versions become familiar."
        ),
        "exercises": [
            {
                "id": "st-1",
                "title": "Two Sum (the rite of passage)",
                "instructions": (
"The most famous interview question, done right.\n\n**Your task**\n\nWrite "
"`two_sum(nums, target)` returning the **indices** `[i, j]` (i < j) of the two "
"numbers adding to target, or `None` if no pair exists. Required: **O(n) time, one "
"pass** — as you scan, remember each value's index in a dict and ask 'have I "
"already seen my complement?'. The checker includes a duplicate-values case "
"(`[3, 3]`, target 6) that breaks naive value-keyed approaches if you insert "
"before you look."
                ),
                "starter_code": (
                    "def two_sum(nums, target):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "assert two_sum([2, 7, 11, 15], 9) == [0, 1]\n"
                    "assert two_sum([3, 2, 4], 6) == [1, 2]\n"
                    "assert two_sum([3, 3], 6) == [0, 1]\n"
                    "assert two_sum([1, 2, 3], 99) is None\n"
                    "# rough O(n) sanity: 200k items must be fast\n"
                    "import time\n"
                    "big = list(range(200_000))\n"
                    "t0 = time.perf_counter()\n"
                    "assert two_sum(big, 399_997) == [199_998, 199_999]\n"
                    "assert time.perf_counter() - t0 < 1.0, 'too slow — is this O(n^2)?'\n"
                    "print('PASS: one-pass hashmap two_sum, duplicates handled')\n"
                ),
                "refresher": (
"**The complement trick.** For each number `x`, the partner you need is exactly "
"`target - x`. A dict `{value: index}` built *as you go* answers 'have I seen my "
"complement?' in O(1):\n\n"
"```python\nseen = {}\nfor i, x in enumerate(nums):\n    if target - x in seen:\n        return [seen[target - x], i]\n    seen[x] = i\n```\n\n"
"Look up **before** inserting: that's what makes `[3, 3]` work (the second 3 finds "
"the first) while never matching an element with itself. This check-then-insert "
"scan is a template — you'll reuse it for 'find duplicate', 'longest streak', and "
"a dozen other problems. Trading O(n) memory for O(n) time is the fundamental "
"bargain of hash-based algorithms."
                ),
                "objectives": [
                    "Apply the seen-dict one-pass pattern",
                    "Handle duplicate values via check-before-insert ordering",
                    "State time/space complexity and the memory-for-speed trade",
                ],
                "hints": [
                    "Build {value: index} as you scan with enumerate.",
                    "For each x: is target - x already in the dict? If yes you're done — earlier index first.",
                    "Insert x AFTER the lookup — this handles [3,3] and prevents self-matching.",
                ],
                "resources": [
                    {"title": "Time complexity of Python operations", "url": "https://wiki.python.org/moin/TimeComplexity"},
                    {"title": "Real Python: dicts deep dive", "url": "https://realpython.com/python-dicts/"},
                ],
            },
            {
                "id": "st-2",
                "title": "Group Anagrams (canonical keys)",
                "instructions": (
"A grouping problem whose whole difficulty is choosing the right dict key.\n\n"
"**Your task**\n\nWrite `group_anagrams(words)` returning a list of groups (lists) "
"where each group contains words that are anagrams of each other. Group order "
"doesn't matter; order within a group must follow first appearance. The trick: "
"anagrams share a **canonical form** — e.g. `'eat'` and `'tea'` both sort to "
"`'aet'`. Use that as the dict key. This exact idea — normalize, then group by the "
"normalized key — is how you dedup near-identical records in real pipelines."
                ),
                "starter_code": (
                    "def group_anagrams(words):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "out = group_anagrams(['eat', 'tea', 'tan', 'ate', 'nat', 'bat'])\n"
                    "as_sets = sorted(tuple(g) for g in out)\n"
                    "assert sorted(map(tuple, out)) == sorted(map(tuple, [['eat','tea','ate'], ['tan','nat'], ['bat']])), out\n"
                    "assert group_anagrams([]) == []\n"
                    "assert group_anagrams(['x']) == [['x']]\n"
                    "print('PASS: canonical-key grouping — normalize, then bucket')\n"
                ),
                "refresher": (
"**Group-by is always a dict of lists** (you built this in LogMiner and "
"mini-Spark):\n\n"
"```python\ngroups = {}\nfor w in words:\n    key = canonical(w)\n    groups.setdefault(key, []).append(w)\nreturn list(groups.values())\n```\n\n"
"The art is `canonical()`. For anagrams: `''.join(sorted(w))` — O(k log k) per "
"word — or a 26-letter count tuple for O(k). Keys must be hashable, hence the "
"join-to-string or tuple (a list key raises TypeError).\n\n"
"**The data-engineering translation:** entity resolution. 'Acme Corp.' vs 'ACME "
"corp' group together once you canonicalize (lowercase, strip punctuation). Same "
"algorithm, messier keys — and in SQL it's `GROUP BY lower(trim(name))`."
                ),
                "objectives": [
                    "Design canonical keys that make 'same-ness' hashable",
                    "Use setdefault/dict-of-lists grouping fluently",
                    "Connect canonicalization to real-world dedup and GROUP BY",
                ],
                "hints": [
                    "canonical form: ''.join(sorted(word)).",
                    "groups.setdefault(key, []).append(word), then return list(groups.values()).",
                ],
                "resources": [
                    {"title": "sorted() and key functions", "url": "https://docs.python.org/3/howto/sorting.html"},
                    {"title": "collections.defaultdict (the setdefault alternative)", "url": "https://docs.python.org/3/library/collections.html#collections.defaultdict"},
                ],
            },
            {
                "id": "st-3",
                "title": "LRU Cache (the data-infra favorite)",
                "instructions": (
"Asked constantly in data-platform interviews because caches are everywhere: query "
"caches, connection pools, feature stores.\n\n**Your task**\n\nImplement class "
"`LRUCache(capacity)` with `get(key)` (return value or -1) and `put(key, value)`. "
"When capacity is exceeded, evict the **least recently used** key. Both operations "
"must be O(1) — in Python the honest shortcut is `collections.OrderedDict` with "
"`move_to_end()` and `popitem(last=False)`. Every get AND every put of an existing "
"key counts as a 'use'."
                ),
                "starter_code": (
                    "from collections import OrderedDict\n\n"
                    "class LRUCache:\n"
                    "    def __init__(self, capacity):\n"
                    "        ...\n\n"
                    "    def get(self, key):\n"
                    "        ...\n\n"
                    "    def put(self, key, value):\n"
                    "        ...\n"
                ),
                "check_code": (
                    "c = LRUCache(2)\n"
                    "c.put(1, 'a'); c.put(2, 'b')\n"
                    "assert c.get(1) == 'a'      # 1 is now most-recent\n"
                    "c.put(3, 'c')               # evicts 2 (least recent), not 1\n"
                    "assert c.get(2) == -1\n"
                    "assert c.get(1) == 'a' and c.get(3) == 'c'\n"
                    "c.put(1, 'A')               # update refreshes recency too\n"
                    "c.put(4, 'd')               # evicts 3\n"
                    "assert c.get(3) == -1 and c.get(1) == 'A'\n"
                    "print('PASS: O(1) LRU — the cache pattern behind Redis maxmemory-lru')\n"
                ),
                "refresher": (
"**Why LRU needs two structures in one.** You need O(1) lookup (hash) AND O(1) "
"'move to front / evict from back' (ordering). Classic answer: hashmap + doubly "
"linked list. Python's `OrderedDict` fuses them:\n\n"
"```python\nod.move_to_end(k)          # mark k most-recent\nod.popitem(last=False)     # evict the OLDEST entry\n```\n\n"
"On `get`: hit → move_to_end, return; miss → -1. On `put`: if key exists, update "
"+ move_to_end; else insert, and if over capacity, popitem(last=False).\n\n"
"**Why interviewers love it:** it tests whether you can *compose* structures to "
"meet complexity requirements — the everyday skill of infra work. Redis's "
"`maxmemory-policy allkeys-lru` is this class, industrial-strength; you'll meet "
"it again in Cache Money (Project 14)."
                ),
                "objectives": [
                    "Compose lookup + ordering for dual O(1) requirements",
                    "Drive OrderedDict's move_to_end/popitem correctly",
                    "Explain LRU eviction and where it appears in real infra",
                ],
                "hints": [
                    "get: if key missing return -1; else move_to_end(key) then return the value.",
                    "put: if key in cache, just update value and move_to_end; else insert then check len > capacity.",
                    "Eviction is popitem(last=False) — last=True would evict the newest (a classic bug).",
                ],
                "resources": [
                    {"title": "OrderedDict docs", "url": "https://docs.python.org/3/library/collections.html#collections.OrderedDict"},
                    {"title": "Redis eviction policies", "url": "https://redis.io/docs/latest/develop/reference/eviction/"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"**Contains Duplicate II** (LeetCode-style, Easy/Medium): given an integer array "
"`nums` and integer `k`, return True if there are two indices i, j with "
"`nums[i] == nums[j]` and `abs(i - j) <= k`. Aim for O(n) time."
                ),
                "difficulty": "Easy",
                "topics": ["hashmap", "sliding window"],
                "answer": (
"```python\ndef contains_nearby_duplicate(nums, k):\n    last_seen = {}\n    for i, x in enumerate(nums):\n        if x in last_seen and i - last_seen[x] <= k:\n            return True\n        last_seen[x] = i\n    return False\n```"
                ),
                "explanation": (
"Track each value's most recent index in a dict. When we see the value again, "
"the gap to its *last* occurrence is the smallest possible gap, so checking only "
"that one suffices — earlier occurrences are strictly farther. Overwriting keeps "
"the dict at one entry per distinct value. O(n) time, O(min(n, distinct)) space. "
"Follow-up interviewers like: with a size-k window you can instead keep a set of "
"the last k values, adding/removing as the window slides — same complexity, "
"bounded memory, and that's the version you'd use on an unbounded stream."
                ),
            },
            {
                "question": (
"**Top K Frequent Elements** (Medium): given `nums` and `k`, return the k most "
"frequent values. Discuss the complexity of at least two approaches."
                ),
                "difficulty": "Medium",
                "topics": ["hashmap", "heap", "bucket sort"],
                "answer": (
"```python\nfrom collections import Counter\nimport heapq\n\ndef top_k(nums, k):\n    counts = Counter(nums)                      # O(n)\n    return [x for x, _ in counts.most_common(k)]  # heap under the hood\n\n# explicit heap version — what most_common does:\ndef top_k_heap(nums, k):\n    counts = Counter(nums)\n    return heapq.nlargest(k, counts, key=counts.get)  # O(m log k)\n```"
                ),
                "explanation": (
"Count first (O(n)), then select. Sorting all m distinct values costs O(m log m); "
"a size-k heap costs O(m log k) — the win when k ≪ m. The O(n) bucket-sort "
"variant (index = frequency, since frequency ≤ n) is worth mentioning for the "
"follow-up. This is *the* data-engineering interview question in disguise: top-K "
"per key over a big stream is LogMiner's top_ips, Spark's "
"`groupBy.count.orderBy.limit`, and 'find the hottest products' in SQL "
"(`ORDER BY cnt DESC LIMIT k`). Being able to say 'heap when k is small, sort "
"when you need them all' is exactly the judgment interviews probe."
                ),
            },
            {
                "question": (
"**Design question** (Medium): you're deduplicating a 500M-row daily feed by a "
"string `record_id`. A Python set of all ids doesn't fit in RAM. What are your "
"options and their trade-offs?"
                ),
                "difficulty": "Medium",
                "topics": ["hashing", "system design", "memory"],
                "answer": (
"Main options: **(1) Sort-based dedup** — external sort the file by record_id, "
"then a single linear scan drops adjacent duplicates; O(n log n) disk-friendly, "
"exact. **(2) Partitioned hashing** — hash record_id into K buckets (files); "
"each bucket fits in RAM, dedup each with a set; exact, parallelizable (this is "
"literally what Spark's `dropDuplicates` shuffle does). **(3) Bloom filter** — "
"a bit-array sketch answering 'possibly seen / definitely not seen' in tiny "
"memory; false positives mean you may drop a few non-duplicates, no false "
"negatives. **(4) Database unique index** — load with INSERT ... ON CONFLICT DO "
"NOTHING and let the warehouse's B-tree do it."
                ),
                "explanation": (
"The interviewer is testing whether your in-memory instincts (set-based dedup) "
"scale gracefully. The key insight to verbalize: hash partitioning preserves the "
"'same key → same place' guarantee across files/machines, so per-partition "
"dedup is globally correct — the same property that makes distributed GROUP BY "
"work. Mention exactness requirements (billing data → exact; analytics ~99.9% → "
"Bloom is fine) to show engineering judgment, and idempotent upsert (ww-3) as "
"the boring-but-robust production answer."
                ),
            },
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "algo-gym",
        "title": "Algo Gym",
        "tagline": "Two pointers, sliding windows, binary search — on data problems",
        "level": "Intermediate",
        "tech": ["two pointers", "sliding window", "binary search", "sorting"],
        "est_hours": 6,
        "brief": (
            "The array-technique trio that unlocks most medium interview questions — "
            "practiced on data-flavored problems: session windows over event streams, "
            "merging sorted exports, searching sorted time-series. Build each pattern "
            "as a reusable function in workspace/algo_gym/, tested, with complexity "
            "notes. These are also real pipeline tools: merging sorted files is how "
            "external sort works, and window logic is sessionization."
        ),
        "milestones": [
            "Implement merge_sorted(a, b) (the merge step of mergesort) and extend it to merge_k_sorted using heapq.merge — this is how log files from N servers combine.",
            "Implement longest_session(events, gap): the longest run of consecutive events where each inter-event gap <= gap seconds — classic sessionization.",
            "Implement binary search over a sorted timestamp list: first_at_or_after(ts_list, t) — then compare with the bisect module.",
            "Benchmark linear scan vs binary search on 1M sorted timestamps; write the crossover observation in a comment.",
            "pytest the lot, including empty inputs and single-element edge cases.",
        ],
        "under_the_hood": (
            "**Why these three patterns cover so much.** They're all ways to avoid "
            "nested loops. *Two pointers* exploits sorted order: advance the pointer "
            "whose side can't possibly contribute more — O(n²) → O(n). *Sliding "
            "window* maintains an invariant over a moving range, adding one element "
            "and evicting from the front — perfect for 'longest/shortest run "
            "satisfying X'. *Binary search* halves a sorted space per probe — "
            "O(log n), and it generalizes to 'search over the answer' problems.\n\n"
            "**Timsort**, Python's sort, is a mergesort hybrid exploiting existing "
            "runs — O(n log n) worst, O(n) on nearly-sorted data (common in "
            "time-ordered pipelines!). `sorted(key=...)` is stable: equal keys keep "
            "their order, which multi-level sorts rely on.\n\n"
            "**The data-engineering thread:** external merge sort (merge_k_sorted) "
            "is how databases sort data bigger than RAM and how Spark's "
            "sort-merge-join works; sessionization is a bread-and-butter analytics "
            "task; binary search over sorted partitions is how Parquet row-group "
            "pruning and database indexes cut reads."
        ),
        "exercises": [
            {
                "id": "ag-1",
                "title": "Merge two sorted streams",
                "instructions": (
"The merge step that powers external sort, sort-merge joins, and log "
"consolidation.\n\n**Your task**\n\nWrite `merge_sorted(a, b)` combining two "
"already-sorted lists into one sorted list in **O(len(a) + len(b))** — one pass, "
"two pointers, no `sorted()` call (the checker inspects your source!). Then think: "
"why does this beat concatenate-and-sort (O(n log n)) — and why does it still work "
"when a and b are 10GB files read line-by-line?"
                ),
                "starter_code": (
                    "def merge_sorted(a, b):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "assert merge_sorted([1, 3, 5], [2, 4, 6]) == [1, 2, 3, 4, 5, 6]\n"
                    "assert merge_sorted([], [1]) == [1]\n"
                    "assert merge_sorted([1, 1], [1]) == [1, 1, 1]\n"
                    "assert merge_sorted([1, 2], [10, 20]) == [1, 2, 10, 20]\n"
                    "_src = _USER_SOURCE.replace('merge_sorted', '')   # ignore the function's own name\n"
                    "assert 'sorted(' not in _src and '.sort(' not in _src, 'merge manually — no sorting!'\n"
                    "print('PASS: the merge step — external sort and merge joins are built on this')\n"
                ),
                "refresher": (
"**Two pointers on two lists:**\n\n"
"```python\ni = j = 0\nout = []\nwhile i < len(a) and j < len(b):\n    if a[i] <= b[j]:\n        out.append(a[i]); i += 1\n    else:\n        out.append(b[j]); j += 1\nout.extend(a[i:]); out.extend(b[j:])   # drain the leftover tail\n```\n\n"
"Each comparison permanently retires one element — hence linear time. The `<=` "
"(not `<`) keeps the merge *stable*: ties take from `a` first.\n\n"
"**Why it matters at scale:** you only ever need the *head* of each input — so "
"the inputs can be files, generators, or network streams of any size "
"(`heapq.merge` generalizes to K streams lazily). A database sorting 100GB with "
"1GB of RAM sorts 1GB chunks, spills them, then merge-K's the sorted runs. "
"Spark's sort-merge join sorts both sides and runs exactly this two-pointer walk "
"to match keys."
                ),
                "objectives": [
                    "Write the canonical two-pointer merge with tail draining",
                    "Explain stability and why <= preserves it",
                    "Connect merging to external sort and sort-merge joins",
                ],
                "hints": [
                    "Two indexes i, j starting at 0; compare a[i] vs b[j]; append the smaller and advance that pointer.",
                    "After the while loop ONE list may have leftovers — extend with both slices (one is empty).",
                ],
                "resources": [
                    {"title": "heapq.merge — K-way lazy merging", "url": "https://docs.python.org/3/library/heapq.html#heapq.merge"},
                    {"title": "External sorting", "url": "https://en.wikipedia.org/wiki/External_sorting"},
                ],
            },
            {
                "id": "ag-2",
                "title": "Sessionize an event stream (sliding logic)",
                "instructions": (
"Sessionization — one of the most-asked practical questions for data roles.\n\n"
"**Your task**\n\nWrite `count_sessions(timestamps, gap)`: given a **sorted** list "
"of event timestamps (ints, seconds) for one user, return the number of sessions, "
"where a new session starts whenever the gap since the previous event is "
"**strictly greater** than `gap`. Empty list → 0 sessions. One pass, O(n).\n\n"
"Example: `[0, 10, 20, 100, 105]` with gap 30 → 2 sessions "
"(`0-20` and `100-105`)."
                ),
                "starter_code": (
                    "def count_sessions(timestamps, gap):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "assert count_sessions([], 30) == 0\n"
                    "assert count_sessions([5], 30) == 1\n"
                    "assert count_sessions([0, 10, 20, 100, 105], 30) == 2\n"
                    "assert count_sessions([0, 30, 60], 30) == 1   # exactly gap -> same session\n"
                    "assert count_sessions([0, 31, 62], 30) == 3\n"
                    "print('PASS: sessionization — the analytics question that never dies')\n"
                ),
                "refresher": (
"**Adjacent-pair scanning.** Many stream problems reduce to 'compare each "
"element with its predecessor':\n\n"
"```python\nsessions = 1  # first event opens a session (guard empty first!)\nfor prev, curr in zip(ts, ts[1:]):\n    if curr - prev > gap:\n        sessions += 1\n```\n\n"
"`zip(ts, ts[1:])` pairs neighbors; on huge streams, `itertools.pairwise` does "
"it lazily. Edge discipline — empty list, single event, gap-exactly-equal — is "
"where interviewers watch you; note the spec says *strictly greater*.\n\n"
"**Where you'll use it for real:** in SQL, sessionization is the famous "
"`LAG(ts) OVER (PARTITION BY user ORDER BY ts)` + running-sum-of-breaks pattern "
"(you'll write it in Window Works); in Spark, window functions do the same "
"per-user across a cluster. The one-pass logic you just wrote is what those "
"engines execute per partition."
                ),
                "objectives": [
                    "Scan adjacent pairs with zip/pairwise",
                    "Handle empty/single/boundary-gap edges explicitly",
                    "Recognize sessionization across Python, SQL LAG, and Spark windows",
                ],
                "hints": [
                    "Handle the empty list first: return 0. Then start sessions = 1.",
                    "Compare consecutive events: a gap STRICTLY greater than `gap` starts a new session (> not >=).",
                ],
                "resources": [
                    {"title": "itertools.pairwise", "url": "https://docs.python.org/3/library/itertools.html#itertools.pairwise"},
                    {"title": "Sessionization in SQL (LAG pattern)", "url": "https://mode.com/blog/finding-user-sessions-sql"},
                ],
            },
            {
                "id": "ag-3",
                "title": "Binary search on time-series",
                "instructions": (
"Find things in sorted data in O(log n) — by hand once, then never again.\n\n"
"**Your task**\n\nWrite `first_at_or_after(ts, t)`: given a sorted list of "
"timestamps, return the **index of the first element >= t**, or `len(ts)` if none "
"(this is exactly `bisect.bisect_left` — implement it yourself; the checker blocks "
"the bisect import). Use the half-open invariant lo/hi and be careful: the classic "
"bug family here is off-by-one and infinite loops."
                ),
                "starter_code": (
                    "def first_at_or_after(ts, t):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "assert 'bisect' not in _USER_SOURCE, 'implement it yourself this once'\n"
                    "ts = [10, 20, 20, 30, 40]\n"
                    "assert first_at_or_after(ts, 20) == 1   # FIRST 20\n"
                    "assert first_at_or_after(ts, 25) == 3\n"
                    "assert first_at_or_after(ts, 5) == 0\n"
                    "assert first_at_or_after(ts, 99) == 5\n"
                    "assert first_at_or_after([], 1) == 0\n"
                    "print('PASS: hand-rolled bisect_left — index lookups, partition pruning, same math')\n"
                ),
                "refresher": (
"**The half-open invariant** keeps binary search bug-free: maintain that the "
"answer lies in `[lo, hi)`:\n\n"
"```python\nlo, hi = 0, len(ts)\nwhile lo < hi:\n    mid = (lo + hi) // 2\n    if ts[mid] < t:\n        lo = mid + 1     # mid is too small — exclude it\n    else:\n        hi = mid         # mid could BE the answer — keep it\nreturn lo\n```\n\n"
"Every iteration strictly shrinks the range (that's why there's no infinite "
"loop), and when lo == hi the range is empty — lo is the first index >= t. "
"Choosing `<` vs `<=` in the comparison is what distinguishes bisect_left from "
"bisect_right; being able to derive both is interview gold.\n\n"
"**Real-world siblings:** a B-tree index lookup descends by the same comparison "
"logic; Parquet skips row-groups whose min/max range excludes your filter; "
"Kafka consumers seek to an offset by timestamp. 'It's sorted, so I can halve' "
"is a superpower — spot it everywhere."
                ),
                "objectives": [
                    "Implement bisect_left with the half-open invariant",
                    "Explain why the loop terminates and returns the leftmost match",
                    "Map binary search onto indexes, partition pruning, offset seeks",
                ],
                "hints": [
                    "lo, hi = 0, len(ts); loop while lo < hi.",
                    "If ts[mid] < t the answer is right of mid: lo = mid + 1. Otherwise hi = mid (mid might be it).",
                    "Return lo. Test [10,20,20,30] target 20 by hand on paper — it should land on index 1.",
                ],
                "resources": [
                    {"title": "bisect module", "url": "https://docs.python.org/3/library/bisect.html"},
                    {"title": "Binary search variants explained", "url": "https://en.wikipedia.org/wiki/Binary_search_algorithm"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"**Merge Intervals** (Medium): given intervals `[[start, end], ...]`, merge all "
"overlapping intervals. E.g. `[[1,3],[2,6],[8,10]]` → `[[1,6],[8,10]]`. This is "
"also 'combine overlapping user sessions'."
                ),
                "difficulty": "Medium",
                "topics": ["sorting", "intervals"],
                "answer": (
"```python\ndef merge_intervals(intervals):\n    intervals.sort(key=lambda iv: iv[0])\n    out = []\n    for s, e in intervals:\n        if out and s <= out[-1][1]:\n            out[-1][1] = max(out[-1][1], e)   # extend current\n        else:\n            out.append([s, e])                 # start new\n    return out\n```"
                ),
                "explanation": (
"Sort by start (O(n log n)); then a single scan suffices because after sorting, "
"an interval can only overlap the *most recent* merged one — if it doesn't reach "
"back that far, nothing later will either. The `max()` matters for contained "
"intervals like [2,3] inside [1,6] (a favorite trap). Total O(n log n) time, "
"O(n) output. Data-engineering face of the same problem: merging on-call "
"shifts, coalescing time ranges of sensor outages, or compacting session "
"windows — and in SQL it's the gaps-and-islands pattern you'll meet in Window "
"Works."
                ),
            },
            {
                "question": (
"**Longest Substring Without Repeating Characters** (Medium): return the length "
"of the longest substring of `s` with all distinct characters. O(n) required."
                ),
                "difficulty": "Medium",
                "topics": ["sliding window", "hashmap"],
                "answer": (
"```python\ndef length_of_longest(s):\n    last = {}          # char -> last index seen\n    best = start = 0\n    for i, ch in enumerate(s):\n        if ch in last and last[ch] >= start:\n            start = last[ch] + 1   # jump window past the repeat\n        last[ch] = i\n        best = max(best, i - start + 1)\n    return best\n```"
                ),
                "explanation": (
"A sliding window [start, i] holds distinct characters. On a repeat *inside the "
"window*, snap `start` past the previous occurrence — the dict gives that jump "
"in O(1), so each character is processed once: O(n), O(min(n, alphabet)) space. "
"The subtle guard `last[ch] >= start` ignores stale occurrences left behind "
"when the window previously jumped (test 'abba' to feel it — naive versions "
"move start *backwards*). Windows-with-state is the same mental machinery as "
"streaming aggregations and watermark windows in stream processing."
                ),
            },
            {
                "question": (
"**Search in Rotated Sorted Array** (Medium): a sorted array was rotated at an "
"unknown pivot (e.g. `[4,5,6,7,0,1,2]`). Find target's index in O(log n) or "
"return -1."
                ),
                "difficulty": "Medium",
                "topics": ["binary search"],
                "answer": (
"```python\ndef search_rotated(nums, target):\n    lo, hi = 0, len(nums) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if nums[mid] == target:\n            return mid\n        if nums[lo] <= nums[mid]:            # left half is sorted\n            if nums[lo] <= target < nums[mid]:\n                hi = mid - 1\n            else:\n                lo = mid + 1\n        else:                                 # right half is sorted\n            if nums[mid] < target <= nums[hi]:\n                lo = mid + 1\n            else:\n                hi = mid - 1\n    return -1\n```"
                ),
                "explanation": (
"Key observation: at any mid, *at least one half is properly sorted* (the "
"rotation point is only in one half). Identify the sorted half by comparing "
"endpoints, check whether target lies within its range, and recurse into the "
"half that could contain it. Still halves each step → O(log n). This teaches "
"the general skill of adapting binary search when the neat invariant is "
"disturbed — the same reasoning you use searching a timestamp across "
"log-rotated files or partially-compacted log segments."
                ),
            },
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "heap-stream",
        "title": "Heap & Stream",
        "tagline": "Heaps, top-K at scale, and order statistics on infinite streams",
        "level": "Intermediate+",
        "tech": ["heapq", "priority queues", "streaming algorithms", "reservoir sampling"],
        "est_hours": 6,
        "brief": (
            "Streams don't fit in memory and never end — yet dashboards want top-K "
            "and medians in real time. Build the streaming toolkit: bounded top-K "
            "with a min-heap, running median with two heaps, reservoir sampling for "
            "fair samples of unbounded data. These are the exact algorithms inside "
            "monitoring systems, `ORDER BY ... LIMIT k` execution, and Spark's "
            "approximate quantiles."
        ),
        "milestones": [
            "Implement TopK(k) with .push(item, score) and .result() using a min-heap of size k; verify against sorted() on random data.",
            "Implement RunningMedian with a max-heap (lower half) + min-heap (upper half); stream 100k values through and spot-check against statistics.median.",
            "Implement reservoir_sample(stream, k) and prove fairness empirically: sample 10k times from range(100), plot/count selection frequencies.",
            "Wire TopK into your LogMiner pipeline: top-10 IPs over an unbounded generator without materializing counts of everything.",
            "Write complexity notes: why TopK is O(n log k) not O(n log n) and when that matters (k=10, n=10^9).",
        ],
        "under_the_hood": (
            "**A heap is an array wearing a tree costume.** heapq keeps the "
            "min-heap invariant (parent <= children) in a flat list: children of i "
            "live at 2i+1, 2i+2. Push/pop bubble values up/down in O(log n); "
            "peeking the min is O(1) — `heap[0]`. That 'cheapest element instantly' "
            "property is why heaps power priority queues, schedulers (Airflow's "
            "scheduler queues task instances by priority!), Dijkstra, and k-way "
            "merges.\n\n"
            "**The top-K trick inverted:** to keep the K *largest*, use a *min*-heap "
            "— the root is the weakest current member, the 'bar to clear'. A "
            "newcomer either beats the root (replace) or is discarded. Memory stays "
            "O(k) forever — that's what makes it a *streaming* algorithm.\n\n"
            "**Streaming mindset:** exact answers over unbounded data need "
            "unbounded memory, so streaming trades exactness or completeness for "
            "boundedness: top-K keeps only k, reservoir sampling keeps a fair k, "
            "sketches (HyperLogLog for distinct counts — Spark's approx_count_distinct, "
            "Redis PFCOUNT) keep probabilistic summaries. Knowing *when* an "
            "approximate answer is acceptable is a senior-engineer trait."
        ),
        "exercises": [
            {
                "id": "hs-1",
                "title": "Bounded Top-K over a stream",
                "instructions": (
"The dashboard question: top 10 products by revenue, from a stream too big to "
"store.\n\n**Your task**\n\nWrite `top_k_stream(pairs, k)` where pairs is an "
"iterable of `(item, score)`. Return the k items with the highest scores, ordered "
"best-first, using a **min-heap capped at size k** (heapq) — never storing more "
"than k entries (the checker feeds a generator and requires ties/order handled: "
"push tuples of (score, item)). One pass, O(n log k)."
                ),
                "starter_code": (
                    "import heapq\n\n"
                    "def top_k_stream(pairs, k):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "def gen():\n"
                    "    for p in [('a', 5), ('b', 9), ('c', 1), ('d', 7), ('e', 3)]:\n"
                    "        yield p\n"
                    "assert top_k_stream(gen(), 3) == ['b', 'd', 'a']\n"
                    "assert top_k_stream(iter([]), 3) == []\n"
                    "assert top_k_stream(iter([('x', 1)]), 5) == ['x']\n"
                    "big = ((f'i{n}', n % 1000) for n in range(50_000))\n"
                    "out = top_k_stream(big, 2)\n"
                    "assert len(out) == 2 and all(o.startswith('i') for o in out)\n"
                    "print('PASS: O(k) memory top-K — the streaming dashboard workhorse')\n"
                ),
                "refresher": (
"**Min-heap as a bouncer.** Keep the k best seen so far; the heap root is the "
"*worst of the best* — the bar to clear:\n\n"
"```python\nheap = []\nfor item, score in pairs:\n    if len(heap) < k:\n        heapq.heappush(heap, (score, item))\n    elif score > heap[0][0]:\n        heapq.heapreplace(heap, (score, item))  # pop root + push, one op\nreturn [item for score, item in sorted(heap, reverse=True)]\n```\n\n"
"Tuples compare element-first, so `(score, item)` heaps order by score. Final "
"sort of k elements is O(k log k) — trivial. Contrast with `sorted(all)[:k]`: "
"that's O(n log n) time and O(n) memory, impossible on a true stream.\n\n"
"**Where this exact code lives in the wild:** `heapq.nlargest` implements it; "
"databases execute `ORDER BY score DESC LIMIT 10` with a top-K heap instead of "
"a full sort (look for 'top-N heapsort' in Postgres EXPLAIN); Spark's "
"`takeOrdered` runs one per partition then merges the per-partition heaps — "
"map-side top-K, the mini-spark pattern again."
                ),
                "objectives": [
                    "Maintain a bounded min-heap for streaming top-K",
                    "Use tuple comparison and heapreplace idiomatically",
                    "Contrast O(n log k)/O(k) with sort-everything, and name real systems using it",
                ],
                "hints": [
                    "Push (score, item) tuples — heapq orders by first element.",
                    "Under k items: heappush. At capacity: only act if score beats heap[0][0]; heapreplace is push+pop in one.",
                    "Finish: sort the heap descending and extract items.",
                ],
                "resources": [
                    {"title": "heapq — official docs", "url": "https://docs.python.org/3/library/heapq.html"},
                    {"title": "Real Python: heaps & priority queues", "url": "https://realpython.com/python-heapq-module/"},
                ],
            },
            {
                "id": "hs-2",
                "title": "Running median (two heaps)",
                "instructions": (
"A famous Hard question — and a real metric (p50 latency) computed exactly.\n\n"
"**Your task**\n\nImplement class `RunningMedian` with `.add(x)` and `.median()`. "
"Strategy: a **max-heap of the lower half** (store negatives — heapq is min-only) "
"and a **min-heap of the upper half**, kept balanced (sizes differ by at most 1, "
"lower may hold the extra). Median: top of the bigger heap, or the mean of both "
"tops when equal. Add is O(log n), median O(1)."
                ),
                "starter_code": (
                    "import heapq\n\n"
                    "class RunningMedian:\n"
                    "    def __init__(self):\n"
                    "        self.lo = []   # max-heap via negatives (lower half)\n"
                    "        self.hi = []   # min-heap (upper half)\n\n"
                    "    def add(self, x):\n"
                    "        ...\n\n"
                    "    def median(self):\n"
                    "        ...\n"
                ),
                "check_code": (
                    "rm = RunningMedian()\n"
                    "import statistics\n"
                    "seen = []\n"
                    "for x in [5, 15, 1, 3, 8, 7, 9, 10, 20, 6]:\n"
                    "    rm.add(x); seen.append(x)\n"
                    "    assert abs(rm.median() - statistics.median(seen)) < 1e-9, (seen, rm.median())\n"
                    "print('PASS: exact streaming median — p50 the honest way')\n"
                ),
                "refresher": (
"**Two heaps facing each other.** Everything <= median sits in a max-heap "
"(`lo`); everything above in a min-heap (`hi`). The two roots bracket the "
"median. The insert dance:\n\n"
"```python\nheapq.heappush(self.lo, -x)                    # 1. into lower half\nheapq.heappush(self.hi, -heapq.heappop(self.lo))  # 2. its max moves up\nif len(self.hi) > len(self.lo):               # 3. rebalance sizes\n    heapq.heappush(self.lo, -heapq.heappop(self.hi))\n```\n\n"
"Push-then-transfer guarantees ordering between halves without comparisons; the "
"rebalance keeps lo either equal or one larger. Median: `-lo[0]` when odd, "
"`(-lo[0] + hi[0]) / 2` when even. The negation trick (max-heap = min-heap of "
"negatives) is standard Python — heapq has no max-heap.\n\n"
"**Why medians (not averages) rule ops dashboards:** one 60s timeout in a "
"thousand 10ms requests barely moves the mean but lies about typical "
"experience; p50/p99 don't. At true scale, exact medians give way to sketches "
"(t-digest — what Spark's approxQuantile uses), but interviews want this exact "
"two-heap machine."
                ),
                "objectives": [
                    "Simulate a max-heap with negation",
                    "Keep dual heaps balanced through the push-transfer-rebalance dance",
                    "Explain percentiles vs means and where sketches take over",
                ],
                "hints": [
                    "Always do the 3-step dance: push to lo (negated), move lo's max to hi, rebalance if hi grew bigger.",
                    "median(): odd total → -self.lo[0]; even → average of -self.lo[0] and self.hi[0].",
                    "Remember EVERY value in lo is stored negated — negate on the way in AND out.",
                ],
                "resources": [
                    {"title": "heapq docs (see the priority queue notes)", "url": "https://docs.python.org/3/library/heapq.html"},
                    {"title": "t-digest: percentile sketches at scale", "url": "https://github.com/tdunning/t-digest"},
                ],
            },
            {
                "id": "hs-3",
                "title": "Reservoir sampling (fair samples of infinity)",
                "instructions": (
"How do you take a fair 1000-row sample of a stream whose length you don't know? "
"This algorithm is on real DE interview loops.\n\n**Your task**\n\nWrite "
"`reservoir_sample(stream, k, rng)`: keep the first k items; for item i (1-based, "
"i > k) draw `j = rng.randrange(i)` and if `j < k`, replace `reservoir[j]`. "
"Result: every item has exactly k/n probability of surviving — provable by "
"induction. `rng` is a seeded random.Random (passed in so the checker can verify "
"determinism AND fairness statistically)."
                ),
                "starter_code": (
                    "def reservoir_sample(stream, k, rng):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "import random\n"
                    "out = reservoir_sample(iter(range(5)), 10, random.Random(1))\n"
                    "assert out == [0, 1, 2, 3, 4], 'short streams: keep everything'\n"
                    "counts = [0] * 20\n"
                    "for trial in range(4000):\n"
                    "    rng = random.Random(trial)\n"
                    "    for x in reservoir_sample(iter(range(20)), 5, rng):\n"
                    "        counts[x] += 1\n"
                    "expected = 4000 * 5 / 20   # = 1000 each if fair\n"
                    "assert all(abs(c - expected) < 150 for c in counts), f'unfair sample: {counts}'\n"
                    "print('PASS: provably fair sampling of unbounded streams')\n"
                ),
                "refresher": (
"**The elegant induction.** Keep a k-slot reservoir. Item i (i > k) gets in "
"with probability k/i, evicting a uniformly random resident:\n\n"
"```python\nreservoir = []\nfor i, x in enumerate(stream, 1):\n    if i <= k:\n        reservoir.append(x)\n    else:\n        j = rng.randrange(i)      # uniform in [0, i)\n        if j < k:                  # happens with prob k/i\n            reservoir[j] = x\n```\n\n"
"Why it's fair: item i enters with k/i; every later item i+1..n fails to evict "
"it with probability (1 - 1/(i+1))·... which telescopes to i/n — multiply and "
"you get k/n for everyone. The single randrange doing double duty (admit? "
"which slot?) is the classy touch.\n\n"
"**Where you'll use it:** sampling events for a debug table, fair training "
"subsets when labels stream in, `TABLESAMPLE`-style peeks at unbounded feeds. "
"Naive alternatives — 'take the first k' (biased to old data) or 'store "
"everything, sample later' (unbounded memory) — are exactly the wrong answers "
"interviewers listen for."
                ),
                "objectives": [
                    "Implement reservoir sampling with the single-draw trick",
                    "Sketch the k/n fairness argument",
                    "Identify biased alternatives and why they fail",
                ],
                "hints": [
                    "enumerate(stream, 1) gives 1-based i — the probabilities depend on it.",
                    "First k items: append. After: j = rng.randrange(i); if j < k: reservoir[j] = x.",
                ],
                "resources": [
                    {"title": "Reservoir sampling", "url": "https://en.wikipedia.org/wiki/Reservoir_sampling"},
                    {"title": "random module docs", "url": "https://docs.python.org/3/library/random.html"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"**Kth Largest Element in a Stream** (Easy/Medium): design class `KthLargest(k, "
"nums)` with `add(val)` returning the kth largest value seen so far. Then: why "
"is this the same problem as 'top-K products by revenue, updated live'?"
                ),
                "difficulty": "Easy",
                "topics": ["heap", "streaming"],
                "answer": (
"```python\nimport heapq\n\nclass KthLargest:\n    def __init__(self, k, nums):\n        self.k = k\n        self.heap = nums\n        heapq.heapify(self.heap)          # O(n)\n        while len(self.heap) > k:\n            heapq.heappop(self.heap)\n\n    def add(self, val):\n        if len(self.heap) < self.k:\n            heapq.heappush(self.heap, val)\n        elif val > self.heap[0]:\n            heapq.heapreplace(self.heap, val)\n        return self.heap[0]               # root = kth largest\n```"
                ),
                "explanation": (
"A min-heap of the k largest values: the root is by definition the kth largest. "
"add() is O(log k); memory O(k) regardless of stream length. heapify is O(n) — "
"a fact interviewers probe (building by n pushes would be O(n log n)). The "
"live-dashboard version is identical with (score, item) tuples: the heap holds "
"the current leaderboard and the root is the entry bar. Trade-off note worth "
"saying aloud: this maintains the *set* of top-k cheaply but ranked output "
"costs O(k log k) per read — fine when reads are rarer than writes."
                ),
            },
            {
                "question": (
"**Merge K Sorted Lists** (Hard): merge k sorted linked lists (or files) into "
"one sorted output. Compare the heap approach with pairwise merging."
                ),
                "difficulty": "Hard",
                "topics": ["heap", "k-way merge", "external sort"],
                "answer": (
"```python\nimport heapq\n\ndef merge_k(lists):\n    heap = [(lst[0], i, 0) for i, lst in enumerate(lists) if lst]\n    heapq.heapify(heap)\n    out = []\n    while heap:\n        val, i, j = heapq.heappop(heap)\n        out.append(val)\n        if j + 1 < len(lists[i]):\n            heapq.heappush(heap, (lists[i][j + 1], i, j + 1))\n    return out\n```\nDivide-and-conquer pairwise merging is the other O(N log k) approach: merge "
"lists in pairs, halving the count each round."
                ),
                "explanation": (
"The heap holds one 'head' per list (size k); each pop emits the global minimum "
"and pushes that list's next element: N total elements × O(log k) heap ops = "
"O(N log k), memory O(k) beyond output. The index `i` in the tuple breaks ties "
"so values never compare unhashable payloads — a practical detail interviewers "
"appreciate. This IS external sort's merge phase and log-consolidation across "
"k servers; `heapq.merge` ships it lazily (generator output), which is the "
"version you'd use on files too big for RAM. Pairwise merging has the same "
"complexity but materializes intermediates — worse constant factors on disk."
                ),
            },
            {
                "question": (
"**Conceptual** (Medium): your pipeline must report the number of *distinct* "
"users per day across 2B events. An exact set is too big. What do you propose, "
"and what are the error characteristics?"
                ),
                "difficulty": "Medium",
                "topics": ["sketches", "HyperLogLog", "streaming"],
                "answer": (
"Use **HyperLogLog**: hash each user id; track, per bucket, the maximum number "
"of leading zeros observed in the hashes; combine buckets with a harmonic mean "
"to estimate cardinality. Standard error ≈ 1.04/√m for m buckets — e.g. m=16384 "
"gives ~0.8% error in ~16KB of memory, regardless of cardinality. HLLs also "
"**merge losslessly** (bucket-wise max), so per-hour sketches roll up into "
"daily/weekly counts for free. Available as `approx_count_distinct` in Spark, "
"`PFADD/PFCOUNT` in Redis, `APPROX_COUNT_DISTINCT` in most warehouses."
                ),
                "explanation": (
"The intuition to narrate: rare hash patterns imply many distinct values — "
"seeing a hash with 20 leading zeros suggests ~2^20 distinct inputs, and "
"averaging many buckets tames the variance. The crucial systems property is "
"mergeability — it makes the sketch distributable (compute per partition, "
"merge, exactly the map/shuffle/reduce shape) and re-aggregatable across time "
"windows. Knowing when ~1% error is acceptable (dashboards, trends) versus not "
"(billing) — and saying so unprompted — is what separates senior answers."
                ),
            },
        ],
    },
]
