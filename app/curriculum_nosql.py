"""
Stage 4 — NoSQL & Non-Relational Databases (3 projects).

In-app exercises implement the *engines' ideas* in Python (aggregation
pipelines, TTL caches, consistent hashing) — the build-it-yourself approach —
while milestones drive the real MongoDB and Redis services in the compose
stack (docker compose --profile db up -d).
"""

STAGE4_PROJECTS = [
    # ------------------------------------------------------------------
    {
        "id": "doc-store",
        "title": "DocStore",
        "tagline": "MongoDB: documents, aggregation pipelines, and when schemaless bites",
        "level": "Intermediate+",
        "tech": ["MongoDB", "documents", "aggregation pipeline", "indexes", "schema design"],
        "est_hours": 7,
        "brief": (
            "Your stack's Mongo comes pre-seeded with product reviews (nested "
            "documents) and a clickstream — the classic document-database workloads. "
            "Learn CRUD and the aggregation pipeline properly, design "
            "document schemas (embed vs reference — THE eternal question), and "
            "meet the sharp edges: no joins, no transactions across documents "
            "(mostly), and schema drift. In-app you'll build a mini aggregation "
            "engine so $group never feels like magic."
        ),
        "milestones": [
            "Connect from Jupyter (pymongo, host 'mongo') to db 'appdata'; explore reviews and events with find(), projections, and sort/limit.",
            "Aggregation practice: average rating per product ($group), top-10 most-reviewed products, rating histogram ($bucket) — check one result against a hand computation.",
            "Unwind nested arrays: average 'quality' aspect score per product via $unwind on aspects — the join-substitute for embedded data.",
            "Design exercise: model orders three ways (fully embedded items, referenced products, hybrid with snapshot prices) and write one paragraph on when each wins.",
            "Indexes: explain() a query on rating + created_at before/after a compound index — same planner story as Postgres, different syntax.",
            "Export reviews to the Postgres warehouse (flatten with Python, ww-1 style) — your first cross-database hop, formalized in Stage 6.",
        ],
        "under_the_hood": (
            "**Documents are pre-joined data.** A review embeds its aspects; "
            "reading it is one seek, no join — the whole point. The cost: querying "
            "*across* documents (all reviews mentioning 'shipping' per product "
            "category) requires the aggregation pipeline, and updating denormalized "
            "copies (product name in every review) is your problem now. Embed what "
            "you read together and rarely change; reference what's shared, "
            "unbounded, or independently updated.\n\n"
            "**The aggregation pipeline is your LazyFrame:** an array of stages "
            "($match → $unwind → $group → $sort), each transforming a document "
            "stream — literally the generator pipelines of LogMiner. $match early "
            "uses indexes (predicate pushdown!); $group builds a hash of "
            "accumulators (mini-spark's reduce); $lookup exists but marks a design "
            "that maybe wanted a relational database.\n\n"
            "**BSON, not JSON:** typed binary (dates, ints, ObjectId — its "
            "timestamp prefix makes _id roughly insertion-ordered). WiredTiger "
            "stores documents in B-trees with MVCC snapshots — more familiar than "
            "the marketing suggests. 'Schemaless' really means *the schema lives "
            "in your application code and its enforcement is your job* — schema "
            "drift is the tax, and validation ($jsonSchema) the mitigation."
        ),
        "exercises": [
            {
                "id": "ds-1",
                "title": "Build the aggregation pipeline",
                "instructions": (
"Make $match/$group/$sort stop being magic by writing them.\n\n**Your task**\n\n"
"Implement `aggregate(docs, pipeline)` supporting stages: `{'$match': {field: "
"value}}` (equality only), `{'$group': {'_id': '$field', 'total': {'$sum': "
"'$other'}, 'count': {'$sum': 1}}}` (group by field; accumulators $sum of a "
"'$field' or of literal 1), and `{'$sort': {field: -1|1}}`. Stages apply in "
"order, like Mongo. The checker runs a real-shaped pipeline over review docs."
                ),
                "starter_code": (
                    "def aggregate(docs, pipeline):\n"
                    "    \"\"\"docs: list of dicts. pipeline: list of stage dicts.\"\"\"\n"
                    "    ...\n"
                ),
                "check_code": (
                    "docs = [\n"
                    "    {'product': 'p1', 'rating': 5, 'votes': 10},\n"
                    "    {'product': 'p2', 'rating': 3, 'votes': 2},\n"
                    "    {'product': 'p1', 'rating': 4, 'votes': 1},\n"
                    "    {'product': 'p1', 'rating': 5, 'votes': 5},\n"
                    "]\n"
                    "out = aggregate(docs, [\n"
                    "    {'$match': {'rating': 5}},\n"
                    "    {'$group': {'_id': '$product', 'total': {'$sum': '$votes'}, 'count': {'$sum': 1}}},\n"
                    "    {'$sort': {'total': -1}},\n"
                    "])\n"
                    "assert out == [{'_id': 'p1', 'total': 15, 'count': 2}], out\n"
                    "out2 = aggregate(docs, [{'$group': {'_id': '$product', 'count': {'$sum': 1}}},\n"
                    "                        {'$sort': {'count': -1}}])\n"
                    "assert out2[0] == {'_id': 'p1', 'count': 3}\n"
                    "print('PASS: you implemented $match/$group/$sort — pipelines demystified')\n"
                ),
                "refresher": (
"**Each stage is a function: list-of-docs → list-of-docs.** Dispatch on the "
"stage name and fold:\n\n"
"```python\nfor stage in pipeline:\n    (name, spec), = stage.items()   # one key per stage\n    if name == '$match':\n        docs = [d for d in docs if all(d.get(k) == v\n                for k, v in spec.items())]\n    elif name == '$group':\n        ...  # dict of accumulators keyed by the '$field' value\n    elif name == '$sort':\n        (field, direction), = spec.items()\n        docs = sorted(docs, key=lambda d: d[field],\n                      reverse=direction == -1)\n```\n\n"
"$group is mini-spark's map+reduce in one: bucket docs by "
"`d[spec['_id'][1:]]` (strip the '$'), and for each accumulator add "
"`d[field]` if the spec value is a '$string', else the literal (that's how "
"`{'$sum': 1}` counts). The `'$field'` string convention is Mongo's way of "
"saying 'reference, not literal' — a tiny DSL. You've now written the "
"execution model of every pipeline you'll ever send Mongo, which is exactly "
"how to reason about their performance: stages stream, $group materializes "
"state, order matters."
                ),
                "objectives": [
                    "Implement stage dispatch over a document stream",
                    "Decode the '$field' reference convention and {'$sum': 1} counting",
                    "Reason about pipeline performance from the execution model",
                ],
                "hints": [
                    "Loop stages; each replaces docs. One key per stage dict: (name, spec), = stage.items().",
                    "$group: build {key: accumulated_dict}; the group key comes from spec['_id'][1:]; return list(groups.values()) with _id included.",
                    "Accumulator: if the spec value is a string starting with '$', add d[that field]; if it's a number, add the number.",
                ],
                "resources": [
                    {"title": "MongoDB aggregation pipeline", "url": "https://www.mongodb.com/docs/manual/core/aggregation-pipeline/"},
                    {"title": "$group accumulators", "url": "https://www.mongodb.com/docs/manual/reference/operator/aggregation/group/"},
                ],
            },
            {
                "id": "ds-2",
                "title": "Embed vs reference (the modeling decision)",
                "instructions": (
"THE document-modeling interview question, as executable logic.\n\n**Your "
"task**\n\nImplement `recommend_model(relation)` taking a dict describing a "
"parent-child relation: keys `child_count` ('few'|'many'|'unbounded'), "
"`read_together` (bool), `child_updated_independently` (bool), "
"`child_shared_across_parents` (bool). Return 'embed', 'reference', or "
"'hybrid' by these professional rules, in priority order: shared across "
"parents OR unbounded growth → 'reference'; updated independently but read "
"together → 'hybrid' (reference + snapshot of stable fields); read together "
"with few/many children → 'embed'; otherwise → 'reference'."
                ),
                "starter_code": (
                    "def recommend_model(relation):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "assert recommend_model({'child_count': 'few', 'read_together': True,\n"
                    "    'child_updated_independently': False, 'child_shared_across_parents': False}) == 'embed'\n"
                    "assert recommend_model({'child_count': 'unbounded', 'read_together': True,\n"
                    "    'child_updated_independently': False, 'child_shared_across_parents': False}) == 'reference'\n"
                    "assert recommend_model({'child_count': 'few', 'read_together': True,\n"
                    "    'child_updated_independently': False, 'child_shared_across_parents': True}) == 'reference'\n"
                    "assert recommend_model({'child_count': 'many', 'read_together': True,\n"
                    "    'child_updated_independently': True, 'child_shared_across_parents': False}) == 'hybrid'\n"
                    "assert recommend_model({'child_count': 'few', 'read_together': False,\n"
                    "    'child_updated_independently': False, 'child_shared_across_parents': False}) == 'reference'\n"
                    "print('PASS: the embed/reference decision tree, executable')\n"
                ),
                "refresher": (
"**The three forces of document modeling:**\n\n"
"*Read locality* — data read together should live together (embedding = one "
"disk seek). *Write independence* — data updated on its own schedule wants "
"its own document (embedded copies mean fan-out updates). *Cardinality* — "
"documents cap at 16MB and arrays shouldn't grow unboundedly (comments on a "
"viral post: the classic blowup).\n\n"
"The **hybrid/snapshot** pattern deserves special attention because it's "
"everywhere in production: an order embeds `{product_id, name, price}` — "
"reference for identity, *snapshot* of the fields as they were at purchase "
"time. Sound familiar? It's SCD2's insight (Star Schema Studio) in document "
"clothing: transactional facts must freeze the state they occurred under.\n\n"
"Encoding judgment as an explicit priority-ordered decision function is "
"itself a professional habit — this one mirrors MongoDB's own schema design "
"guidance, and walking an interviewer through these exact forces (with the "
"16MB and unbounded-array caveats) IS the strong answer to 'how would you "
"model X in Mongo?'"
                ),
                "objectives": [
                    "Weigh read locality vs write independence vs cardinality",
                    "Apply the snapshot/hybrid pattern and link it to SCD2",
                    "Answer embed-vs-reference interview questions with a framework",
                ],
                "hints": [
                    "Implement the rules in the exact priority order given — first match wins.",
                    "shared OR unbounded → reference, before anything else.",
                ],
                "resources": [
                    {"title": "MongoDB data modeling", "url": "https://www.mongodb.com/docs/manual/data-modeling/"},
                    {"title": "6 rules of thumb for MongoDB schema design", "url": "https://www.mongodb.com/blog/post/6-rules-of-thumb-for-mongodb-schema-design"},
                ],
            },
            {
                "id": "ds-3",
                "title": "$unwind + regroup (nested array analytics)",
                "instructions": (
"Analytics over embedded arrays — the operation that replaces joins.\n\n**Your "
"task**\n\nImplement `avg_aspect_scores(reviews)`: each review has `aspects: "
"[{'name': ..., 'score': ...}, ...]`. Flatten (unwind) all aspects across all "
"reviews and return `{aspect_name: average_score}` with averages as floats. "
"Mind the edge: reviews with no aspects key or an empty list. This is "
"$unwind + $group, in the Python you'd use before deciding the pipeline is "
"worth it."
                ),
                "starter_code": (
                    "def avg_aspect_scores(reviews):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "reviews = [\n"
                    "    {'id': 1, 'aspects': [{'name': 'quality', 'score': 4}, {'name': 'shipping', 'score': 2}]},\n"
                    "    {'id': 2, 'aspects': [{'name': 'quality', 'score': 5}]},\n"
                    "    {'id': 3},\n"
                    "    {'id': 4, 'aspects': []},\n"
                    "]\n"
                    "out = avg_aspect_scores(reviews)\n"
                    "assert out == {'quality': 4.5, 'shipping': 2.0}, out\n"
                    "assert avg_aspect_scores([]) == {}\n"
                    "print('PASS: unwind + regroup — nested-array analytics unlocked')\n"
                ),
                "refresher": (
"**Unwinding is a flat-map:** one document with a 3-element array becomes "
"three (doc, element) rows — then ordinary grouping applies:\n\n"
"```python\nsums, counts = {}, {}\nfor r in reviews:\n    for a in r.get('aspects', []):       # .get: missing key = empty\n        sums[a['name']] = sums.get(a['name'], 0) + a['score']\n        counts[a['name']] = counts.get(a['name'], 0) + 1\nreturn {k: sums[k] / counts[k] for k in sums}\n```\n\n"
"Tracking (sum, count) pairs rather than lists of values is the streaming-"
"average idiom — O(distinct aspects) memory, and it's *mergeable* (combine "
"two partial (sum, count) pairs by adding) which makes it distributable: "
"Spark's `avg` computes exactly these partials per partition and merges "
"(never averaging averages — the classic wrong answer, weighting groups "
"incorrectly!). In Mongo this whole function is "
"`[{'$unwind': '$aspects'}, {'$group': {'_id': '$aspects.name', 'avg': "
"{'$avg': '$aspects.score'}}}]`; now you know its cost model: unwinding "
"multiplies the stream by average array length before grouping shrinks it."
                ),
                "objectives": [
                    "Flat-map nested arrays with defensive .get access",
                    "Keep mergeable (sum, count) partials instead of value lists",
                    "Explain why averaging averages is wrong and what Spark does instead",
                ],
                "hints": [
                    "Nested loop: for review → for aspect in review.get('aspects', []).",
                    "Two dicts (sums, counts) keyed by aspect name; divide at the end.",
                ],
                "resources": [
                    {"title": "$unwind", "url": "https://www.mongodb.com/docs/manual/reference/operator/aggregation/unwind/"},
                    {"title": "Streaming/mergeable aggregations (Spark avg)", "url": "https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.functions.avg.html"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"Design the MongoDB schema for a blogging platform: posts, comments (can be "
"thousands per post), tags, and authors. Which relations do you embed, which "
"do you reference, and why?"
                ),
                "difficulty": "Medium",
                "topics": ["document modeling", "embed vs reference"],
                "answer": (
"**Tags: embed** as a string array in the post (few, read together, rarely "
"restructured) with a multikey index for tag queries. **Author: reference** "
"(author_id) plus a *snapshot* of display fields (name, avatar) — shared "
"across posts, updated independently; accept stale snapshots or fan-out "
"update on rename. **Comments: reference** in their own collection keyed by "
"post_id — 'thousands, unbounded' is the direct trigger: embedding risks the "
"16MB document cap, makes every post read carry all comments, and turns "
"comment-writes into post-document contention. Paginate with a compound "
"index (post_id, created_at). Optionally embed the *latest 3* comments in "
"the post as a display cache — the subset pattern."
                ),
                "explanation": (
"Each decision maps to the three forces: locality (tags), shared+independent "
"(author → reference + snapshot, the hybrid pattern), unbounded growth "
"(comments → reference, always). The subset-pattern flourish shows you "
"design for the read path (render a post page in ONE query) while keeping "
"unbounded data external. Strong candidates also mention: write contention "
"on hot documents, $lookup existing for the occasional cross-collection "
"need, and schema validation to keep 'schemaless' honest. Weak answers "
"embed comments — interviewers are specifically fishing for that."
                ),
            },
            {
                "question": (
"Your Mongo aggregation `[{'$group': ...}, {'$match': ...}]` is slow on 50M "
"documents. The same logic with stages reversed is 40x faster. Explain why, "
"and state the general optimization principle."
                ),
                "difficulty": "Medium",
                "topics": ["aggregation performance", "pushdown"],
                "answer": (
"$group must consume the ENTIRE stream, building accumulator state for every "
"group, before anything passes on; a $match placed after it filters the "
"*grouped results* — all 50M documents were processed regardless. Reversed, "
"$match runs first: it can use an index (only stage position 1 can!), cuts "
"the stream to the relevant slice, and $group then aggregates a fraction of "
"the data. The principle is **predicate pushdown**: filter as early — and as "
"index-friendly — as possible. Mongo's optimizer auto-reorders some cases, "
"but $match-after-$group on *derived* fields can't move, so design pipelines "
"filter-first deliberately."
                ),
                "explanation": (
"The same principle you saw as Catalyst's filter pushdown (ss-3) and 'WHERE "
"before GROUP BY, HAVING after' in SQL (sf-1) — one idea, three syntaxes, "
"which is exactly how to frame it in an interview to show depth. Additional "
"points: $project early to shed unused fields (column pruning), $unwind "
"multiplies stream size so filter before unwinding, allowDiskUse for groups "
"exceeding 100MB memory, and explain('executionStats') as the Mongo EXPLAIN "
"ANALYZE. Recognizing that every engine — SQL, Mongo, Spark — rewards the "
"same filter-early/shrink-early instincts is the mark of an engineer rather "
"than a syntax user."
                ),
            },
            {
                "question": (
"When would you pick MongoDB over PostgreSQL for a new service — and when is "
"that the wrong call? Postgres has JSONB; Mongo has multi-document "
"transactions. Cut through the marketing."
                ),
                "difficulty": "Hard",
                "topics": ["database selection", "trade-offs"],
                "answer": (
"Mongo genuinely wins when: the natural unit of work is a self-contained "
"document (content, catalogs, user profiles), schema varies legitimately "
"per record, horizontal write-scaling via sharding is a near-term need, and "
"cross-entity queries/joins are rare. Postgres (often with JSONB for the "
"flexible parts) wins when: data is relational at heart (orders/customers/"
"inventory), you need real cross-entity transactions and constraints "
"(foreign keys — Mongo has none), ad-hoc analytics and joins are routine, or "
"the team already runs Postgres well. Wrong calls: choosing Mongo to 'avoid "
"designing a schema' (the schema debt just moves into application code and "
"drifts), or choosing it for scale a single Postgres node handles fine "
"(which is farther than most think). Mongo's multi-document transactions "
"exist but cost coordination and are a smell that the model wants to be "
"relational."
                ),
                "explanation": (
"Interviewers ask this to detect dogma in either direction. The strong frame "
"is workload-first: unit of access, consistency needs, query patterns, team "
"operations — then the honest middle path that JSONB covers most 'flexible "
"fields' needs inside a relational core, while true document workloads with "
"shard-scale writes justify Mongo. Bonus signal: mention that 'schemaless' "
"means schema-in-code (validation is your job), that Mongo secondary reads "
"are eventually consistent by default, and that polyglot persistence (next "
"project!) means services can use both — per workload, not per fashion."
                ),
            },
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "cache-money",
        "title": "Cache Money",
        "tagline": "Redis: caching, TTLs, rate limiting, leaderboards — speed as a datastore",
        "level": "Intermediate+",
        "tech": ["Redis", "caching patterns", "TTL", "sorted sets", "rate limiting"],
        "est_hours": 6,
        "brief": (
            "Redis is the speed layer of nearly every serious architecture: cache, "
            "rate limiter, queue, leaderboard, session store — all from five data "
            "types over a network hash table. Use the real Redis in your stack for "
            "the milestones; in-app, build the patterns from scratch (TTL cache, "
            "sliding-window rate limiter, leaderboard) so you understand exactly "
            "what Redis does for you — and what it can't (durability trade-offs)."
        ),
        "milestones": [
            "Connect from Jupyter (redis-py, host 'redis'); tour the types: SET/GET with EX ttl, INCR counters, LPUSH/RPOP lists, ZADD/ZRANGE sorted sets, HSET hashes.",
            "Cache-aside: wrap a slow warehouse query (revenue per country) with Redis caching + 60s TTL; measure the hit-path speedup; then discuss what happens when the warehouse updates (staleness!).",
            "Build a rate limiter with INCR + EXPIRE (fixed window), then upgrade to a ZSET sliding window; hammer it in a loop to verify limits hold.",
            "Leaderboard: ZADD customer spend from the warehouse; query top-10 (ZREVRANGE), a customer's rank (ZREVRANK), and spenders in a range (ZRANGEBYSCORE).",
            "Kill Redis mid-demo (docker compose stop redis) and observe your cache-aside code degrade gracefully to the database — resilience is part of the pattern.",
        ],
        "under_the_hood": (
            "**Why Redis is fast:** all data lives in RAM, and a single-threaded "
            "event loop (dd-3's model!) executes commands one at a time — no locks, "
            "no context switches, sub-millisecond ops. Single-threading is a "
            "*feature*: every command is atomic by construction, which is why INCR "
            "works as a concurrent counter with zero ceremony.\n\n"
            "**Durability is a dial, not a given:** RDB snapshots (lose minutes on "
            "crash), AOF with everysec fsync (lose ≤1s), or appendfsync always "
            "(slow). Treat Redis as a cache or recoverable state, not the system "
            "of record — the warehouse remains truth. Eviction policies "
            "(allkeys-lru — your st-3 LRUCache, industrialized) govern behavior at "
            "maxmemory.\n\n"
            "**Sorted sets** are the crown jewel: a hash (member → score) PLUS a "
            "skip list ordered by score — O(log n) inserts, O(log n + k) range "
            "queries. A skip list is 'binary search over linked lists via "
            "probabilistic express lanes' — the same halving instinct as your "
            "ag-3 bisect. Leaderboards, sliding windows, delayed-job queues: all "
            "ZSET applications."
        ),
        "exercises": [
            {
                "id": "cm-1",
                "title": "TTL cache with cache-aside",
                "instructions": (
"The most-used pattern in production systems, built honestly.\n\n**Your "
"task**\n\nImplement `TTLCache(ttl)` with `.get(key, now)` and `.set(key, "
"value, now)` — entries expire when `now >= stored_time + ttl` (expired get → "
"None). Then `cached_fetch(cache, key, now, fetch_fn)` implementing "
"cache-aside: hit → cached value, no fetch call; miss/expired → call "
"fetch_fn(), store, return. The checker counts fetch calls and advances a "
"fake clock — no real sleeping."
                ),
                "starter_code": (
                    "class TTLCache:\n"
                    "    def __init__(self, ttl):\n"
                    "        self.ttl = ttl\n"
                    "        self.store = {}   # key -> (value, stored_at)\n\n"
                    "    def get(self, key, now):\n"
                    "        ...\n\n"
                    "    def set(self, key, value, now):\n"
                    "        ...\n\n"
                    "def cached_fetch(cache, key, now, fetch_fn):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "calls = {'n': 0}\n"
                    "def slow_fetch():\n"
                    "    calls['n'] += 1\n"
                    "    return 'DATA'\n"
                    "c = TTLCache(ttl=60)\n"
                    "assert cached_fetch(c, 'rev', 0, slow_fetch) == 'DATA' and calls['n'] == 1\n"
                    "assert cached_fetch(c, 'rev', 30, slow_fetch) == 'DATA' and calls['n'] == 1  # hit\n"
                    "assert cached_fetch(c, 'rev', 60, slow_fetch) == 'DATA' and calls['n'] == 2  # expired at exactly ttl\n"
                    "assert c.get('missing', 0) is None\n"
                    "print('PASS: cache-aside with TTL — the pattern behind every fast dashboard')\n"
                ),
                "refresher": (
"**Cache-aside (lazy caching):** the app owns the logic — try cache, fall "
"back to source, populate on the way out:\n\n"
"```python\ndef cached_fetch(cache, key, now, fetch_fn):\n    val = cache.get(key, now)\n    if val is not None:\n        return val\n    val = fetch_fn()\n    cache.set(key, val, now)\n    return val\n```\n\n"
"TTL check is lazy too — expiry happens at read time (`now - stored_at >= "
"ttl`), which is essentially Redis's model (plus a background sampler). "
"Injecting `now` as a parameter instead of calling time.time() inside is "
"what makes the checker (and any real test) possible — *clock injection*, a "
"testability habit worth keeping.\n\n"
"The pattern's fine print, which interviews probe: a `None`-meaning-miss API "
"can't cache legitimate None/negative results (sentinel objects fix it); "
"expiry causes **thundering herd** — all requests stampede the database the "
"moment a hot key dies (mitigations: jittered TTLs, single-flight locks, "
"background refresh); and staleness is a *chosen contract*: TTL 60 means "
"'up to 60s stale is acceptable'. Say those three things and you've aced "
"the caching question."
                ),
                "objectives": [
                    "Implement cache-aside with lazy TTL expiry",
                    "Use clock injection for testable time logic",
                    "Name the fine print: negative caching, thundering herd, staleness contracts",
                ],
                "hints": [
                    "get: missing key → None; else unpack (value, stored_at); expired if now - stored_at >= ttl.",
                    "cached_fetch: get → return on hit; else fetch_fn(), set, return.",
                    "Expiry boundary: at now == stored_at + ttl the entry is ALREADY expired (>=).",
                ],
                "resources": [
                    {"title": "Redis: SET with EX/TTL", "url": "https://redis.io/docs/latest/commands/set/"},
                    {"title": "AWS: caching patterns (cache-aside et al.)", "url": "https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/caching-patterns.html"},
                ],
            },
            {
                "id": "cm-2",
                "title": "Sliding-window rate limiter",
                "instructions": (
"Protect an API like a pro — the exact algorithm Redis ZSETs run in "
"production.\n\n**Your task**\n\nImplement `RateLimiter(limit, window)` with "
"`.allow(user, now)` → bool: allow if the user has made fewer than `limit` "
"*allowed* requests in the last `window` seconds (sliding, not fixed "
"buckets). Keep per-user timestamp lists, pruning entries older than "
"`now - window`. Denied requests do NOT count toward the window. The checker "
"walks a timeline crossing the boundary."
                ),
                "starter_code": (
                    "class RateLimiter:\n"
                    "    def __init__(self, limit, window):\n"
                    "        self.limit = limit\n"
                    "        self.window = window\n"
                    "        self.hits = {}   # user -> list of allowed timestamps\n\n"
                    "    def allow(self, user, now):\n"
                    "        ...\n"
                ),
                "check_code": (
                    "rl = RateLimiter(limit=3, window=10)\n"
                    "assert [rl.allow('u', t) for t in [0, 1, 2]] == [True, True, True]\n"
                    "assert rl.allow('u', 3) is False           # 4th within window\n"
                    "assert rl.allow('u', 9) is False           # still within\n"
                    "assert rl.allow('u', 10) is True           # t=0 slid out (now-window=0, prune < 0? boundary!)\n"
                    "assert rl.allow('v', 3) is True            # separate user\n"
                    "print('PASS: sliding window — smooth limits, no bucket-boundary bursts')\n"
                ),
                "refresher": (
"**Why sliding beats fixed windows:** fixed 10s buckets allow 3 requests at "
"t=9.9 and 3 more at t=10.1 — a 6-burst across the boundary. A sliding "
"window always looks back exactly `window` seconds:\n\n"
"```python\ndef allow(self, user, now):\n    ts = self.hits.setdefault(user, [])\n    ts[:] = [t for t in ts if t > now - self.window]  # prune old\n    if len(ts) < self.limit:\n        ts.append(now)\n        return True\n    return False\n```\n\n"
"Boundary care: prune keeps `t > now - window` (strict), so a hit at t=0 "
"exits the window exactly at now=10 — matching the checker. Only *allowed* "
"requests append (else attackers extend their own ban).\n\n"
"**The Redis translation** is nearly literal: timestamps in a ZSET scored by "
"time — `ZREMRANGEBYSCORE key -inf (now-window)` prunes, `ZCARD` counts, "
"`ZADD` records, wrapped in a pipeline/Lua script for atomicity across those "
"steps (single-threaded execution makes the Lua script a transaction). "
"Follow-ups you can now field: token bucket (allows controlled bursts, O(1) "
"memory vs O(limit) here) and fixed-window-with-two-bucket interpolation "
"(approximate sliding at O(1))."
                ),
                "objectives": [
                    "Implement prune-count-append sliding windows with strict boundaries",
                    "Map the algorithm onto Redis ZSET commands + Lua atomicity",
                    "Compare sliding window vs token bucket vs fixed window",
                ],
                "hints": [
                    "Prune first, every call: keep timestamps t > now - window.",
                    "Deny WITHOUT appending — denied calls never consume window budget.",
                    "setdefault(user, []) then mutate the list in place (ts[:] = ...).",
                ],
                "resources": [
                    {"title": "Redis sorted sets", "url": "https://redis.io/docs/latest/develop/data-types/sorted-sets/"},
                    {"title": "Rate limiting algorithms compared", "url": "https://blog.cloudflare.com/counting-things-a-lot-of-different-things/"},
                ],
            },
            {
                "id": "cm-3",
                "title": "Leaderboard on a skip-list mindset",
                "instructions": (
"The ZSET workload: ranked queries without full sorts.\n\n**Your task**\n\n"
"Implement `Leaderboard` with `.upsert(member, score)` (add or update), "
"`.top(n)` → list of (member, score) best-first (ties: member ascending), "
"`.rank(member)` → 0-based rank from the top (None if absent), and "
"`.count_in_range(lo, hi)` → members with lo <= score <= hi. Keep it simple "
"with a dict + sorted views (Redis's skip list makes these O(log n); yours "
"may be O(n log n) — the API contract is what matters)."
                ),
                "starter_code": (
                    "class Leaderboard:\n"
                    "    def __init__(self):\n"
                    "        self.scores = {}\n\n"
                    "    def upsert(self, member, score):\n"
                    "        ...\n\n"
                    "    def top(self, n):\n"
                    "        ...\n\n"
                    "    def rank(self, member):\n"
                    "        ...\n\n"
                    "    def count_in_range(self, lo, hi):\n"
                    "        ...\n"
                ),
                "check_code": (
                    "lb = Leaderboard()\n"
                    "lb.upsert('ada', 100); lb.upsert('bo', 250); lb.upsert('chi', 100); lb.upsert('dee', 400)\n"
                    "lb.upsert('ada', 300)   # update, not duplicate\n"
                    "assert lb.top(3) == [('dee', 400), ('ada', 300), ('bo', 250)]\n"
                    "assert lb.rank('dee') == 0 and lb.rank('chi') == 3\n"
                    "assert lb.rank('ghost') is None\n"
                    "assert lb.count_in_range(200, 350) == 2   # ada 300, bo 250\n"
                    "print('PASS: the ZSET API — leaderboards, percentiles, delayed queues')\n"
                ),
                "refresher": (
"**One sort key, many queries.** Everything derives from the sorted view "
"`sorted(self.scores.items(), key=lambda kv: (-kv[1], kv[0]))` — descending "
"score, ascending member for stable ties:\n\n"
"```python\ndef top(self, n): return self._sorted()[:n]\ndef rank(self, m):\n    for i, (member, _) in enumerate(self._sorted()):\n        if member == m: return i\n    return None\n```\n\n"
"Redis keeps this view *incrementally* with a skip list: layered linked "
"lists where each node appears in higher 'express lanes' with probability "
"1/2 — search skims the top lane and drops down, achieving O(log n) like a "
"balanced tree but with simpler lock-free-friendly code. Plus the companion "
"hash gives O(1) member→score. That dual structure (again! LRU was "
"hash+list) is why ZRANK, ZADD and ZRANGEBYSCORE are all cheap "
"simultaneously.\n\n"
"ZSET applications beyond leaderboards, worth having on tap: sliding-window "
"rate limits (cm-2), delayed job queues (score = execute_at; poll "
"ZRANGEBYSCORE -inf now), priority queues, and time-series indexes. 'What "
"Redis type would you use for X?' — the answer is a ZSET surprisingly "
"often."
                ),
                "objectives": [
                    "Derive top/rank/range queries from one sort contract",
                    "Explain skip lists and the hash+skiplist dual structure",
                    "List the ZSET application family for design questions",
                ],
                "hints": [
                    "Sort key: (-score, member) gets descending score with alphabetical ties.",
                    "upsert is just dict assignment — the dict prevents duplicates.",
                    "count_in_range: sum(1 for s in self.scores.values() if lo <= s <= hi).",
                ],
                "resources": [
                    {"title": "Skip lists (Pugh's original idea, readable)", "url": "https://en.wikipedia.org/wiki/Skip_list"},
                    {"title": "Redis ZSET commands", "url": "https://redis.io/docs/latest/commands/?group=sorted-set"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"Design a caching layer for a product page serving 50k req/s with a Postgres "
"backend. Cover: pattern choice, TTL strategy, invalidation, and the failure "
"modes you're defending against."
                ),
                "difficulty": "Hard",
                "topics": ["caching architecture", "invalidation"],
                "answer": (
"Cache-aside on Redis with per-entity keys (`product:{id}:v2`), JSON/msgpack "
"values, TTL ~5min **with ±20% jitter** (staggers expiry, prevents "
"synchronized stampedes). Invalidation: on product update, DELETE the key "
"(next read repopulates) — delete-not-update avoids writing stale race "
"losers; include a schema version in the key for deploy-safe format changes. "
"Defenses: **thundering herd** on hot keys → single-flight locking (SET NX "
"on a lock key; losers briefly serve stale or wait) or background refresh "
"ahead of expiry; **cache penetration** (queries for nonexistent ids) → "
"cache negative results briefly or bloom-filter known ids; **Redis down** → "
"degrade to Postgres with a circuit breaker and aggressive timeouts, never "
"an outage. Monitor hit ratio (target >95% here) and eviction rate."
                ),
                "explanation": (
"The grading rubric in such interviews is essentially the defense list: "
"herd, penetration, stampede-by-synchronized-TTL, stale-write races, and "
"graceful degradation — each named with its standard mitigation. Cache-aside "
"is right because the DB remains source of truth and cache loss is an "
"availability blip, not data loss (contrast write-through/write-behind, "
"worth mentioning to show you know the alternatives). The versioned-key "
"trick quietly solves the hardest operational problem (invalidation across "
"deploys). If pushed on consistency: TTL is your staleness SLA; true "
"read-your-writes needs the delete-on-write path plus sticky routing or "
"short TTLs — be explicit that it's a trade, not magic."
                ),
            },
            {
                "question": (
"Implement (describe) a distributed lock with Redis. Why is the naive "
"SETNX-then-DEL version broken, and what does the correct version add?"
                ),
                "difficulty": "Hard",
                "topics": ["distributed locks", "atomicity"],
                "answer": (
"Correct single-node version: acquire with `SET lock_key {unique_token} NX "
"PX 30000` — one atomic command setting the key only-if-absent WITH a TTL. "
"Release with a Lua script: `if GET == my_token then DEL` — atomically "
"verifying ownership before deleting. The naive version breaks three ways: "
"SETNX without TTL deadlocks forever if the holder crashes; adding EXPIRE "
"as a second command isn't atomic (crash between them = deadlock again); "
"and blind DEL on release can delete *someone else's* lock — you stalled "
"past your TTL, another client acquired, your DEL frees their lock. The "
"token + Lua check closes that. Remaining honest caveat: if your process "
"pauses (GC, VM freeze) past the TTL while mid-critical-section, mutual "
"exclusion is violated — fencing tokens (monotonic counters checked by the "
"resource) are the real fix; Redlock across nodes remains debated."
                ),
                "explanation": (
"A precision question: every flaw is an atomicity gap, and the fixes are "
"'make it one atomic step' (SET NX PX; Lua for check-and-del) — Redis's "
"single-threaded execution is what makes Lua scripts transactional. The "
"stalled-holder scenario and fencing tokens are the senior differentiator "
"(from Kleppmann's famous critique): TTL-based locks provide *liveness*, "
"but only resource-side fencing provides *safety* under arbitrary pauses. "
"For data pipelines specifically: prefer idempotent tasks over distributed "
"locks wherever possible (ww-3 again) — needing perfect mutual exclusion is "
"often a design smell you can engineer away."
                ),
            },
            {
                "question": (
"Your Redis instance hit maxmemory and latency spiked; some cached keys "
"also vanished 'randomly'. Explain what happened and how you'd configure "
"and monitor it properly."
                ),
                "difficulty": "Medium",
                "topics": ["eviction", "operations"],
                "answer": (
"At maxmemory, every write triggers the eviction policy. Default `noeviction` "
"refuses writes with errors; `allkeys-lru` (typical for caches) evicts "
"approximately-least-recently-used keys — the 'random' disappearances (it "
"samples 5 keys and evicts the LRU-est, so it's approximate). Latency spike: "
"eviction work happens on the single event-loop thread, and large values "
"(or big DEL/expire cascades) block everything behind them. Configure: "
"maxmemory ~70-80% of RAM (leave room for fork-based persistence copies), "
"policy allkeys-lru (pure cache) or volatile-ttl (mixed usage — only evict "
"TTL'd keys), lazyfree-lazy-eviction to offload frees. Monitor: "
"used_memory vs maxmemory, evicted_keys rate, keyspace hit ratio, and "
"SLOWLOG for blocking commands (KEYS, big SMEMBERS — ban them)."
                ),
                "explanation": (
"Connects st-3's LRU to production reality: Redis approximates LRU by "
"sampling (exact LRU costs too much bookkeeping — an engineering trade "
"worth naming), and the single-threaded model (its superpower for "
"atomicity) is precisely why slow operations are catastrophic. The "
"fork-memory point (RDB/AOF-rewrite fork copy-on-write can double memory "
"under write load) explains the 70-80% rule and is a detail that reads as "
"real operational experience. Meta-lesson for the interview: cache "
"evictions aren't failures, they're the design — but eviction of *hot* keys "
"means undersized memory, visible as hit-ratio decay."
                ),
            },
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "polyglot",
        "title": "Polyglot Persistence",
        "tagline": "One dataset, four stores — choosing databases like an architect",
        "level": "Advanced",
        "tech": ["architecture", "CAP/PACELC", "consistency models", "storage engines"],
        "est_hours": 6,
        "brief": (
            "The capstone of the database stages: stop thinking in products, start "
            "thinking in trade-offs. You'll route one business's workloads across "
            "your actual stack — Postgres (transactions/analytics), Mongo "
            "(catalog documents), Redis (sessions/cache) — implement the routing "
            "layer in Python, and study consistency hands-on by building "
            "consistent hashing and a quorum read/write simulator. This project is "
            "80% of the 'design a data platform' interview."
        ),
        "milestones": [
            "Route the workloads: for an e-commerce business, assign 8 given workloads (checkout, catalog browse, session store, order analytics, review text, spend leaderboard, event firehose, vector search) to stores in a decision doc with one-line justifications.",
            "Implement the polyglot repository: a Python OrderService that writes the order to Postgres (transaction), caches the customer's recent orders in Redis, and records a review-prompt document in Mongo — one logical operation, three stores.",
            "Face the dual-write problem your OrderService just created: kill Redis mid-write and observe partial state; write up the outbox pattern as the fix (implemented for real in Stage 6).",
            "Build consistent_hashing.py (exercise pg-1 grown up): 3 'nodes', 10k keys, kill a node — measure the fraction of keys that moved vs naive mod-N.",
            "Quorum lab: with your simulator (exercise pg-3), test R/W combos on 5 replicas — find every combo where R+W <= N returns stale data, and relate it to Mongo read/write concerns.",
        ],
        "under_the_hood": (
            "**CAP, stated honestly:** during a network partition, a distributed "
            "store must choose — refuse some requests (consistency) or answer "
            "with possibly-stale data (availability). PACELC adds the everyday "
            "half: Else (no partition), you still trade Latency vs Consistency — "
            "cross-region sync replication is slow *always*, not just during "
            "failures. Single-node Postgres ducks the theorem (and that's an "
            "argument FOR it); clustered Mongo/Cassandra/Dynamo-style stores live "
            "on this spectrum via replication settings.\n\n"
            "**Quorums make the trade quantitative:** N replicas, write to W, "
            "read from R. R+W > N forces read/write sets to overlap — someone in "
            "your read set saw the latest write (version numbers break the tie). "
            "R=1, W=1: fast, available, stale-able. Mongo's "
            "writeConcern/readConcern and Cassandra's consistency levels are "
            "exactly this dial.\n\n"
            "**Storage engines shape workloads:** B-trees (Postgres, WiredTiger) "
            "read fast, write-amplify on random inserts; LSM-trees (Cassandra, "
            "RocksDB) batch writes into sorted runs — write-optimized, "
            "read-pays-compaction. Redis skips disk-first entirely. 'Which "
            "database?' usually reduces to: what's the unit of access, what "
            "consistency does the business need, and which engine matches the "
            "read/write ratio."
        ),
        "exercises": [
            {
                "id": "pg-1",
                "title": "Consistent hashing (the scaling classic)",
                "instructions": (
"Why does adding a cache node NOT invalidate everything? This algorithm — a "
"top-tier interview favorite.\n\n**Your task**\n\nImplement "
"`HashRing(nodes, vnodes=100)` with `.get_node(key)` and `.add_node(name)` / "
"`.remove_node(name)`. Place vnodes per node on the ring at "
"`stable_hash(f'{node}:{i}')` (keep the list sorted); a key routes to the "
"first vnode clockwise from `stable_hash(key)`, wrapping around at the end "
"(your ag-3 bisect does the lookup).\n\n"
"**Use the provided `stable_hash`, never Python's built-in `hash()`** — "
"built-in string hashing is randomized per process, so two machines (or two "
"restarts of one) would build *different rings* and route the same key to "
"different nodes. Real implementations use MD5/SHA for exactly this reason.\n\n"
"The checker verifies determinism, balance, and the headline property: "
"removing one of 4 nodes remaps only ~1/4 of keys."
                ),
                "starter_code": (
                    "import bisect\n"
                    "import hashlib\n\n"
                    "def stable_hash(s):\n"
                    "    \"\"\"Deterministic across processes and machines.\n"
                    "    Python's built-in hash() is randomized per interpreter (PYTHONHASHSEED),\n"
                    "    which would give every node a different ring — a distributed-cache disaster.\"\"\"\n"
                    "    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)\n\n"
                    "class HashRing:\n"
                    "    def __init__(self, nodes, vnodes=100):\n"
                    "        self.vnodes = vnodes\n"
                    "        self.ring = []          # sorted list of (position, node)\n"
                    "        for n in nodes:\n"
                    "            self.add_node(n)\n\n"
                    "    def add_node(self, name):\n"
                    "        ...\n\n"
                    "    def remove_node(self, name):\n"
                    "        ...\n\n"
                    "    def get_node(self, key):\n"
                    "        ...\n"
                ),
                "check_code": (
                    "ring = HashRing(['a', 'b', 'c', 'd'])\n"
                    "keys = [f'k{i}' for i in range(4000)]\n"
                    "before = {k: ring.get_node(k) for k in keys}\n"
                    "assert before == {k: ring.get_node(k) for k in keys}, 'must be deterministic'\n"
                    "from collections import Counter\n"
                    "load = Counter(before.values())\n"
                    "assert all(600 < c < 1400 for c in load.values()), f'unbalanced: {load}'\n"
                    "ring.remove_node('d')\n"
                    "after = {k: ring.get_node(k) for k in keys}\n"
                    "moved = sum(1 for k in keys if before[k] != after[k])\n"
                    "assert moved < 1800, f'{moved}/4000 moved — should be ~1000 (only d\\'s keys)'\n"
                    "assert all(after[k] == before[k] for k in keys if before[k] != 'd'), 'non-d keys must not move'\n"
                    "print(f'PASS: {moved}/4000 keys moved on node loss — consistent hashing works')\n"
                ),
                "refresher": (
"**The problem with `hash(key) % N`:** change N and *every* key remaps — "
"one node failure invalidates the whole cache fleet. **The ring fix:** hash "
"nodes AND keys into the same space; a key belongs to the next node "
"clockwise. Now removing a node only remaps *its own* arc.\n\n"
"```python\ndef add_node(self, name):\n    for i in range(self.vnodes):\n        bisect.insort(self.ring, (stable_hash(f'{name}:{i}'), name))\n\ndef get_node(self, key):\n    i = bisect.bisect(self.ring, (stable_hash(key),))\n    return self.ring[i % len(self.ring)][1]   # wrap = clockwise\n```\n\n"
"**Why `stable_hash` and not `hash()`?** CPython randomizes string hashing "
"per process (PYTHONHASHSEED) as a defence against hash-collision DoS. "
"Excellent for dicts, catastrophic for a ring: every client would compute "
"different node positions, so the same key would resolve to different "
"servers — and a restart would silently invalidate the whole cache. Anything "
"that must agree *across processes* (partitioners, shard routers, cache "
"rings, bucketed files) needs a stable hash: MD5/SHA, or an explicitly "
"seeded non-cryptographic hash like MurmurHash.\n\n"

"**Vnodes** (100 positions per node) solve the balance problem — one "
"position per node makes arc sizes wildly uneven; many positions average "
"out (law of large numbers), and a dead node's load spreads over *all* "
"survivors instead of dumping onto one neighbor.\n\n"
"This is the routing layer of Dynamo/Cassandra, Memcached clients, and "
"Kafka-consumer partition assignment in spirit. Note the contrast with "
"ss-1's fixed hash partitioning: Spark can use mod-N because a job's N "
"never changes mid-flight; *elastic* systems need the ring. Knowing when "
"each applies is the architect-level point."
                ),
                "objectives": [
                    "Implement ring lookup with bisect + wraparound",
                    "Explain vnodes and the minimal-remapping guarantee",
                    "Use a process-stable hash and say why built-in hash() breaks distribution",
                    "Contrast mod-N vs ring hashing and when each is right",
                ],
                "hints": [
                    "add_node: insort (stable_hash(f'{name}:{i}'), name) for each vnode.",
                    "get_node: bisect over (stable_hash(key),) then index % len(ring) for wraparound.",
                    "remove_node: rebuild the ring without that node's entries (filter).",
                ],
                "resources": [
                    {"title": "Consistent hashing (Dynamo paper §4.2)", "url": "https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf"},
                    {"title": "Cassandra: data distribution", "url": "https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html"},
                ],
            },
            {
                "id": "pg-2",
                "title": "Workload → store router",
                "instructions": (
"Encode database-selection judgment as reviewable logic.\n\n**Your task**\n\n"
"Implement `choose_store(workload)` over a dict with keys: `unit` "
"('row'|'document'|'key_value'|'vector'), `consistency` "
"('strong'|'eventual'), `pattern` ('transactional'|'analytical'|"
"'cache'|'search'), `relationships` (bool — cross-entity joins/constraints "
"needed). Priority rules: cache pattern OR key_value unit → 'redis'; vector "
"unit → 'postgres+pgvector'; relationships OR strong+transactional → "
"'postgres'; document unit with eventual consistency → 'mongo'; analytical "
"→ 'postgres' (the warehouse); else → 'postgres' (the safe default)."
                ),
                "starter_code": (
                    "def choose_store(workload):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "assert choose_store({'unit': 'key_value', 'consistency': 'eventual', 'pattern': 'cache', 'relationships': False}) == 'redis'\n"
                    "assert choose_store({'unit': 'row', 'consistency': 'strong', 'pattern': 'transactional', 'relationships': True}) == 'postgres'\n"
                    "assert choose_store({'unit': 'document', 'consistency': 'eventual', 'pattern': 'analytical', 'relationships': False}) == 'mongo'\n"
                    "assert choose_store({'unit': 'vector', 'consistency': 'eventual', 'pattern': 'search', 'relationships': False}) == 'postgres+pgvector'\n"
                    "assert choose_store({'unit': 'row', 'consistency': 'eventual', 'pattern': 'analytical', 'relationships': False}) == 'postgres'\n"
                    "assert choose_store({'unit': 'document', 'consistency': 'strong', 'pattern': 'transactional', 'relationships': False}) == 'postgres'\n"
                    "print('PASS: architecture judgment, made explicit and testable')\n"
                ),
                "refresher": (
"**Selection is dimensional analysis, not brand preference.** The four axes "
"in this function are the ones that matter in real reviews:\n\n"
"*Unit of access* — what does one operation touch? A row among related "
"rows, a self-contained document, an opaque value by key, a similarity "
"neighborhood? *Consistency* — does the business break on staleness "
"(payments) or tolerate it (view counts)? *Pattern* — OLTP point "
"operations, analytical scans, sub-ms cache hits, similarity search? "
"*Relationships* — do cross-entity constraints/joins carry the logic?\n\n"
"Note two deliberate biases to defend out loud: strong+transactional beats "
"'document' (a document workload demanding strong transactional semantics "
"belongs in Postgres — JSONB holds the documents; the ds-2 lesson's "
"mirror), and the else-branch defaults to Postgres because *boring "
"technology you operate well* beats optimal-on-paper. In interviews, "
"walking these axes before naming ANY product is the seniority signal; "
"the encoded priority order is your defense against 'why not X?' — you "
"can point at which axis X loses on."
                ),
                "objectives": [
                    "Analyze workloads along unit/consistency/pattern/relationship axes",
                    "Defend Postgres-as-default and strong-transactional overrides",
                    "Turn architecture judgment into reviewable code",
                ],
                "hints": [
                    "Implement rules in the exact priority order — early return per rule.",
                    "The tricky case: document + strong + transactional → postgres (rule 3 fires before the mongo rule).",
                ],
                "resources": [
                    {"title": "Kleppmann, DDIA ch. 2-3 (the book for this)", "url": "https://dataintensive.net/"},
                    {"title": "Choose Boring Technology", "url": "https://boringtechnology.club/"},
                ],
            },
            {
                "id": "pg-3",
                "title": "Quorum reads/writes simulator",
                "instructions": (
"Make R + W > N intuitive by breaking it.\n\n**Your task**\n\nImplement "
"`QuorumStore(n)` — n replicas, each a dict storing "
"`key → (value, version)`. `.write(key, value, w)`: bump a global version, "
"write to the FIRST w replicas (list order — deterministic, simulating the "
"others being slow/partitioned), return the version. `.read(key, r)`: query "
"the first r replicas, return the value with the **highest version** among "
"responses (None if none have it). Then demonstrate: with n=3, does "
"w=1,r=1 guarantee reading your write? The checker proves both sides."
                ),
                "starter_code": (
                    "class QuorumStore:\n"
                    "    def __init__(self, n):\n"
                    "        self.replicas = [{} for _ in range(n)]\n"
                    "        self.version = 0\n\n"
                    "    def write(self, key, value, w):\n"
                    "        ...\n\n"
                    "    def read(self, key, r):\n"
                    "        ...\n"
                ),
                "check_code": (
                    "qs = QuorumStore(3)\n"
                    "qs.write('x', 'v1', w=3)\n"
                    "assert qs.read('x', r=1) == 'v1'          # fully replicated: any read works\n"
                    "qs.write('x', 'v2', w=1)                   # sloppy write: only replica 0 has v2\n"
                    "assert qs.read('x', r=1) == 'v2'          # read replica 0: lucky\n"
                    "assert qs.replicas[2].get('x', (None, 0))[0] == 'v1', 'replica 2 should be stale'\n"
                    "assert qs.read('x', r=3) == 'v2'          # R+W>N: overlap guarantees freshness\n"
                    "qs2 = QuorumStore(3)\n"
                    "qs2.write('y', 'old', w=3)\n"
                    "qs2.write('y', 'new', w=1)\n"
                    "stale_possible = 'old'  # a read of only replicas 1..2 (r=2 starting at index 1)\n"
                    "highest = max((rep['y'] for rep in qs2.replicas[1:3]), key=lambda t: t[1])[0]\n"
                    "assert highest == 'old', 'replicas 1-2 truly are stale'\n"
                    "assert qs2.read('y', r=2) == 'new'        # our read includes replica 0 -> fresh\n"
                    "print('PASS: R+W>N overlap felt in code — quorums demystified')\n"
                ),
                "refresher": (
"**Versions are the tiebreaker.** With multiple replicas answering, 'latest' "
"needs a definition — a monotonic version (real systems: per-key vector "
"clocks or last-write-wins timestamps, each with famous problems):\n\n"
"```python\ndef write(self, key, value, w):\n    self.version += 1\n    for rep in self.replicas[:w]:\n        rep[key] = (value, self.version)\n    return self.version\n\ndef read(self, key, r):\n    hits = [rep[key] for rep in self.replicas[:r] if key in rep]\n    return max(hits, key=lambda t: t[1])[0] if hits else None\n```\n\n"
"The overlap argument in one line: any w-set and r-set with r + w > n "
"share at least one replica (pigeonhole), and that shared replica has the "
"newest version — max() surfaces it. Your checker's stale scenario (w=1 "
"then reading the *other* two replicas) is exactly what R+W ≤ N permits.\n\n"
"Real-system mapping: Mongo writeConcern:'majority' + readConcern:"
"'majority' ≈ w,r = ⌈n/2⌉+... (majority overlap); Cassandra exposes the "
"raw dial (ONE/QUORUM/ALL) per query. And the anti-entropy afterthought "
"your simulator skips — read repair, hinted handoff — is how lazy replicas "
"eventually catch up: 'eventual' consistency is a *process*, not a hope."
                ),
                "objectives": [
                    "Implement versioned quorum reads/writes",
                    "Prove the R+W>N overlap guarantee by pigeonhole",
                    "Map w/r to Mongo write/read concerns and Cassandra levels",
                ],
                "hints": [
                    "write: increment self.version first; write (value, version) to replicas[:w].",
                    "read: gather (value, version) from replicas[:r] that have the key; return max by version.",
                    "Empty hits → None (read of an unknown key).",
                ],
                "resources": [
                    {"title": "Dynamo paper (quorums, hinted handoff)", "url": "https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf"},
                    {"title": "MongoDB read/write concerns", "url": "https://www.mongodb.com/docs/manual/reference/write-concern/"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"Design the data layer for a ride-hailing app: driver locations (updated "
"every 2s), trips (payments!), user profiles, and a real-time 'drivers "
"near me' query. Choose stores and justify."
                ),
                "difficulty": "Hard",
                "topics": ["polyglot architecture", "geo", "consistency"],
                "answer": (
"**Trips/payments: Postgres** — money demands ACID transactions, "
"constraints, audit history (append-only trip_events table). **Driver "
"locations: Redis** — 2s updates × 100k drivers is an ephemeral, "
"high-churn, loss-tolerant workload: GEOADD/GEOSEARCH gives 'near me' "
"natively; losing 2 seconds of positions on crash is harmless (next update "
"heals it) — persistence off or lax. **User profiles: Postgres** (JSONB "
"for flexible preference blobs) — relational to trips, moderate write "
"rate. **Trip analytics: warehouse** (Postgres/columnar) fed by ETL from "
"the OLTP tables. Critical connective tissue: location writes NEVER touch "
"Postgres (write-rate mismatch is the design's whole point), and trip "
"state transitions emit events (outbox) that update Redis-cached driver "
"status — one-directional flows, no dual-write ambiguity."
                ),
                "explanation": (
"The question tests workload *segregation*: the killer error is one store "
"for everything (Postgres melts under location writes; Redis can't hold "
"payments). Each choice maps to the pg-2 axes — unit of access, "
"consistency, pattern. The Redis-geo answer shows breadth (GEO commands "
"are ZSETs with geohash scores — your leaderboard!), the loss-tolerance "
"argument shows judgment about what durability actually protects, and the "
"outbox mention preempts the dual-write follow-up interviewers love. If "
"pressed on scale: shard locations by city/geohash-prefix (consistent "
"hashing!), and note that 'near me' tolerates eventual consistency — "
"a 2s-stale driver dot is invisible to users."
                ),
            },
            {
                "question": (
"Your team wants to add Cassandra for an append-heavy events workload "
"currently straining Postgres. Argue both sides like a staff engineer, "
"then decide."
                ),
                "difficulty": "Hard",
                "topics": ["LSM vs B-tree", "operational cost", "decision-making"],
                "answer": (
"**For:** Cassandra's LSM engine turns random inserts into sequential "
"writes (memtable → flushed SSTables), sustaining write rates B-trees "
"can't; linear horizontal scaling; tunable consistency fits append-only "
"telemetry; no single-node ceiling. **Against:** an entirely new "
"operational skillset (compaction tuning, repairs, JVM), weak ad-hoc "
"query/join support pushes complexity into services, and the workload "
"might be servable by cheaper moves: Postgres partitioning by day + BRIN "
"indexes, batched COPY loading, or simply routing events to object "
"storage/parquet (the Stage-7 lakehouse) if reads are analytical. "
"**Decision frame:** if events are write-once-read-rarely-and-"
"analytically, the lake is the right sink, not Cassandra; if they need "
"low-latency keyed reads at massive write scale (device state), Cassandra "
"earns its cost. Most teams asking this question have the first workload — "
"so: exhaust Postgres+lake first, adopt Cassandra on measured need."
                ),
                "explanation": (
"Interviewers at staff level grade the *shape* of reasoning: name the "
"engine-level why (LSM write path vs B-tree write amplification — "
"under-the-hood knowledge earning its keep), price the operational cost "
"honestly, and — the differentiator — question whether the workload's READ "
"side even wants a database. The 'events are usually analytics' insight "
"reframes the whole problem toward the lakehouse, which is both often "
"correct and demonstrates architectural range. Ending with a reversible, "
"evidence-gated decision ('measure, then adopt') rather than a hot take "
"is exactly the tone senior loops reward."
                ),
            },
            {
                "question": (
"Explain the dual-write problem: your service writes an order to Postgres "
"then publishes an event to Kafka/Redis, and sometimes the second write "
"fails. Why are retries insufficient, and what is the outbox pattern?"
                ),
                "difficulty": "Medium",
                "topics": ["dual writes", "outbox pattern", "exactly-once"],
                "answer": (
"Two independent systems cannot be updated atomically — between the DB "
"commit and the publish, your process can crash, the broker can be down, "
"the network can fail. Retries don't close the gap: retry-until-success "
"can't distinguish 'publish failed' from 'publish succeeded but the ack "
"was lost' (risking duplicates), and a crash before any retry loses the "
"event entirely. **Outbox pattern:** write the order AND an event row "
"into an `outbox` table *in the same Postgres transaction* (atomic — both "
"or neither). A separate relay process reads the outbox and publishes, "
"marking rows sent; it retries freely because consumers deduplicate by "
"event id (idempotent consumption). Delivery guarantee becomes "
"at-least-once + idempotency = effectively-exactly-once."
                ),
                "explanation": (
"This is the distributed-systems question most likely to appear in a data "
"engineering loop, because pipelines ARE the consumers. The reasoning to "
"articulate: atomicity exists only within one system's transaction "
"boundary, so *move the second write inside it* (as data), then make "
"crossing the boundary retryable + deduplicatable. CDC tools (Debezium) "
"industrialize the relay by tailing the WAL — the same idea one level "
"down. And note the thread running through the whole curriculum: "
"at-least-once + idempotent handler (ww-3, oi-2) is the only "
"exactly-once that actually exists in practice — saying precisely that "
"sentence is an interview cheat code."
                ),
            },
        ],
    },
]
