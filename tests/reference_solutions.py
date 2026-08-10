"""
Reference solutions for every exercise across all stages — used by test_exercises.py
to prove each exercise's check_code passes a correct solution. (Not shipped to learners
inside the app; keep for maintenance.)

SQL exercises: the learner's editor is pre-filled with a seeded sqlite database
(the `_SEED` prefix), so reference solutions for those must include it too —
handled at the bottom of this file.
"""

from curriculum_sql import _SEED

SOLUTIONS = {
    # ---- Task Forge
    "tf-1": """
from dataclasses import dataclass, field

@dataclass
class Task:
    title: str
    done: bool = False
    tags: list = field(default_factory=list)

    def complete(self):
        self.done = True
        return self
""",
    "tf-2": """
class TaskNotFoundError(Exception):
    pass

class TaskStore:
    def __init__(self):
        self.tasks = []

    def add(self, title):
        self.tasks.append({'title': title, 'done': False})
        return len(self.tasks) - 1

    def complete(self, task_id):
        if not (0 <= task_id < len(self.tasks)):
            raise TaskNotFoundError(task_id)
        self.tasks[task_id]['done'] = True
""",
    "tf-3": """
import json

def to_json(tasks):
    return json.dumps(tasks)

def from_json(text):
    return json.loads(text)
""",
    # ---- Weather Watcher
    "ww-1": """
payload = {
    'latitude': -17.83,
    'current_weather': {
        'time': '2026-07-27T09:00',
        'temperature': 18.4,
        'windspeed': 11.2,
    },
}

def flatten(payload, city):
    cw = payload['current_weather']
    return {'city': city, 'time': cw['time'],
            'temperature': cw['temperature'], 'windspeed': cw['windspeed']}
""",
    "ww-2": """
def with_retry(fn, attempts=3):
    last = None
    for _ in range(attempts):
        try:
            return fn()
        except Exception as e:
            last = e
    raise last
""",
    "ww-3": """
import sqlite3

conn = sqlite3.connect(':memory:')
conn.execute('CREATE TABLE readings(city TEXT, time TEXT, temp REAL, UNIQUE(city, time))')

def upsert(conn, rows):
    conn.executemany(
        'INSERT INTO readings(city, time, temp) VALUES(?, ?, ?) '
        'ON CONFLICT(city, time) DO UPDATE SET temp=excluded.temp', rows)
    conn.commit()
""",
    # ---- LogMiner
    "lm-1": """
def numbers(lines):
    for line in lines:
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        yield int(s)
""",
    "lm-2": """
import re

PAT = re.compile(r'^(\\d+\\.\\d+\\.\\d+\\.\\d+) .*" (\\d{3}) (\\d+)$')

def parse(line):
    m = PAT.match(line)
    if not m:
        return None
    return {'ip': m.group(1), 'status': int(m.group(2)), 'bytes': int(m.group(3))}
""",
    "lm-3": """
from collections import Counter

def top_ips(rows, n):
    c = Counter(r['ip'] for r in rows)
    return c.most_common(n)
""",
    # ---- DataDeck
    "dd-1": """
from pydantic import BaseModel, Field, ValidationError

class Reading(BaseModel):
    city: str = Field(min_length=1)
    temperature: float = Field(ge=-90, le=60)
    time: str
""",
    "dd-2": """
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get('/cities/{name}')
def city(name: str):
    return {'city': name, 'len': len(name)}
""",
    "dd-3": """
import asyncio

async def gather_all(coros):
    return list(await asyncio.gather(*coros))
""",
    # ---- Pandas PowerPlant
    "pp-1": """
import numpy as np

fare = np.array([10.0, 20.0, 5.0, 8.0])
km = np.array([2.0, 4.0, 0.0, 2.0])

fare_per_km = np.where(km == 0, 0.0, fare / np.where(km == 0, 1.0, km))
""",
    "pp-2": """
import pandas as pd

trips = pd.DataFrame({
    'borough': ['Manhattan', 'Brooklyn', 'Manhattan', 'Queens', 'Brooklyn'],
    'fare':    [12.0,        8.0,        20.0,       5.0,      7.0],
})

result = trips.groupby('borough')['fare'].sum().sort_values(ascending=False)
""",
    "pp-3": """
import pandas as pd

trips = pd.DataFrame({'zone_id': [1, 2, 1, 3, 2, 1],
                      'fare': [10.0, 6.0, 4.0, 9.0, 3.0, 2.0]})
zones = pd.DataFrame({'zone_id': [1, 2, 3],
                      'borough': ['Manhattan', 'Brooklyn', 'Queens']})

merged = trips.merge(zones, on='zone_id', how='inner')
winner = merged.groupby('zone_id')['fare'].sum().idxmax()
""",
    # ---- First Spark
    "fs-1": """
def mini_spark(partitions, key_fn, agg_fn):
    # 1) map side: group within each partition
    mapped = []
    for part in partitions:
        groups = {}
        for rec in part:
            groups.setdefault(key_fn(rec), []).append(rec)
        mapped.append(groups)
    # 2) shuffle: merge across partitions
    shuffled = {}
    for groups in mapped:
        for k, vals in groups.items():
            shuffled.setdefault(k, []).extend(vals)
    # 3) reduce
    return {k: agg_fn(vs) for k, vs in shuffled.items()}
""",
    "fs-2": """
class LazyFrame:
    def __init__(self, data, steps=None):
        self.data = data
        self.steps = steps or []

    def filter(self, pred):
        return LazyFrame(self.data, self.steps + [('filter', pred)])

    def map(self, fn):
        return LazyFrame(self.data, self.steps + [('map', fn)])

    def collect(self):
        it = iter(self.data)
        for kind, fn in self.steps:
            # builtins bind fn immediately (a genexp here would hit the
            # classic late-binding closure bug and apply the wrong fn)
            it = filter(fn, it) if kind == 'filter' else map(fn, it)
        return list(it)
""",
    "fs-3": """
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = (SparkSession.builder.master('local[2]')
         .appName('exercise').getOrCreate())

trips = spark.createDataFrame(
    [('M', 10.0), ('B', 8.0), ('M', 20.0), ('Q', 5.0), ('B', 7.0)],
    ['borough', 'fare'])

rows = trips.groupBy('borough').agg(F.sum('fare').alias('total')).collect()
result = {r['borough']: r['total'] for r in rows}
""",
    # ---- Spark at Scale
    "ss-1": """
def partition_keys(keys, n):
    parts = [[] for _ in range(n)]
    for k in keys:
        parts[hash(k) % n].append(k)
    return parts

def skew_ratio(partitions):
    sizes = [len(p) for p in partitions]
    avg = sum(sizes) / len(sizes)
    return max(sizes) / avg
""",
    "ss-2": """
def broadcast_join(big_rows, small_table, key):
    index = {row[key]: row for row in small_table}
    out = []
    for row in big_rows:
        match = index.get(row[key])
        if match is not None:
            merged = dict(row)
            for k, v in match.items():
                if k != key:
                    merged[k] = v
            out.append(merged)
    return out
""",
    "ss-3": """
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = (SparkSession.builder.master('local[2]')
         .appName('catalyst').getOrCreate())

df = spark.createDataFrame(
    [(i, 'M' if i % 2 else 'B', float(i)) for i in range(100)],
    ['id', 'borough', 'fare'])

q = df.select('borough', 'fare').filter(F.col('fare') > 50)

plan = df._jdf.queryExecution().executedPlan().toString()
plan = q._jdf.queryExecution().executedPlan().toString()
pushed = 'Filter' in plan
print(plan)
""",
    # ---- Orchestrate It
    "oi-1": """
def topo_order(deps):
    order, state = [], {}
    def visit(t):
        if state.get(t) == 1:
            raise ValueError('cycle')
        if state.get(t) == 2:
            return
        state[t] = 1
        for up in deps.get(t, []):
            visit(up)
        state[t] = 2
        order.append(t)
    for t in deps:
        visit(t)
    return order
""",
    "oi-2": """
def run_task(fn, retries=2):
    states = []
    for attempt in range(retries + 1):
        states.append('running')
        try:
            fn()
            states.append('success')
            return states
        except Exception:
            if attempt < retries:
                states.append('up_for_retry')
            else:
                states.append('failed')
    return states
""",
    "oi-3": """
def topo(deps):
    order, state = [], {}
    def visit(t):
        if state.get(t) == 1:
            raise ValueError('cycle')
        if state.get(t) == 2:
            return
        state[t] = 1
        for up in deps.get(t, []):
            visit(up)
        state[t] = 2
        order.append(t)
    for t in deps:
        visit(t)
    return order

def run_dag(deps, fns):
    states = {}
    for task in topo(deps):
        ups = deps.get(task, [])
        if any(states.get(u) in ('failed', 'upstream_failed') for u in ups):
            states[task] = 'upstream_failed'
            continue
        try:
            fns[task]()
            states[task] = 'success'
        except Exception:
            states[task] = 'failed'
    return states
""",

    # ================= Stage 2: Structly
    "st-1": """
def two_sum(nums, target):
    seen = {}
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
    return None
""",
    "st-2": """
def group_anagrams(words):
    groups = {}
    for w in words:
        groups.setdefault(''.join(sorted(w)), []).append(w)
    return list(groups.values())
""",
    "st-3": """
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.od = OrderedDict()

    def get(self, key):
        if key not in self.od:
            return -1
        self.od.move_to_end(key)
        return self.od[key]

    def put(self, key, value):
        if key in self.od:
            self.od[key] = value
            self.od.move_to_end(key)
            return
        self.od[key] = value
        if len(self.od) > self.capacity:
            self.od.popitem(last=False)
""",
    # ================= Stage 2: Algo Gym
    "ag-1": """
def merge_sorted(a, b):
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            out.append(a[i]); i += 1
        else:
            out.append(b[j]); j += 1
    out.extend(a[i:])
    out.extend(b[j:])
    return out
""",
    "ag-2": """
def count_sessions(timestamps, gap):
    if not timestamps:
        return 0
    sessions = 1
    for prev, curr in zip(timestamps, timestamps[1:]):
        if curr - prev > gap:
            sessions += 1
    return sessions
""",
    "ag-3": """
def first_at_or_after(ts, t):
    lo, hi = 0, len(ts)
    while lo < hi:
        mid = (lo + hi) // 2
        if ts[mid] < t:
            lo = mid + 1
        else:
            hi = mid
    return lo
""",
    # ================= Stage 2: Heap & Stream
    "hs-1": """
import heapq

def top_k_stream(pairs, k):
    heap = []
    for item, score in pairs:
        if len(heap) < k:
            heapq.heappush(heap, (score, item))
        elif score > heap[0][0]:
            heapq.heapreplace(heap, (score, item))
    return [item for score, item in sorted(heap, key=lambda t: t[0], reverse=True)]
""",
    "hs-2": """
import heapq

class RunningMedian:
    def __init__(self):
        self.lo = []
        self.hi = []

    def add(self, x):
        heapq.heappush(self.lo, -x)
        heapq.heappush(self.hi, -heapq.heappop(self.lo))
        if len(self.hi) > len(self.lo):
            heapq.heappush(self.lo, -heapq.heappop(self.hi))

    def median(self):
        if len(self.lo) > len(self.hi):
            return -self.lo[0]
        return (-self.lo[0] + self.hi[0]) / 2
""",
    "hs-3": """
def reservoir_sample(stream, k, rng):
    reservoir = []
    for i, x in enumerate(stream, 1):
        if i <= k:
            reservoir.append(x)
        else:
            j = rng.randrange(i)
            if j < k:
                reservoir[j] = x
    return reservoir
""",
    # ================= Stage 3: SQL Foundry (sql string exercises)
    "sf-1": """
sql = '''
SELECT c.country, SUM(oi.quantity * oi.unit_price) AS revenue
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.status = 'completed'
GROUP BY c.country
ORDER BY revenue DESC
'''
""",
    "sf-2": """
sql = '''
SELECT c.name
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL
ORDER BY c.name
'''
""",
    "sf-3": """
sql = '''
WITH spend AS (
    SELECT c.country AS country, c.name AS name,
           SUM(oi.quantity * oi.unit_price) AS spend
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE o.status = 'completed'
    GROUP BY c.country, c.name
)
SELECT s.country, s.name, s.spend
FROM spend s
WHERE s.spend = (SELECT MAX(s2.spend) FROM spend s2 WHERE s2.country = s.country)
ORDER BY s.country
'''
""",
    # ================= Stage 3: Window Works
    "wf-1": """
sql = '''
WITH spend AS (
    SELECT c.country AS country, c.name AS name,
           SUM(oi.quantity * oi.unit_price) AS spend
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE o.status = 'completed'
    GROUP BY c.country, c.name
),
ranked AS (
    SELECT country, name, spend,
           ROW_NUMBER() OVER (PARTITION BY country ORDER BY spend DESC) AS rn
    FROM spend
)
SELECT country, name, spend FROM ranked
WHERE rn <= 2
ORDER BY country, spend DESC
'''
""",
    "wf-2": """
sql = '''
WITH monthly AS (
    SELECT strftime('%Y-%m', o.order_date) AS month,
           SUM(oi.quantity * oi.unit_price) AS revenue
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    WHERE o.status = 'completed'
    GROUP BY month
)
SELECT month, revenue,
       LAG(revenue) OVER (ORDER BY month) AS prev_revenue
FROM monthly
ORDER BY month
'''
""",
    "wf-3": """
import sqlite3
conn = sqlite3.connect(':memory:')
conn.executescript('''
CREATE TABLE events(user_id TEXT, ts INT);
INSERT INTO events VALUES
 ('u1',0),('u1',10),('u1',20),('u1',100),('u1',105),
 ('u2',0),('u2',40),('u2',50);
''')

sql = '''
WITH flagged AS (
    SELECT user_id, ts,
           CASE WHEN LAG(ts) OVER (PARTITION BY user_id ORDER BY ts) IS NULL
                     OR ts - LAG(ts) OVER (PARTITION BY user_id ORDER BY ts) > 30
                THEN 1 ELSE 0 END AS new_session
    FROM events
),
sessions AS (
    SELECT user_id, ts,
           SUM(new_session) OVER (PARTITION BY user_id ORDER BY ts) AS session_id
    FROM flagged
)
SELECT user_id, session_id, MIN(ts) AS session_start, COUNT(*) AS events
FROM sessions
GROUP BY user_id, session_id
ORDER BY user_id, session_id
'''
""",
    # ================= Stage 3: PG Warehouse
    "pw-1": """
import math

def should_use_index(total_rows, matching_rows, row_cost=1.0, index_cost=3.0):
    if total_rows <= 0:
        return False
    seq = total_rows * row_cost
    idx = math.log2(max(total_rows, 2)) * index_cost + matching_rows * row_cost * 2
    return idx < seq

def selectivity_verdict(total, matching):
    return 'index' if should_use_index(total, matching) else 'seq_scan'
""",
    "pw-2": """
def transfer(accounts, frm, to, amount):
    if frm not in accounts:
        raise KeyError(frm)
    if to not in accounts:
        raise KeyError(to)
    if accounts[frm] < amount:
        raise ValueError('insufficient funds')
    accounts[frm] -= amount
    accounts[to] += amount
""",
    "pw-3": """
import sqlite3, math

conn = sqlite3.connect(':memory:')
conn.execute('CREATE TABLE t(id INT, val TEXT)')

def load_rows(conn, rows, batch_size):
    batches = 0
    for i in range(0, len(rows), batch_size):
        conn.executemany('INSERT INTO t VALUES (?, ?)', rows[i:i + batch_size])
        conn.commit()
        batches += 1
    return batches

def estimate_cost(n_rows, per_stmt_overhead, per_row_cost, batch_size):
    return math.ceil(n_rows / batch_size) * per_stmt_overhead + n_rows * per_row_cost
""",
    # ================= Stage 3: Star Schema
    "sc-1": """
from collections import Counter

def validate_grain(rows, grain_keys):
    counts = Counter(tuple(r[k] for k in grain_keys) for r in rows)
    return [k for k, c in counts.items() if c > 1]

def safe_to_sum(rows, grain_keys, measure):
    if validate_grain(rows, grain_keys):
        return False
    for r in rows:
        v = r.get(measure)
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            return False
    return True
""",
    "sc-2": """
def scd2_apply(dim, updates, today):
    for u in updates:
        current = next((r for r in dim
                        if r['natural_key'] == u['natural_key'] and r['is_current']), None)
        if current is None:
            dim.append({'natural_key': u['natural_key'], 'attrs': u['attrs'],
                        'valid_from': today, 'valid_to': None, 'is_current': True})
        elif current['attrs'] == u['attrs']:
            continue
        else:
            current['valid_to'] = today
            current['is_current'] = False
            dim.append({'natural_key': u['natural_key'], 'attrs': u['attrs'],
                        'valid_from': today, 'valid_to': None, 'is_current': True})
    return dim
""",
    # ================= Stage 3: Migration Master
    "mm-1": """
import sqlite3

conn = sqlite3.connect(':memory:')

def apply_migrations(conn, migrations):
    conn.execute('CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY)')
    done = {r[0] for r in conn.execute('SELECT version FROM schema_migrations')}
    applied = []
    for version, sql in sorted(migrations):
        if version in done:
            continue
        conn.executescript(sql)
        conn.execute('INSERT INTO schema_migrations VALUES (?)', (version,))
        conn.commit()
        applied.append(version)
    return applied
""",
    "mm-2": """
import sqlite3

conn = sqlite3.connect(':memory:')
conn.execute('CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT, email TEXT)')
conn.executemany('INSERT INTO users(name) VALUES (?)',
                 [(f'user{i}',) for i in range(10)])

def backfill(conn, batch_size, compute_fn):
    batches = 0
    while True:
        rows = conn.execute(
            'SELECT id, name FROM users WHERE email IS NULL ORDER BY id LIMIT ?',
            (batch_size,)).fetchall()
        if not rows:
            return batches
        for id_, name in rows:
            conn.execute('UPDATE users SET email = ? WHERE id = ?', (compute_fn(name), id_))
        conn.commit()
        batches += 1
""",
    # ================= Stage 4: DocStore
    "ds-1": """
def aggregate(docs, pipeline):
    for stage in pipeline:
        (name, spec), = stage.items()
        if name == '$match':
            docs = [d for d in docs if all(d.get(k) == v for k, v in spec.items())]
        elif name == '$group':
            key_field = spec['_id'][1:]
            accs = {k: v for k, v in spec.items() if k != '_id'}
            groups = {}
            for d in docs:
                key = d.get(key_field)
                g = groups.setdefault(key, {'_id': key, **{k: 0 for k in accs}})
                for out_name, acc in accs.items():
                    (op, operand), = acc.items()
                    if op == '$sum':
                        if isinstance(operand, str) and operand.startswith('$'):
                            g[out_name] += d.get(operand[1:], 0)
                        else:
                            g[out_name] += operand
            docs = list(groups.values())
        elif name == '$sort':
            (field, direction), = spec.items()
            docs = sorted(docs, key=lambda d: d[field], reverse=direction == -1)
    return docs
""",
    "ds-2": """
def recommend_model(relation):
    if relation['child_shared_across_parents'] or relation['child_count'] == 'unbounded':
        return 'reference'
    if relation['child_updated_independently'] and relation['read_together']:
        return 'hybrid'
    if relation['read_together'] and relation['child_count'] in ('few', 'many'):
        return 'embed'
    return 'reference'
""",
    "ds-3": """
def avg_aspect_scores(reviews):
    sums, counts = {}, {}
    for r in reviews:
        for a in r.get('aspects', []):
            sums[a['name']] = sums.get(a['name'], 0) + a['score']
            counts[a['name']] = counts.get(a['name'], 0) + 1
    return {k: sums[k] / counts[k] for k in sums}
""",
    # ================= Stage 4: Cache Money
    "cm-1": """
class TTLCache:
    def __init__(self, ttl):
        self.ttl = ttl
        self.store = {}

    def get(self, key, now):
        if key not in self.store:
            return None
        value, stored_at = self.store[key]
        if now - stored_at >= self.ttl:
            return None
        return value

    def set(self, key, value, now):
        self.store[key] = (value, now)

def cached_fetch(cache, key, now, fetch_fn):
    val = cache.get(key, now)
    if val is not None:
        return val
    val = fetch_fn()
    cache.set(key, val, now)
    return val
""",
    "cm-2": """
class RateLimiter:
    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.hits = {}

    def allow(self, user, now):
        ts = self.hits.setdefault(user, [])
        ts[:] = [t for t in ts if t > now - self.window]
        if len(ts) < self.limit:
            ts.append(now)
            return True
        return False
""",
    "cm-3": """
class Leaderboard:
    def __init__(self):
        self.scores = {}

    def _sorted(self):
        return sorted(self.scores.items(), key=lambda kv: (-kv[1], kv[0]))

    def upsert(self, member, score):
        self.scores[member] = score

    def top(self, n):
        return self._sorted()[:n]

    def rank(self, member):
        if member not in self.scores:
            return None
        for i, (m, _) in enumerate(self._sorted()):
            if m == member:
                return i
        return None

    def count_in_range(self, lo, hi):
        return sum(1 for s in self.scores.values() if lo <= s <= hi)
""",
    # ================= Stage 4: Polyglot
    "pg-1": """
import bisect
import hashlib

def stable_hash(s):
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)

class HashRing:
    def __init__(self, nodes, vnodes=100):
        self.vnodes = vnodes
        self.ring = []
        for n in nodes:
            self.add_node(n)

    def add_node(self, name):
        for i in range(self.vnodes):
            bisect.insort(self.ring, (stable_hash(f'{name}:{i}'), name))

    def remove_node(self, name):
        self.ring = [entry for entry in self.ring if entry[1] != name]

    def get_node(self, key):
        if not self.ring:
            return None
        i = bisect.bisect(self.ring, (stable_hash(key),))
        return self.ring[i % len(self.ring)][1]
""",
    "pg-2": """
def choose_store(workload):
    if workload['pattern'] == 'cache' or workload['unit'] == 'key_value':
        return 'redis'
    if workload['unit'] == 'vector':
        return 'postgres+pgvector'
    if workload['relationships'] or (workload['consistency'] == 'strong'
                                     and workload['pattern'] == 'transactional'):
        return 'postgres'
    if workload['unit'] == 'document' and workload['consistency'] == 'eventual':
        return 'mongo'
    if workload['pattern'] == 'analytical':
        return 'postgres'
    return 'postgres'
""",
    "pg-3": """
class QuorumStore:
    def __init__(self, n):
        self.replicas = [{} for _ in range(n)]
        self.version = 0

    def write(self, key, value, w):
        self.version += 1
        for rep in self.replicas[:w]:
            rep[key] = (value, self.version)
        return self.version

    def read(self, key, r):
        hits = [rep[key] for rep in self.replicas[:r] if key in rep]
        if not hits:
            return None
        return max(hits, key=lambda t: t[1])[0]
""",
    # ================= Stage 5: Cleanroom
    "cr-1": """
from datetime import datetime

def parse_money(s):
    if s is None:
        return None
    if isinstance(s, (int, float)) and not isinstance(s, bool):
        return float(s)
    t = str(s).strip().lstrip('$').replace(',', '')
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        return None

def parse_date_any(s):
    if not isinstance(s, str):
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m-%d-%Y'):
        try:
            return datetime.strptime(s.strip(), fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None
""",
    "cr-2": """
import pandas as pd
import numpy as np

def clean_missing(df):
    report = {}
    keyed = df[df['email'].notna()].copy()
    report['rows_dropped'] = len(df) - len(keyed)
    report['age_filled'] = int(keyed['age'].isna().sum())
    keyed['age'] = keyed['age'].fillna(keyed['age'].median())
    report['country_filled'] = int(keyed['country'].isna().sum())
    keyed['country'] = keyed['country'].fillna('unknown')
    keyed = keyed.reset_index(drop=True)
    return keyed, report
""",
    # ================= Stage 5: DuckDB Turbo
    "dt-1": """
import duckdb
import pandas as pd

trips = pd.DataFrame({
    'borough': ['M', 'B', 'M', 'Q', 'B', 'M'],
    'fare':    [10.0, 8.0, 20.0, 5.0, 7.0, 2.0],
})

result = duckdb.sql('''
    SELECT borough, SUM(fare) AS total
    FROM trips
    GROUP BY borough
    ORDER BY total DESC
''').df()
""",
    "dt-2": """
def rows_scanned_estimate(row_groups, predicate_min, predicate_max):
    scanned = sum(g['rows'] for g in row_groups
                  if g['min'] <= predicate_max and predicate_min <= g['max'])
    total = sum(g['rows'] for g in row_groups)
    return (scanned, total)
""",
    # ================= Stage 5: Feature Foundry
    "ff-1": """
from datetime import date

def rfm_features(orders, snapshot):
    snap = date.fromisoformat(snapshot)
    out = {}
    for o in orders:
        d = date.fromisoformat(o['order_date'])
        if d >= snap:
            continue
        cid = o['customer_id']
        f = out.setdefault(cid, {'last': d, 'frequency': 0, 'monetary': 0.0})
        f['frequency'] += 1
        f['monetary'] += o['amount']
        if d > f['last']:
            f['last'] = d
    return {cid: {'recency_days': (snap - f['last']).days,
                  'frequency': f['frequency'],
                  'monetary': f['monetary']}
            for cid, f in out.items()}
""",
    "ff-2": """
import math

class Scaler:
    def __init__(self):
        self.mean = None
        self.std = None

    def fit(self, values):
        n = len(values)
        self.mean = sum(values) / n
        self.std = math.sqrt(sum((x - self.mean) ** 2 for x in values) / n)
        return self

    def transform(self, values):
        if self.mean is None:
            raise RuntimeError('fit before transform')
        if self.std == 0:
            return [0.0 for _ in values]
        return [(x - self.mean) / self.std for x in values]

def safe_split_scale(train, test):
    s = Scaler()
    s.fit(train)
    return s.transform(train), s.transform(test)
""",
    # ================= Stage 6: Pipeline Blueprint
    "pb-1": """
def run_pipeline(extract, transforms, load, batch_size=2):
    report = {'read': 0, 'filtered': 0, 'loaded': 0, 'batches': 0}
    batch = []
    for record in extract:
        report['read'] += 1
        for t in transforms:
            record = t(record)
            if record is None:
                report['filtered'] += 1
                break
        else:
            batch.append(record)
            if len(batch) >= batch_size:
                load(batch)
                report['loaded'] += len(batch)
                report['batches'] += 1
                batch = []
    if batch:
        load(batch)
        report['loaded'] += len(batch)
        report['batches'] += 1
    return report
""",
    "pb-2": """
def run_with_dlq(records, transform, load, dead_letter):
    ok = []
    for r in records:
        try:
            ok.append(transform(r))
        except Exception as e:
            dead_letter.append({'record': r, 'error': str(e)})
    load(ok)
    return {'ok': len(ok), 'dead': len(dead_letter)}
""",
    "pb-3": """
def build_pipeline(config, registry):
    src = dict(config['source'])
    kind = src.pop('type')
    if kind not in registry:
        raise ValueError(f'unknown source type: {kind}')
    source = registry[kind](**src)

    transforms = []
    for name in config['transforms']:
        if name not in registry:
            raise ValueError(f'unknown transform: {name}')
        transforms.append(registry[name])

    snk = dict(config['sink'])
    skind = snk.pop('type')
    if skind not in registry:
        raise ValueError(f'unknown sink type: {skind}')
    sink = registry[skind](**snk)

    return {'source': source, 'transforms': transforms, 'sink': sink}
""",
    # ================= Stage 6: CDC Lite
    "cl-1": """
def sync(source_rows, state, load):
    wm = state.get('watermark', float('-inf'))
    new = sorted((r for r in source_rows if r['ts'] > wm), key=lambda r: r['ts'])
    if not new:
        return 0
    load(new)
    state['watermark'] = new[-1]['ts']
    return len(new)
""",
    "cl-2": """
def sync_with_overlap(source_rows, state, load, overlap):
    wm = state.get('watermark', float('-inf'))
    seen = state.setdefault('seen_ids', set())
    lower = wm - overlap if wm != float('-inf') else float('-inf')
    new = sorted((r for r in source_rows
                  if r['ts'] > lower and r['id'] not in seen),
                 key=lambda r: r['ts'])
    if not new:
        return 0
    load(new)
    seen.update(r['id'] for r in new)
    highest = max(r['ts'] for r in new)
    state['watermark'] = highest if wm == float('-inf') else max(wm, highest)
    return len(new)
""",
    # ================= Stage 6: Quality Gate
    "qg-1": """
from collections import Counter

def run_checks(rows, checks):
    results = []
    for spec in checks:
        t = spec['type']
        col = spec['column']
        if t == 'not_null':
            v = sum(1 for r in rows if r.get(col) is None)
        elif t == 'unique':
            counts = Counter(r.get(col) for r in rows if r.get(col) is not None)
            v = sum(c - 1 for c in counts.values() if c > 1)
        elif t == 'range':
            v = 0
            for r in rows:
                val = r.get(col)
                if val is None:
                    continue
                if not isinstance(val, (int, float)) or isinstance(val, bool):
                    v += 1
                elif not (spec['min'] <= val <= spec['max']):
                    v += 1
        else:
            v = 0
        results.append({'check': spec, 'passed': v == 0, 'violations': v})
    return results
""",
    "qg-2": """
import math

def is_anomalous(history, current, sigmas=3.0):
    if len(history) < 3:
        return False
    m = sum(history) / len(history)
    s = math.sqrt(sum((x - m) ** 2 for x in history) / len(history))
    if s == 0:
        return current != m
    return abs(current - m) > sigmas * s

def check_run(history, current):
    if len(history) < 3:
        return {'anomalous': False, 'mean': None, 'std': None}
    m = sum(history) / len(history)
    s = math.sqrt(sum((x - m) ** 2 for x in history) / len(history))
    return {'anomalous': is_anomalous(history, current), 'mean': m, 'std': s}
""",
    # ================= Stage 6: Stream Simulator
    "sm-1": """
def consume(log, state, process, commit_first):
    offset = state.get('offset', 0)
    processed = 0
    while offset < len(log):
        record = log[offset]
        if commit_first:
            state['offset'] = offset + 1
            try:
                process(record)
            except Exception:
                return {'processed': processed, 'offset': state['offset']}
            processed += 1
        else:
            try:
                process(record)
            except Exception:
                state['offset'] = offset
                return {'processed': processed, 'offset': offset}
            processed += 1
            state['offset'] = offset + 1
        offset += 1
    state.setdefault('offset', offset)
    return {'processed': processed, 'offset': state['offset']}
""",
    "sm-2": """
def window_count(events, size, lateness):
    counts = {}
    dropped = 0
    watermark = float('-inf')
    for ts, key in events:
        start = (ts // size) * size
        if watermark >= start + size + lateness:
            dropped += 1
        else:
            counts[(start, key)] = counts.get((start, key), 0) + 1
        watermark = max(watermark, ts)
    return counts, dropped
""",
    # ================= Stage 7: Lakehouse Lite
    "ll-1": """
def plan_work(bronze_partitions, silver_state):
    return sorted(d for d, file_ts in bronze_partitions.items()
                  if d not in silver_state or file_ts > silver_state[d])
""",
    "ll-2": """
def merge_into(target, updates, key):
    pos = {row[key]: i for i, row in enumerate(target)}
    updated = inserted = 0
    for u in updates:
        k = u[key]
        if k in pos:
            target[pos[k]] = u
            updated += 1
        else:
            pos[k] = len(target)
            target.append(u)
            inserted += 1
    return updated, inserted
""",
    # ================= Stage 8: Airflow Pro
    "ap-1": """
def run_mapped(items, task_fn, max_active=4):
    results = []
    for start in range(0, len(items), max_active):
        for item in items[start:start + max_active]:
            try:
                results.append(('ok', task_fn(item)))
            except Exception as e:
                results.append(('failed', str(e)))
    return results
""",
    "ap-2": """
def sensor_wait(check_fn, timeout, poke_interval, clock):
    pokes = 0
    while True:
        pokes += 1
        try:
            ok = check_fn()
        except Exception:
            ok = False
        if ok:
            return {'found': True, 'pokes': pokes, 'waited': clock['t']}
        if clock['t'] + poke_interval > timeout:
            return {'found': False, 'pokes': pokes, 'waited': clock['t']}
        clock['t'] += poke_interval
""",
    # ================= Stage 9: DS Primer
    "dp-1": """
def percentile(sorted_vals, q):
    idx = q * (len(sorted_vals) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = idx - lo
    return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])

def describe_robust(values):
    if not values:
        raise ValueError('empty input')
    s = sorted(values)
    return {
        'mean': sum(s) / len(s),
        'median': percentile(s, 0.5),
        'p95': percentile(s, 0.95),
        'iqr': percentile(s, 0.75) - percentile(s, 0.25),
    }
""",
    "dp-2": """
def simpson_check(groups):
    winners = {}
    tot_xa = tot_na = tot_xb = tot_nb = 0
    for name, (xa, na, xb, nb) in groups.items():
        winners[name] = 'A' if xa / na > xb / nb else 'B'
        tot_xa += xa; tot_na += na; tot_xb += xb; tot_nb += nb
    agg = 'A' if tot_xa / tot_na > tot_xb / tot_nb else 'B'
    uniq = set(winners.values())
    paradox = len(uniq) == 1 and next(iter(uniq)) != agg
    return {'aggregate_winner': agg, 'group_winners': winners, 'paradox': paradox}
""",
    # ================= Stage 9: Model Factory
    "mf-1": """
def confusion(y_true, y_pred):
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    return {'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn}

def metrics(y_true, y_pred):
    c = confusion(y_true, y_pred)
    total = len(y_true)
    accuracy = (c['tp'] + c['tn']) / total if total else 0.0
    precision = c['tp'] / (c['tp'] + c['fp']) if (c['tp'] + c['fp']) else 0.0
    recall = c['tp'] / (c['tp'] + c['fn']) if (c['tp'] + c['fn']) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {'accuracy': accuracy, 'precision': precision, 'recall': recall, 'f1': f1}
""",
    "mf-2": """
def time_series_splits(n_samples, n_splits):
    base, rem = divmod(n_samples, n_splits + 1)
    sizes = [base + (1 if i < rem else 0) for i in range(n_splits + 1)]
    bounds = []
    acc = 0
    for s in sizes:
        acc += s
        bounds.append(acc)
    out = []
    for k in range(n_splits):
        train_end = bounds[k]
        test_end = bounds[k + 1]
        out.append((list(range(train_end)), list(range(train_end, test_end))))
    return out
""",
    # ================= Stage 9: Vector Vault
    "vv-1": """
import math

def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)

def top_k(query, corpus, k):
    scored = [(doc, round(cosine(query, vec), 6)) for doc, vec in corpus.items()]
    scored.sort(key=lambda t: (-t[1], t[0]))
    return scored[:k]
""",
    "vv-2": """
def chunk_text(text, size, overlap):
    if overlap >= size:
        raise ValueError('overlap must be smaller than size')
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            space = text.rfind(' ', start, end)
            if space > start:
                end = space
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks
""",
    # ================= Stage 9: LLM Pipeline
    "lp-1": """
import json

ALLOWED = ('positive', 'negative', 'neutral')

def _parse(text):
    t = text.strip()
    if t.startswith('```'):
        t = t.split('\\n', 1)[1].rsplit('```', 1)[0]
    data = json.loads(t)
    s = data['sentiment']
    if s not in ALLOWED:
        raise ValueError(f'bad value: {s}')
    return s

def extract_sentiment(review, llm, max_repairs=1):
    prompt = f'Classify the sentiment of this review as JSON {{"sentiment": ...}}: {review}'
    attempts = 0
    while True:
        response = llm(prompt)
        try:
            return _parse(response)
        except Exception as e:
            attempts += 1
            if attempts > max_repairs:
                return None
            prompt = (f'Your previous response was invalid.\\n'
                      f'Previous response: {response}\\n'
                      f'Error: {e}\\n'
                      f'Return ONLY valid JSON {{"sentiment": "positive"|"negative"|"neutral"}} '
                      f'for review: {review}')
""",
    "lp-2": """
def enrich_batch(records, llm, cache, price_per_1k_tokens=0.5):
    results = {}
    calls = hits = tokens = 0
    for rec in records:
        prompt = f"classify: {rec['text']}"
        if prompt in cache:
            hits += 1
        else:
            resp = llm(prompt)
            cache[prompt] = resp
            tokens += len(prompt) // 4 + len(resp) // 4
            calls += 1
        results[rec['id']] = cache[prompt]
    return {'results': results, 'calls': calls, 'cache_hits': hits,
            'tokens': tokens, 'cost': tokens / 1000 * price_per_1k_tokens}
""",
    # ================= Stage 9: RAG Works
    "rw-1": """
def recall_at_k(retrieved, relevant, k):
    if not relevant:
        return 1.0
    return len(set(retrieved[:k]) & set(relevant)) / len(relevant)

def mrr(all_retrieved, all_relevant):
    total = 0.0
    for retrieved, relevant in zip(all_retrieved, all_relevant):
        rr = 0.0
        for i, doc in enumerate(retrieved, 1):
            if doc in relevant:
                rr = 1 / i
                break
        total += rr
    return total / len(all_retrieved) if all_retrieved else 0.0

def evaluate(runs):
    recalls = [recall_at_k(r['retrieved'], r['relevant'], 5) for r in runs]
    m = mrr([r['retrieved'] for r in runs], [r['relevant'] for r in runs])
    return {'recall@5': sum(recalls) / len(recalls) if recalls else 0.0, 'mrr': m}
""",
    "rw-2": """
def rrf(rankings, k=60):
    scores = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, 1):
            scores[doc] = scores.get(doc, 0.0) + 1 / (k + rank)
    return sorted(scores, key=lambda d: (-scores[d], d))
""",
    # ================= Stage 10: Grand Central
    "gc-1": """
DEPS = {
    'ingest_events': [],
    'ingest_reviews': [],
    'quality_gate': ['ingest_events', 'ingest_reviews'],
    'silver': ['quality_gate'],
    'gold': ['silver'],
    'sync_warehouse': ['gold'],
    'llm_enrich': ['ingest_reviews'],
    'embed_chunks': ['llm_enrich'],
    'serve_refresh': ['sync_warehouse', 'embed_chunks'],
}

def _topo(deps):
    order, state = [], {}
    def visit(t):
        if state.get(t) == 1:
            raise ValueError('cycle')
        if state.get(t) == 2:
            return
        state[t] = 1
        for up in deps.get(t, []):
            visit(up)
        state[t] = 2
        order.append(t)
    for t in deps:
        visit(t)
    return order

def run_platform(fns):
    states = {}
    for task in _topo(DEPS):
        ups = DEPS.get(task, [])
        if any(states.get(u) in ('failed', 'upstream_failed') for u in ups):
            states[task] = 'upstream_failed'
            continue
        try:
            fns[task]()
            states[task] = 'success'
        except Exception:
            states[task] = 'failed'
    return states
""",
}

# SQL exercises need the seeded connection the starter code provides.
for _sql_ex in ('sf-1', 'sf-2', 'sf-3', 'wf-1', 'wf-2'):
    SOLUTIONS[_sql_ex] = _SEED + SOLUTIONS[_sql_ex]
