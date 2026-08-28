"""
Stage 3 — Relational Databases & SQL Mastery (5 projects).

In-app SQL exercises run against seeded SQLite (same SQL concepts, instant
feedback); project milestones run against the real Postgres warehouse service
(docker compose --profile db up -d), which is REUSED by the ETL, Spark and AI
stages — the data layer of the whole curriculum.
"""

# Shared SQLite seed used by SQL exercises: a mini version of the warehouse.
_SEED = '''
import sqlite3
conn = sqlite3.connect(':memory:')
conn.executescript("""
CREATE TABLE customers(customer_id INTEGER PRIMARY KEY, name TEXT, country TEXT);
CREATE TABLE orders(order_id INTEGER PRIMARY KEY, customer_id INT, order_date TEXT, status TEXT);
CREATE TABLE order_items(order_id INT, product_id INT, quantity INT, unit_price REAL);
CREATE TABLE products(product_id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL);
INSERT INTO customers VALUES
 (1,'ada','ZW'),(2,'bo','ZA'),(3,'chi','ZW'),(4,'dee','US'),(5,'ed','ZA');
INSERT INTO products VALUES
 (1,'laptop','electronics',1000),(2,'novel','books',20),
 (3,'shirt','clothing',30),(4,'phone','electronics',600);
INSERT INTO orders VALUES
 (10,1,'2026-01-05','completed'),(11,1,'2026-02-10','completed'),
 (12,2,'2026-01-20','cancelled'),(13,3,'2026-03-01','completed'),
 (14,4,'2026-03-15','completed'),(15,1,'2026-03-20','returned'),
 (16,5,'2026-04-02','completed');
INSERT INTO order_items VALUES
 (10,1,1,1000),(10,2,2,20),(11,4,1,600),(12,3,3,30),
 (13,2,5,20),(14,1,1,1000),(14,4,1,600),(15,3,1,30),(16,2,1,20);
""")
'''

STAGE3_PROJECTS = [
    # ------------------------------------------------------------------
    {
        "id": "sql-foundry",
        "title": "SQL Foundry",
        "tagline": "Joins, aggregates, subqueries — the interview SQL core",
        "level": "Intermediate",
        "tech": ["SQL", "JOINs", "GROUP BY/HAVING", "subqueries", "NULL logic"],
        "est_hours": 6,
        "brief": (
            "SQL is half of every data-engineering interview. Master the core on a "
            "realistic e-commerce schema: multi-table joins, aggregation with "
            "HAVING, subqueries vs joins, and the NULL traps that fail candidates. "
            "In-app exercises give instant feedback on real queries; milestones run "
            "the same ideas against the live Postgres warehouse (start it with the "
            "Environment command — it seeds itself with 500 customers / 5000 orders "
            "automatically)."
        ),
        "milestones": [
            "Connect to the warehouse from Jupyter (psycopg2, host='warehouse', user/password 'dataforged', db 'warehouse') and explore the schema with \\d-style queries against information_schema.",
            "Revenue questions: total revenue per country; per category; top-10 customers by lifetime spend (joins across all four tables).",
            "HAVING practice: categories with revenue > 10,000; customers with 3+ completed orders.",
            "Find customers who never ordered (LEFT JOIN ... IS NULL, then rewrite with NOT EXISTS — compare plans with EXPLAIN).",
            "The NULL gauntlet: demonstrate that COUNT(col) skips NULLs, that 'x <> NULL' matches nothing, and fix both with COUNT(*), IS NULL and COALESCE.",
        ],
        "under_the_hood": (
            "**Declarative means the planner decides.** You state WHAT; the "
            "database picks HOW: join order, join algorithm (nested loop / hash / "
            "merge — the same algorithms you built in Algo Gym and Spark at Scale!), "
            "index usage. EXPLAIN shows the chosen plan — learning to read it is "
            "Project 10's job.\n\n"
            "**Logical query order** explains most beginner confusion: FROM/JOIN → "
            "WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT. That's why "
            "WHERE can't see aggregates (HAVING exists) and why column aliases "
            "defined in SELECT aren't visible in WHERE.\n\n"
            "**NULL is three-valued logic.** NULL = 'unknown': any comparison with "
            "it yields UNKNOWN, which WHERE treats as false. NOT IN with a NULL in "
            "the subquery returns zero rows — the single most infamous SQL trap. "
            "Aggregates skip NULLs (COUNT(col) vs COUNT(*)). Interviews bait these "
            "constantly; production data feeds them daily."
        ),
        "exercises": [
            {
                "id": "sf-1",
                "title": "Revenue per country (the join chain)",
                "instructions": (
"The bread-and-butter query shape: fact→dim joins plus aggregation.\n\n**Your "
"task**\n\nAgainst the seeded mini-warehouse (schema shown in the starter), write "
"`sql` computing **total revenue per customer country, for completed orders "
"only**, as columns `(country, revenue)` ordered by revenue descending. Revenue = "
"SUM(quantity * unit_price), joining order_items → orders → customers."
                ),
                "starter_code": _SEED + (
"\n# Schema: customers(customer_id,name,country) orders(order_id,customer_id,order_date,status)\n"
"#         order_items(order_id,product_id,quantity,unit_price) products(...)\n"
"sql = '''\nSELECT ...\n'''\n"
                ),
                "check_code": (
                    "rows = conn.execute(sql).fetchall()\n"
                    "# ZW: ada 1040+600, chi 100 = 1740 | US: dee 1600 | ZA: ed 20\n"
                    "assert rows == [('ZW', 1740.0), ('US', 1600.0), ('ZA', 20.0)], rows\n"
                    "print('PASS: three-table join + filtered aggregate — the everyday shape')\n"
                ),
                "refresher": (
"**Joins are just lookups, declared.** Each JOIN clause states a key match; the "
"chain order_items→orders→customers walks fact rows out to their dimensions "
"(pp-3's merge, in SQL):\n\n"
"```sql\nSELECT c.country, SUM(oi.quantity * oi.unit_price) AS revenue\nFROM order_items oi\nJOIN orders o    ON o.order_id = oi.order_id\nJOIN customers c ON c.customer_id = o.customer_id\nWHERE o.status = 'completed'\nGROUP BY c.country\nORDER BY revenue DESC;\n```\n\n"
"Discipline points interviewers notice: alias every table; filter rows in WHERE "
"*before* grouping (cheaper and correct — HAVING is only for aggregate "
"conditions); every non-aggregated SELECT column appears in GROUP BY. SQLite "
"and Postgres both accept ordering by the alias `revenue` (ORDER BY runs after "
"SELECT — the logical order at work)."
                ),
                "objectives": [
                    "Chain fact→dim joins with clean aliases",
                    "Combine WHERE (row filter) with GROUP BY (aggregate) correctly",
                    "Compute derived measures like quantity*unit_price inside SUM",
                ],
                "hints": [
                    "Start FROM order_items, JOIN orders ON order_id, JOIN customers ON customer_id.",
                    "WHERE o.status = 'completed' — before GROUP BY, not HAVING.",
                    "GROUP BY c.country, ORDER BY revenue DESC.",
                ],
                "resources": [
                    {"title": "SQL joins visualized", "url": "https://www.postgresql.org/docs/current/tutorial-join.html"},
                    {"title": "Mode SQL tutorial (excellent practice)", "url": "https://mode.com/sql-tutorial/"},
                ],
            },
            {
                "id": "sf-2",
                "title": "Customers who never ordered (anti-join)",
                "instructions": (
"The #1 SQL interview pattern: find rows in A with no match in B.\n\n**Your "
"task**\n\nWrite `sql` returning the **names of customers who have never placed "
"any order**, alphabetically. Use the LEFT JOIN ... IS NULL pattern (or NOT "
"EXISTS — both accepted). Then, in your head: why would `customer_id NOT IN "
"(SELECT customer_id FROM orders)` silently return nothing if orders ever "
"contained a NULL customer_id?"
                ),
                "starter_code": _SEED + (
"\nsql = '''\nSELECT ...\n'''\n"
                ),
                "check_code": (
                    "rows = [r[0] for r in conn.execute(sql).fetchall()]\n"
                    "assert rows == [], f'seed has no orphan customers yet: {rows}'\n"
                    "conn.execute(\"INSERT INTO customers VALUES (6,'zoe','KE'),(7,'abe','KE')\")\n"
                    "rows = [r[0] for r in conn.execute(sql).fetchall()]\n"
                    "assert rows == ['abe', 'zoe'], rows\n"
                    "print('PASS: anti-join — and you know the NOT IN + NULL trap')\n"
                ),
                "refresher": (
"**Anti-join, two idioms:**\n\n"
"```sql\n-- LEFT JOIN probe: unmatched rows carry NULLs\nSELECT c.name FROM customers c\nLEFT JOIN orders o ON o.customer_id = c.customer_id\nWHERE o.order_id IS NULL\nORDER BY c.name;\n\n-- NOT EXISTS: often clearest and plans well\nSELECT name FROM customers c\nWHERE NOT EXISTS (SELECT 1 FROM orders o\n                  WHERE o.customer_id = c.customer_id)\nORDER BY name;\n```\n\n"
"**The NOT IN trap** is three-valued logic: if the subquery yields a NULL, "
"`x NOT IN (...)` becomes `x <> NULL AND ...` = UNKNOWN — never true — so the "
"whole query returns empty, silently. NOT EXISTS is immune. Interviewers ask "
"this *specifically*; production NULLs trigger it *constantly*. Pipeline "
"translation: anti-joins detect referential breakage — 'events whose user_id "
"has no user row' — your Quality Gate project automates exactly this check."
                ),
                "objectives": [
                    "Write anti-joins via LEFT JOIN/IS NULL and NOT EXISTS",
                    "Explain the NOT IN + NULL three-valued-logic trap",
                    "Use anti-joins as referential-integrity checks in pipelines",
                ],
                "hints": [
                    "LEFT JOIN keeps ALL customers; the ones with no match have NULL order columns.",
                    "Filter WHERE o.order_id IS NULL (any orders column works), ORDER BY name.",
                ],
                "resources": [
                    {"title": "PostgreSQL: subquery expressions (EXISTS/IN)", "url": "https://www.postgresql.org/docs/current/functions-subquery.html"},
                    {"title": "NULLs and three-valued logic", "url": "https://en.wikipedia.org/wiki/Null_(SQL)"},
                ],
            },
            {
                "id": "sf-3",
                "title": "Top spender per country (correlated thinking)",
                "instructions": (
"One step below window functions: per-group maxima with plain SQL.\n\n**Your "
"task**\n\nWrite `sql` returning `(country, name, spend)` for **the top-spending "
"customer in each country** (completed orders only; spend = SUM(quantity * "
"unit_price)). Build a spend-per-customer aggregate (CTE or subquery), then keep "
"rows whose spend equals their country's max. Ordered by country. (Next project "
"you'll do this in one line with RANK() — feeling this pain first is the point.)"
                ),
                "starter_code": _SEED + (
"\nsql = '''\nWITH spend AS (\n    SELECT ...\n)\nSELECT ...\n'''\n"
                ),
                "check_code": (
                    "rows = conn.execute(sql).fetchall()\n"
                    "assert rows == [('US', 'dee', 1600.0), ('ZA', 'ed', 20.0), ('ZW', 'ada', 1640.0)], rows\n"
                    "print('PASS: per-group max via CTE — the pre-window-function classic')\n"
                ),
                "refresher": (
"**CTEs are named building blocks.** `WITH spend AS (...)` materializes a "
"readable intermediate — aggregation first, ranking logic second:\n\n"
"```sql\nWITH spend AS (\n  SELECT c.country, c.name,\n         SUM(oi.quantity * oi.unit_price) AS spend\n  FROM order_items oi\n  JOIN orders o    ON o.order_id = oi.order_id\n  JOIN customers c ON c.customer_id = o.customer_id\n  WHERE o.status = 'completed'\n  GROUP BY c.country, c.name\n)\nSELECT country, name, spend FROM spend s\nWHERE spend = (SELECT MAX(spend) FROM spend s2\n               WHERE s2.country = s.country)\nORDER BY country;\n```\n\n"
"The inner query is *correlated* — re-evaluated per outer row against the same "
"CTE. It's the SQL twin of pandas' `groupby().idxmax()` (pp-3). Note the "
"tie behavior: equality keeps ALL tied top spenders — often what business "
"wants, and exactly the RANK() vs ROW_NUMBER() distinction you'll formalize "
"next project. When per-group-top questions appear in interviews, mentioning "
"both the CTE approach and the window approach (and their tie semantics) is a "
"strong signal."
                ),
                "objectives": [
                    "Structure multi-step queries with CTEs",
                    "Write correlated subqueries for per-group extrema",
                    "Anticipate tie semantics before you learn RANK()",
                ],
                "hints": [
                    "CTE: group by country AND name to get spend per customer (with country attached).",
                    "Outer: keep rows where spend equals the max spend within the same country (correlated subquery on the CTE).",
                ],
                "resources": [
                    {"title": "PostgreSQL: WITH queries (CTEs)", "url": "https://www.postgresql.org/docs/current/queries-with.html"},
                    {"title": "Correlated subqueries", "url": "https://en.wikipedia.org/wiki/Correlated_subquery"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"**Second Highest Salary** (LeetCode 176, Easy/Medium): return the second "
"highest *distinct* salary from `Employee(id, salary)`, or NULL if it doesn't "
"exist. Give two solutions."
                ),
                "difficulty": "Easy",
                "topics": ["SQL", "subqueries", "OFFSET"],
                "answer": (
"```sql\n-- 1: max below max\nSELECT MAX(salary) AS SecondHighestSalary\nFROM Employee\nWHERE salary < (SELECT MAX(salary) FROM Employee);\n\n-- 2: distinct + offset, wrapped so empty -> NULL\nSELECT (SELECT DISTINCT salary FROM Employee\n        ORDER BY salary DESC LIMIT 1 OFFSET 1)\n       AS SecondHighestSalary;\n```"
                ),
                "explanation": (
"Solution 1 reads naturally and returns NULL for free (MAX over zero rows is "
"NULL — aggregate functions' NULL behavior working *for* you once). Solution 2 "
"generalizes to Nth-highest (OFFSET N-1) but needs the scalar-subquery wrap: a "
"bare LIMIT/OFFSET query returns *zero rows* when there's no second salary, "
"while the problem wants *one row containing NULL* — precisely the kind of "
"edge-case reading interviews reward. DISTINCT matters in both: [100, 100, 50] "
"must answer 50, not 100."
                ),
            },
            {
                "question": (
"**Duplicate Emails / dedup** (Easy, then production follow-up): find duplicated "
"emails in `Person(id, email)`; then: how do you *delete* the duplicates keeping "
"the lowest id, at 100M-row scale?"
                ),
                "difficulty": "Medium",
                "topics": ["GROUP BY/HAVING", "self-join", "dedup at scale"],
                "answer": (
"```sql\n-- find\nSELECT email FROM Person\nGROUP BY email HAVING COUNT(*) > 1;\n\n-- delete keeping MIN(id)\nDELETE FROM Person\nWHERE id NOT IN (SELECT MIN(id) FROM Person GROUP BY email);\n\n-- at scale (Postgres): create-swap instead of DELETE\nCREATE TABLE person_clean AS\nSELECT DISTINCT ON (email) * FROM Person ORDER BY email, id;\n-- then swap table names in one transaction and re-add indexes\n```"
                ),
                "explanation": (
"HAVING filters *groups* the way WHERE filters rows — the canonical use. For "
"deletion, the subquery keeps one winner per email. The scale follow-up is "
"where data engineers shine: massive DELETEs bloat and lock (each deleted row "
"is dead-tuple work for VACUUM in Postgres); rewriting the survivors into a "
"new table and atomically swapping is often 10x cheaper and safer to verify "
"before the swap. `DISTINCT ON` (Postgres) picks the first row per email under "
"the given ORDER BY — a superpower worth naming in interviews."
                ),
            },
            {
                "question": (
"**Explain the difference** between INNER, LEFT, FULL and CROSS joins — and "
"the classic follow-up: why did moving a filter from WHERE into the LEFT JOIN's "
"ON clause change the row count?"
                ),
                "difficulty": "Medium",
                "topics": ["joins", "ON vs WHERE"],
                "answer": (
"INNER keeps only matched pairs; LEFT keeps all left rows (NULL-padding "
"unmatched); FULL keeps all rows from both sides; CROSS is every combination "
"(no ON). The follow-up: in a LEFT JOIN, the **ON clause filters the right side "
"*before* padding** — unmatched left rows survive with NULLs. A **WHERE clause "
"filters *after* padding** — and any condition on right-side columns (other "
"than IS NULL) turns NULL-padded rows false, silently converting your LEFT "
"join into an INNER join."
                ),
                "explanation": (
"Example: `LEFT JOIN orders o ON o.customer_id = c.id AND o.status = "
"'completed'` keeps customers with no completed orders (padded); `LEFT JOIN "
"... WHERE o.status = 'completed'` drops them entirely, because for padded "
"rows o.status is NULL and NULL = 'completed' is UNKNOWN. This is among the "
"most common real-world SQL bugs — 'my customer count shrank after I added a "
"filter' — and a beloved interview probe because it tests whether you *model* "
"join evaluation rather than memorize syntax. Rule of thumb: conditions that "
"define the match → ON; conditions that filter the result → WHERE; and on "
"outer joins, think twice about every right-side WHERE condition."
                ),
            },
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "window-works",
        "title": "Window Works",
        "tagline": "Window functions: rank, lag, running totals — interview gold",
        "level": "Intermediate+",
        "tech": ["ROW_NUMBER/RANK", "LAG/LEAD", "frames", "gaps & islands"],
        "est_hours": 7,
        "brief": (
            "Window functions are the highest-signal SQL skill in data interviews — "
            "and the daily driver of analytics engineering. Learn to rank within "
            "groups, compare rows to neighbors (LAG/LEAD), compute running totals "
            "and moving averages, and crack the famous gaps-and-islands problem "
            "(sessionization in SQL — you built the Python version in Algo Gym). "
            "SQLite supports all of it, so every exercise runs in-app; milestones "
            "repeat the patterns on the Postgres warehouse at realistic scale."
        ),
        "milestones": [
            "Rank the warehouse's customers by spend within each country using ROW_NUMBER, RANK and DENSE_RANK — explain each difference on real ties.",
            "Month-over-month revenue growth with LAG: revenue per month, previous month's, and % change — one query.",
            "Running total and 7-day moving average of daily revenue using frame clauses (ROWS BETWEEN 6 PRECEDING AND CURRENT ROW).",
            "Sessionize the Mongo-exported clickstream (or seeded events) in SQL: gaps-and-islands with LAG + running SUM of new-session flags.",
            "Dedup with ROW_NUMBER: keep the latest row per (customer, day) from a table with duplicates — the production dedup idiom.",
        ],
        "under_the_hood": (
            "**Windows = aggregates that don't collapse rows.** GROUP BY folds each "
            "group to one row; a window function computes over a related set (the "
            "'window') while every row survives. `OVER (PARTITION BY x ORDER BY y)` "
            "defines: restart per x, order rows by y within it.\n\n"
            "**Execution:** the engine sorts (or hash-partitions) by the PARTITION/"
            "ORDER keys, then streams each partition maintaining running state — "
            "your count_sessions loop, generalized. That's why windows cost a sort "
            "but not a self-join; pre-window-function SQL needed hideous correlated "
            "subqueries for the same results (you wrote one in sf-3 — on purpose).\n\n"
            "**Frames** are the subtlety separating seniors: ORDER BY inside OVER "
            "defaults the frame to RANGE UNBOUNDED PRECEDING..CURRENT ROW — that's "
            "why adding ORDER BY turns SUM into a *running* sum. ROWS vs RANGE "
            "differ on ties (RANGE includes all peer rows with equal sort keys). "
            "Moving averages want explicit ROWS BETWEEN n PRECEDING AND CURRENT "
            "ROW. Spark's Window API mirrors this exactly — learn once, use in "
            "both."
        ),
        "exercises": [
            {
                "id": "wf-1",
                "title": "Top-2 per group with ROW_NUMBER",
                "instructions": (
"The single most-asked window pattern: 'top N per group'.\n\n**Your task**\n\n"
"Write `sql` returning `(country, name, spend)` for the **top 2 spenders per "
"country** (completed orders; spend = SUM(quantity*unit_price)). Use a CTE for "
"spend, then ROW_NUMBER() OVER (PARTITION BY country ORDER BY spend DESC) and "
"filter rn <= 2. Order by country, then spend descending. Compare mentally with "
"your sf-3 approach — same question, far cleaner."
                ),
                "starter_code": _SEED + (
"\nsql = '''\nWITH spend AS (\n    SELECT ...\n)\nSELECT ...\n'''\n"
                ),
                "check_code": (
                    "rows = conn.execute(sql).fetchall()\n"
                    "assert rows == [('US', 'dee', 1600.0), ('ZA', 'ed', 20.0), ('ZW', 'ada', 1640.0), ('ZW', 'chi', 100.0)], rows\n"
                    "print('PASS: top-N per group — the interview question, retired')\n"
                ),
                "refresher": (
"**The idiom to memorize cold:**\n\n"
"```sql\nWITH spend AS (\n  SELECT c.country, c.name,\n         SUM(oi.quantity*oi.unit_price) AS spend\n  FROM order_items oi\n  JOIN orders o ON o.order_id = oi.order_id\n  JOIN customers c ON c.customer_id = o.customer_id\n  WHERE o.status='completed'\n  GROUP BY c.country, c.name\n),\nranked AS (\n  SELECT *, ROW_NUMBER() OVER (\n           PARTITION BY country ORDER BY spend DESC) AS rn\n  FROM spend\n)\nSELECT country, name, spend FROM ranked\nWHERE rn <= 2 ORDER BY country, spend DESC;\n```\n\n"
"Window results can't be filtered in the same SELECT's WHERE (logical order: "
"windows compute *after* WHERE) — hence the second CTE. The trio: ROW_NUMBER "
"numbers 1,2,3 arbitrarily breaking ties; RANK gives ties equal rank then "
"skips (1,1,3); DENSE_RANK doesn't skip (1,1,2). 'Top 2 including ties?' → "
"RANK. 'Exactly 2 rows?' → ROW_NUMBER. Saying that distinction *unprompted* "
"is an interview flex."
                ),
                "objectives": [
                    "Apply the CTE → window → filter pipeline",
                    "Choose ROW_NUMBER vs RANK vs DENSE_RANK by tie semantics",
                    "Explain why window output needs an outer query to filter",
                ],
                "hints": [
                    "Reuse your sf-3 spend CTE verbatim.",
                    "Second CTE adds ROW_NUMBER() OVER (PARTITION BY country ORDER BY spend DESC).",
                    "Outer SELECT filters rn <= 2 — you can't do it inside the ranked CTE's own WHERE.",
                ],
                "resources": [
                    {"title": "PostgreSQL: window functions tutorial", "url": "https://www.postgresql.org/docs/current/tutorial-window.html"},
                    {"title": "SQLite window functions", "url": "https://www.sqlite.org/windowfunctions.html"},
                ],
            },
            {
                "id": "wf-2",
                "title": "Month-over-month growth with LAG",
                "instructions": (
"Every analytics dashboard's favorite: compare each period to the previous "
"one.\n\n**Your task**\n\nWrite `sql` producing `(month, revenue, prev_revenue)` "
"per month across completed orders — month as `strftime('%Y-%m', order_date)`, "
"revenue summed, and `prev_revenue` via LAG over month order (NULL for the first "
"month). Ordered by month. Aggregate first (CTE), window second — mixing GROUP BY "
"and LAG in one block is the classic error here."
                ),
                "starter_code": _SEED + (
"\nsql = '''\nWITH monthly AS (\n    SELECT ...\n)\nSELECT ...\n'''\n"
                ),
                "check_code": (
                    "rows = conn.execute(sql).fetchall()\n"
                    "assert rows == [('2026-01', 1040.0, None), ('2026-02', 600.0, 1040.0), ('2026-03', 1700.0, 600.0), ('2026-04', 20.0, 1700.0)], rows\n"
                    "print('PASS: LAG over aggregated periods — MoM/WoW/YoY unlocked')\n"
                ),
                "refresher": (
"**LAG(col, n) hands you a previous row's value** without a self-join:\n\n"
"```sql\nWITH monthly AS (\n  SELECT strftime('%Y-%m', o.order_date) AS month,\n         SUM(oi.quantity*oi.unit_price) AS revenue\n  FROM order_items oi JOIN orders o ON o.order_id=oi.order_id\n  WHERE o.status='completed'\n  GROUP BY month\n)\nSELECT month, revenue,\n       LAG(revenue) OVER (ORDER BY month) AS prev_revenue\nFROM monthly ORDER BY month;\n```\n\n"
"The two-layer shape is the lesson: windows *can't* wrap aggregates of a "
"different grain in one pass, so collapse to the period grain first, then "
"window over the periods. Growth % is then "
"`(revenue - prev)/prev * 100` — guard prev=0/NULL with NULLIF/COALESCE. LEAD "
"is the mirror (next row); LAG(col, 12) gives year-over-year on monthly data. "
"In production, beware missing months: LAG sees the previous *row*, not the "
"previous *calendar month* — a date spine (calendar table) fixes it, and "
"mentioning that is senior-level polish."
                ),
                "objectives": [
                    "Layer aggregation-then-window correctly",
                    "Use LAG/LEAD with explicit ORDER BY inside OVER",
                    "Spot the missing-period pitfall and the date-spine fix",
                ],
                "hints": [
                    "CTE first: month + SUM as revenue, GROUP BY month.",
                    "Then LAG(revenue) OVER (ORDER BY month) — no PARTITION BY needed here.",
                ],
                "resources": [
                    {"title": "LAG/LEAD (PostgreSQL window function list)", "url": "https://www.postgresql.org/docs/current/functions-window.html"},
                    {"title": "Date spines (dbt's classic write-up)", "url": "https://docs.getdbt.com/blog/date-spines"},
                ],
            },
            {
                "id": "wf-3",
                "title": "Gaps & islands: sessionize in pure SQL",
                "instructions": (
"The Hard-tier classic — sessionization without loops.\n\n**Your task**\n\nGiven "
"an events table (created in starter: user_id, ts as integer seconds), write "
"`sql` returning `(user_id, session_id, session_start, events)` — sessions "
"defined by gaps > 30s within each user, session_id numbering each user's "
"sessions from 1 in time order. The two-step: (1) LAG to flag new-session starts, "
"(2) running SUM of flags = session id. You solved this with a Python loop in "
"Algo Gym — this is the declarative twin."
                ),
                "starter_code": (
"import sqlite3\nconn = sqlite3.connect(':memory:')\nconn.executescript('''\nCREATE TABLE events(user_id TEXT, ts INT);\nINSERT INTO events VALUES\n ('u1',0),('u1',10),('u1',20),('u1',100),('u1',105),\n ('u2',0),('u2',40),('u2',50);\n''')\n\nsql = '''\nWITH flagged AS (\n    SELECT ...\n),\nsessions AS (\n    SELECT ...\n)\nSELECT ...\n'''\n"
                ),
                "check_code": (
                    "rows = conn.execute(sql).fetchall()\n"
                    "assert rows == [('u1', 1, 0, 3), ('u1', 2, 100, 2), ('u2', 1, 0, 1), ('u2', 2, 40, 2)], rows\n"
                    "print('PASS: gaps & islands — the hardest common interview SQL, done')\n"
                ),
                "refresher": (
"**The two-step that cracks every islands problem:**\n\n"
"```sql\nWITH flagged AS (\n  SELECT user_id, ts,\n         CASE WHEN ts - LAG(ts) OVER (\n                PARTITION BY user_id ORDER BY ts) > 30\n              OR LAG(ts) OVER (\n                PARTITION BY user_id ORDER BY ts) IS NULL\n              THEN 1 ELSE 0 END AS new_session\n  FROM events\n),\nsessions AS (\n  SELECT *, SUM(new_session) OVER (\n           PARTITION BY user_id ORDER BY ts) AS session_id\n  FROM flagged\n)\nSELECT user_id, session_id, MIN(ts), COUNT(*)\nFROM sessions GROUP BY user_id, session_id\nORDER BY user_id, session_id;\n```\n\n"
"Step 1 marks island *starts* (first event or big gap). Step 2's running SUM "
"converts start-flags into island *ids* — each flag increments the counter for "
"all following rows. Step 3 aggregates per island. This flag-then-running-sum "
"trick solves the whole gaps-and-islands family: consecutive login days, "
"streaks, sensor outages, contiguous seat blocks. It's also, almost verbatim, "
"the Spark Window version you'd run on billions of events. If you internalize "
"one hard SQL pattern for interviews, make it this one."
                ),
                "objectives": [
                    "Flag boundaries with LAG + CASE (handling the NULL first row)",
                    "Convert flags to group ids with a running SUM window",
                    "Recognize the gaps-and-islands family across problems",
                ],
                "hints": [
                    "First event per user: LAG is NULL — that must flag as new_session=1 too.",
                    "The running SUM uses the same PARTITION BY user_id ORDER BY ts window.",
                    "Final layer is a plain GROUP BY user_id, session_id with MIN(ts) and COUNT(*).",
                ],
                "resources": [
                    {"title": "Gaps and islands explained", "url": "https://www.red-gate.com/simple-talk/databases/sql-server/t-sql-programming-sql-server/gaps-islands-across-date-ranges/"},
                    {"title": "Spark Window functions (the same API)", "url": "https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.Window.html"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"**Department Top Three Salaries** (LeetCode 185, Hard): from Employee(id, name, "
"salary, departmentId) and Department(id, name), return each department's "
"employees earning a top-three *distinct* salary in that department."
                ),
                "difficulty": "Hard",
                "topics": ["window functions", "DENSE_RANK"],
                "answer": (
"```sql\nSELECT d.name AS Department, e.name AS Employee, e.salary AS Salary\nFROM (\n  SELECT *, DENSE_RANK() OVER (\n           PARTITION BY departmentId\n           ORDER BY salary DESC) AS rk\n  FROM Employee\n) e\nJOIN Department d ON d.id = e.departmentId\nWHERE e.rk <= 3;\n```"
                ),
                "explanation": (
"'Top three **distinct** salaries' is the tell for DENSE_RANK. Walk the "
"example [90, 90, 80, 70, 60] aloud — it's how you nail this under "
"pressure:\n\n"
"- DENSE_RANK → 1, 1, 2, 3, 4 · `rk <= 3` keeps 90, 90, 80, **70** ✅\n"
"- RANK → 1, 1, 3, 4, 5 · `rk <= 3` keeps only 90, 90, 80 — drops 70 ❌\n"
"- ROW_NUMBER → 1, 2, 3, 4, 5 · keeps 90, 90, 80 and breaks the 90-tie "
"arbitrarily ❌\n\n"
"DENSE_RANK doesn't skip after ties, so its rank counts *distinct values* — "
"exactly what the question asks for. The solution is one window + one join + "
"one filter; any correlated-subquery version ('count how many salaries are "
"higher') is O(n²)-ish and marks you as pre-window-function."
                ),
            },
            {
                "question": (
"**Consecutive Days** (Medium/Hard): given Logins(user_id, login_date), find "
"users who logged in on 3 or more consecutive days. (The streak question — "
"asked at Meta/Amazon-style loops constantly.)"
                ),
                "difficulty": "Hard",
                "topics": ["gaps & islands", "date arithmetic"],
                "answer": (
"```sql\nWITH d AS (\n  SELECT DISTINCT user_id, login_date FROM Logins\n),\ngrp AS (\n  SELECT user_id, login_date,\n         DATE(login_date,\n              '-' || ROW_NUMBER() OVER (\n                     PARTITION BY user_id\n                     ORDER BY login_date) || ' days') AS anchor\n  FROM d\n)\nSELECT DISTINCT user_id\nFROM grp\nGROUP BY user_id, anchor\nHAVING COUNT(*) >= 3;\n```\n(Postgres flavor: `login_date - ROW_NUMBER() OVER (...) * INTERVAL '1 day'`.)"
                ),
                "explanation": (
"The date-minus-row-number trick: within a consecutive run, dates increase by "
"1 and row numbers increase by 1, so their *difference is constant* — a "
"perfect group key (the 'anchor'). Runs become groups; HAVING COUNT(*) >= 3 "
"finds streaks. DISTINCT first matters — duplicate same-day logins would "
"desync the row numbers (a trap the strong candidates catch). Alternative "
"framing with LAG + flag + running-sum also works (your wf-3 machinery); "
"offering both and noting they're the same islands idea is a standout answer."
                ),
            },
            {
                "question": (
"**Running total vs GROUP BY** (Medium): explain the difference between "
"`SUM(amount) OVER (ORDER BY day)` and `GROUP BY day` with SUM — and why does "
"adding `PARTITION BY region` to the window change memory/performance "
"characteristics on a big table?"
                ),
                "difficulty": "Medium",
                "topics": ["window frames", "execution"],
                "answer": (
"GROUP BY collapses to one row per day (total per day); the window SUM with "
"ORDER BY keeps every row and computes a *cumulative* total up to that row "
"(default frame UNBOUNDED PRECEDING..CURRENT ROW). Adding PARTITION BY region "
"restarts the accumulation per region: execution sorts (or re-uses an index) "
"on (region, day), streams each partition with O(1) running state, and can "
"process partitions independently — which distributes cleanly (Spark assigns "
"partitions to executors). A window with no PARTITION BY forces a single "
"global ordering — one sort, one stream, no parallelism: the classic "
"'why is my global running total slow on 2B rows' answer."
                ),
                "explanation": (
"This probes execution-model understanding rather than syntax. Key points to "
"hit: default frame semantics (ORDER BY inside OVER changes SUM's meaning!), "
"running state per partition (your count_sessions loop again), sort cost as "
"the dominant term, and the parallelism cliff of unpartitioned windows. "
"Production advice worth volunteering: for dashboard-grade running totals over "
"huge history, pre-aggregate to the day grain first (shrink n), or maintain "
"cumulative snapshots incrementally in the pipeline instead of recomputing."
                ),
            },
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "pg-warehouse",
        "title": "PG Warehouse",
        "tagline": "Real Postgres: indexes, EXPLAIN, transactions, bulk loads",
        "level": "Intermediate+",
        "tech": ["PostgreSQL", "B-tree indexes", "EXPLAIN ANALYZE", "transactions", "COPY"],
        "est_hours": 7,
        "brief": (
            "Time to operate a real database. Your compose stack's `warehouse` "
            "service is a genuine Postgres 16 (with pgvector for later), pre-seeded "
            "with the e-commerce dataset. Learn what interviews and production both "
            "demand: reading query plans, designing indexes that actually get used, "
            "transaction isolation, and loading data fast with COPY. In-app "
            "exercises simulate the concepts; the milestones are hands-on against "
            "the live server from Jupyter."
        ),
        "milestones": [
            "EXPLAIN ANALYZE a customer-orders join before and after dropping/recreating idx_orders_customer — record the plan change (Seq Scan vs Index Scan) and timing.",
            "Design an index for 'orders by customer X in date range Y' — composite (customer_id, order_date); prove column order matters by testing the reversed index.",
            "Demonstrate a transaction: BEGIN, transfer-style paired updates, ROLLBACK vs COMMIT; then force a serialization conflict with two connections.",
            "Bulk-load 1M synthetic rows via COPY (psycopg2 copy_expert) vs executemany — time both; then add the index AFTER loading and compare with loading into an indexed table.",
            "Read pg_stat_user_tables and pg_stat_user_indexes to find unused indexes and seq-scan-heavy tables — the DBA hygiene loop.",
        ],
        "under_the_hood": (
            "**B-tree indexes** are sorted trees over (key → row pointer): "
            "O(log n) descent, then heap fetches for the actual rows. That's why "
            "an index on (customer_id, order_date) serves 'customer = X AND date "
            "range' (descend on X, scan the sorted date run) but an index on "
            "(order_date, customer_id) serves it poorly — leftmost-prefix rule, "
            "the composite-index law (and binary search from Algo Gym, on disk).\n\n"
            "**The planner is cost-based:** it estimates rows via statistics "
            "(ANALYZE keeps them fresh) and picks the cheapest plan — a Seq Scan "
            "genuinely beats an index when a filter matches most of the table. "
            "EXPLAIN ANALYZE shows estimates vs reality; big mismatches mean stale "
            "stats or skew (your ss-1 lesson, in the optimizer).\n\n"
            "**MVCC:** writers don't block readers — each transaction sees a "
            "snapshot; updates write new row versions, old ones linger until "
            "VACUUM. That's why massive UPDATE/DELETE bloats tables (the "
            "create-and-swap trick from SQL Foundry's interview), and why "
            "long-running transactions hold back cleanup. COPY beats INSERT loops "
            "because it streams rows in one command — the per-statement round-trip "
            "and WAL overhead, amortized away — exactly the batching lesson every "
            "ETL loader learns."
        ),
        "exercises": [
            {
                "id": "pw-1",
                "title": "Index or not? (planner reasoning)",
                "instructions": (
"Think like the query planner before you meet the real one.\n\n**Your task**\n\n"
"Implement `should_use_index(total_rows, matching_rows, row_cost=1.0, "
"index_cost=3.0)`: return True if an index scan is cheaper. Model: seq scan costs "
"`total_rows * row_cost`; index scan costs `log2(total_rows) * index_cost + "
"matching_rows * row_cost * 2` (descent + random-access penalty per matched row; "
"guard total_rows=0). Then `selectivity_verdict(total, matching)` returning "
"'index' or 'seq_scan' using it. The checker's cases mirror real planner "
"behavior: tiny selectivity → index; >~half the table → seq scan."
                ),
                "starter_code": (
                    "import math\n\n"
                    "def should_use_index(total_rows, matching_rows, row_cost=1.0, index_cost=3.0):\n"
                    "    ...\n\n"
                    "def selectivity_verdict(total, matching):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "assert selectivity_verdict(1_000_000, 50) == 'index'\n"
                    "assert selectivity_verdict(1_000_000, 600_000) == 'seq_scan'\n"
                    "assert selectivity_verdict(0, 0) == 'seq_scan'\n"
                    "assert should_use_index(1000, 5) is True\n"
                    "assert should_use_index(1000, 900) is False\n"
                    "print('PASS: you can predict Seq Scan vs Index Scan before EXPLAIN tells you')\n"
                ),
                "refresher": (
"**Why indexes aren't free wins.** An index scan pays: tree descent "
"(O(log n)), then a *random* heap fetch per matching row — random I/O is far "
"pricier than sequential streaming. So the crossover is about **selectivity**: "
"fetch 0.1% of rows → index wins big; fetch 50% → just stream the whole table. "
"Postgres models this with real cost constants (random_page_cost vs "
"seq_page_cost) and its statistics' row estimates — your function is a toy "
"twin of `costsize.c`.\n\n"
"```python\nseq = total_rows * row_cost\nidx = math.log2(max(total_rows, 2)) * index_cost \\\n      + matching_rows * row_cost * 2\n```\n\n"
"Practical fallout you'll verify on the live warehouse: indexes on "
"low-cardinality columns (status with 3 values) rarely help; stale ANALYZE "
"stats make the planner guess wrong; and 'why isn't my index used?' is almost "
"always selectivity or leftmost-prefix, not a bug. Interviewers adore asking "
"exactly that question."
                ),
                "objectives": [
                    "Model index-vs-seq-scan cost and the selectivity crossover",
                    "Explain random vs sequential I/O costs",
                    "Diagnose 'why isn't my index used?' from first principles",
                ],
                "hints": [
                    "Guard the empty table first (return False/'seq_scan').",
                    "Implement the two cost formulas exactly as given; compare.",
                    "selectivity_verdict just maps the boolean to the two strings.",
                ],
                "resources": [
                    {"title": "PostgreSQL: using EXPLAIN", "url": "https://www.postgresql.org/docs/current/using-explain.html"},
                    {"title": "PostgreSQL index types", "url": "https://www.postgresql.org/docs/current/indexes-types.html"},
                ],
            },
            {
                "id": "pw-2",
                "title": "Transactions: all or nothing",
                "instructions": (
"Model why banks (and pipelines) need atomicity.\n\n**Your task**\n\nImplement "
"`transfer(accounts, frm, to, amount)` over a dict of balances that must be "
"**atomic**: if the source lacks funds (raise ValueError) or either account is "
"missing (raise KeyError), balances must be COMPLETELY unchanged — no partial "
"debit. Implement it transaction-style: stage changes, validate, then commit "
"both — or mutate then roll back on failure. The checker verifies the "
"failed-transfer-leaves-no-trace property specifically."
                ),
                "starter_code": (
                    "def transfer(accounts, frm, to, amount):\n"
                    "    \"\"\"Atomically move amount between accounts (a dict).\n"
                    "    Raise ValueError on insufficient funds, KeyError on bad account.\"\"\"\n"
                    "    ...\n"
                ),
                "check_code": (
                    "acc = {'a': 100, 'b': 50}\n"
                    "transfer(acc, 'a', 'b', 30)\n"
                    "assert acc == {'a': 70, 'b': 80}\n"
                    "try:\n"
                    "    transfer(acc, 'a', 'b', 999)\n"
                    "    raise AssertionError('should raise on insufficient funds')\n"
                    "except ValueError:\n"
                    "    pass\n"
                    "assert acc == {'a': 70, 'b': 80}, 'FAILED transfer must change NOTHING'\n"
                    "try:\n"
                    "    transfer(acc, 'a', 'ghost', 10)\n"
                    "    raise AssertionError('should raise on missing account')\n"
                    "except KeyError:\n"
                    "    pass\n"
                    "assert acc == {'a': 70, 'b': 80}\n"
                    "print('PASS: atomicity — validate everything, then commit everything')\n"
                ),
                "refresher": (
"**ACID, felt rather than recited.** Atomicity: all effects or none. The "
"robust implementation pattern is *validate-then-mutate*:\n\n"
"```python\nif frm not in accounts or to not in accounts:\n    raise KeyError(...)\nif accounts[frm] < amount:\n    raise ValueError(...)\n# only now touch anything\naccounts[frm] -= amount\naccounts[to] += amount\n```\n\n"
"Databases generalize this with the WAL (write-ahead log): changes go to the "
"log first; COMMIT makes them durable; crash mid-transaction → recovery "
"replays/undoes via the log. In psycopg2 you get BEGIN implicitly and choose "
"`conn.commit()` or `conn.rollback()` — and the classic pipeline bug is "
"forgetting that *reads in the same transaction see your uncommitted writes*, "
"while other connections don't (isolation). For ETL: wrap each batch in one "
"transaction — a crashed load then leaves the warehouse clean instead of "
"half-written, which pairs with idempotent re-runs (ww-3) as the two pillars "
"of safe loading."
                ),
                "objectives": [
                    "Implement validate-then-mutate atomicity",
                    "Connect the pattern to WAL, COMMIT/ROLLBACK and psycopg2",
                    "Design ETL batch loads as transactions",
                ],
                "hints": [
                    "Do ALL checks before ANY mutation — that's the entire trick.",
                    "Check both accounts exist (KeyError) before checking funds (ValueError) — the checker tests both.",
                ],
                "resources": [
                    {"title": "PostgreSQL: transactions tutorial", "url": "https://www.postgresql.org/docs/current/tutorial-transactions.html"},
                    {"title": "psycopg2: transactions", "url": "https://www.psycopg.org/docs/usage.html#transactions-control"},
                ],
            },
            {
                "id": "pw-3",
                "title": "Batch loading (the COPY lesson)",
                "instructions": (
"Why does COPY crush row-by-row INSERTs? Overhead amortization — measure it.\n\n"
"**Your task**\n\nImplement `load_rows(conn, rows, batch_size)` inserting into "
"the provided sqlite table using `executemany` in batches (one commit per "
"batch), returning the number of batches. Then `estimate_cost(n_rows, "
"per_stmt_overhead, per_row_cost, batch_size)` returning total cost where each "
"batch pays overhead once: `ceil(n/batch) * overhead + n * per_row`. The checker "
"verifies both, plus that batching 10k rows by 1000 models ~10x cheaper overhead "
"than row-at-a-time."
                ),
                "starter_code": (
                    "import sqlite3, math\n\n"
                    "conn = sqlite3.connect(':memory:')\n"
                    "conn.execute('CREATE TABLE t(id INT, val TEXT)')\n\n"
                    "def load_rows(conn, rows, batch_size):\n"
                    "    ...\n\n"
                    "def estimate_cost(n_rows, per_stmt_overhead, per_row_cost, batch_size):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "rows = [(i, f'v{i}') for i in range(2500)]\n"
                    "nb = load_rows(conn, rows, 1000)\n"
                    "assert nb == 3\n"
                    "assert conn.execute('SELECT COUNT(*) FROM t').fetchone()[0] == 2500\n"
                    "single = estimate_cost(10_000, 5.0, 0.1, 1)\n"
                    "batched = estimate_cost(10_000, 5.0, 0.1, 1000)\n"
                    "assert abs(single - 51_000) < 1e-6 and abs(batched - 1_050) < 1e-6\n"
                    "assert single / batched > 10\n"
                    "print('PASS: batching amortizes per-statement overhead — the COPY principle')\n"
                ),
                "refresher": (
"**Every statement pays a toll** — parse, plan, round-trip, WAL flush on "
"commit. Row-at-a-time loading pays it n times; batching pays it n/batch "
"times:\n\n"
"```python\nfor i in range(0, len(rows), batch_size):\n    conn.executemany('INSERT INTO t VALUES (?, ?)',\n                     rows[i:i+batch_size])\n    conn.commit()   # one durability point per batch\n```\n\n"
"The hierarchy on real Postgres, slow→fast: INSERT per row with autocommit "
"(worst — one fsync each) → executemany → execute_values (psycopg2, one "
"statement per batch) → **COPY** (single streamed command, minimal parsing, "
"~10-100x the naive loop). Batch-commit also defines your *failure "
"granularity*: a crash loses at most one batch, and paired with idempotent "
"upserts (ww-3) the retry is clean. Same physics everywhere: Kafka producer "
"batching, Spark's partition-level writes, HTTP keep-alive — round-trips are "
"the enemy, amortize them."
                ),
                "objectives": [
                    "Batch inserts with executemany + per-batch commits",
                    "Model and compute overhead amortization",
                    "Rank INSERT/executemany/COPY and choose failure granularity",
                ],
                "hints": [
                    "Slice rows[i:i+batch_size] in a range(0, len, batch) loop; count iterations.",
                    "estimate_cost: math.ceil(n_rows / batch_size) * per_stmt_overhead + n_rows * per_row_cost.",
                ],
                "resources": [
                    {"title": "PostgreSQL COPY", "url": "https://www.postgresql.org/docs/current/sql-copy.html"},
                    {"title": "psycopg2: fast execution helpers", "url": "https://www.psycopg.org/docs/extras.html#fast-execution-helpers"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"Your query `SELECT * FROM orders WHERE customer_id = 42 ORDER BY order_date "
"DESC LIMIT 10` is slow on a 500M-row table. Walk through your diagnosis and "
"fix. (Classic DE interview systems question.)"
                ),
                "difficulty": "Medium",
                "topics": ["indexes", "EXPLAIN", "composite keys"],
                "answer": (
"Diagnose: `EXPLAIN (ANALYZE, BUFFERS)` — expect either a Seq Scan (no usable "
"index) or an Index Scan on customer_id followed by a Sort of that customer's "
"rows. Fix: a composite index `(customer_id, order_date DESC)` — the planner "
"descends to customer 42, then reads rows *already in date order*, stopping "
"after 10: no sort, ~10 row fetches total. Also check: stale statistics "
"(ANALYZE), index bloat, and whether SELECT * forces heap fetches that an "
"index-only scan on a narrower column list could avoid (covering index with "
"INCLUDE)."
                ),
                "explanation": (
"The killer insight is that the composite index serves *both* the filter and "
"the ordering — LIMIT then makes it nearly O(log n) total. Column order is "
"non-negotiable: (order_date, customer_id) would scan the date index checking "
"every row for customer 42. Strong candidates mention the leftmost-prefix "
"rule, index-only scans (visibility map permitting), and the honest caveat "
"that every index taxes writes — this table takes heavy inserts, so you add "
"indexes deliberately, not defensively. Bonus points for partitioning by date "
"at this scale."
                ),
            },
            {
                "question": (
"Two workers of your ETL occasionally upsert the *same* order row "
"concurrently, and you see intermittent deadlocks. Why do deadlocks happen, "
"and give two concrete fixes."
                ),
                "difficulty": "Hard",
                "topics": ["locking", "deadlocks", "upserts"],
                "answer": (
"A deadlock needs circular waiting: worker A locks row 1 then wants row 2; "
"worker B holds row 2 and wants row 1. With multi-row upserts in differing "
"orders, that cycle appears; Postgres detects it and kills one transaction. "
"Fixes: **(1) Consistent lock ordering** — sort each batch by primary key "
"before upserting, so all workers acquire locks in the same global order "
"(cycles become impossible). **(2) Keyed partitioning** — route each order_id "
"to exactly one worker (hash-partition the work queue), so no two workers "
"ever touch the same row (the Spark/Kafka partitioning idea applied to "
"loading). Also honorable: smaller batches + retry-on-deadlock (it's safe — "
"the aborted transaction rolled back cleanly), and SELECT ... FOR UPDATE "
"SKIP LOCKED for queue-like tables."
                ),
                "explanation": (
"This tests whether you understand row locks as a *graph* problem, not "
"magic. Sorting-to-order is the textbook fix and one line of code; "
"partition-the-work is the architectural fix that also removes contention "
"entirely — connecting it to hash partitioning shows systems maturity. "
"Mentioning that ON CONFLICT upserts still take row locks (they don't dodge "
"the problem) and that retries are safe *because* of atomic rollback ties "
"the answer back to ACID fundamentals."
                ),
            },
            {
                "question": (
"Explain MVCC in Postgres: how can a long-running analytics query and OLTP "
"writes coexist without blocking each other, and what maintenance debt does "
"this design create?"
                ),
                "difficulty": "Medium",
                "topics": ["MVCC", "VACUUM", "isolation"],
                "answer": (
"MVCC gives every transaction a snapshot: rows carry (xmin, xmax) transaction "
"ids; an UPDATE writes a *new row version* rather than overwriting, and each "
"transaction sees only versions committed before its snapshot. Readers "
"therefore never block writers and vice versa — the analytics query keeps "
"reading its consistent snapshot while OLTP commits new versions alongside. "
"The debt: dead row versions accumulate (bloat) until **VACUUM** reclaims "
"them, and autovacuum can't clean versions still visible to any open "
"snapshot — so a forgotten idle-in-transaction session or a 6-hour analytics "
"query holds back cleanup table-wide. Long-term, transaction-id wraparound "
"requires periodic aggressive vacuums."
                ),
                "explanation": (
"Interviewers use MVCC to separate 'has used Postgres' from 'understands "
"Postgres'. The coexistence story is the headline, but the debt side is "
"where senior signal lives: bloat from update-heavy tables, the "
"long-transaction footgun (why you run heavy analytics on a replica or in "
"the warehouse — the very architecture this curriculum builds), and why "
"massive DELETEs prefer create-and-swap. If asked to go deeper: default "
"READ COMMITTED re-snapshots per statement, REPEATABLE READ per transaction, "
"and SERIALIZABLE adds predicate-level conflict detection with retry-able "
"serialization failures."
                ),
            },
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "star-schema",
        "title": "Star Schema Studio",
        "tagline": "Dimensional modeling: facts, dimensions, slowly changing truth",
        "level": "Intermediate+",
        "tech": ["dimensional modeling", "star schema", "SCD Type 2", "surrogate keys", "grain"],
        "est_hours": 7,
        "brief": (
            "Schema design is what separates data engineers from script writers — "
            "and every senior interview includes a modeling exercise. Redesign the "
            "warehouse's OLTP tables into a proper analytics star: fact_sales at "
            "order-line grain, dim_customer with Type-2 history, dim_product, "
            "dim_date. Build it in Postgres with real DDL, then feed it and answer "
            "business questions that were painful before and trivial after."
        ),
        "milestones": [
            "Declare the grain ('one row per order line') in a comment, then create fact_sales + dim_customer/dim_product/dim_date DDL with surrogate keys.",
            "Build dim_date for 2025-2027 with a generate_series query (day, month, quarter, year, is_weekend).",
            "Populate the star from the OLTP tables with INSERT..SELECT; fact rows reference dimension surrogate keys, not natural ids.",
            "Implement SCD Type 2 on dim_customer (valid_from, valid_to, is_current): move a customer to a new country and update history correctly.",
            "Answer 'revenue by customer country AT TIME OF SALE vs current country' — impossible without SCD2, one join with it. Feel the payoff.",
        ],
        "under_the_hood": (
            "**Why remodel at all?** OLTP schemas (3NF) optimize writes: no "
            "redundancy, every fact stored once, updates touch one row. Analytics "
            "wants the opposite: wide scans, few joins, stable history. The star "
            "schema trades redundancy for query simplicity — a central fact table "
            "(events/measurements: additive numbers + foreign keys) ringed by "
            "denormalized dimensions (who/what/when/where descriptors).\n\n"
            "**Grain is the sacred contract:** 'one row per order line' decides "
            "every column's meaning. Mixed grains (order-level shipping fee in a "
            "line-level fact) double-count under aggregation — the most common "
            "modeling bug in the wild and a favorite interview probe.\n\n"
            "**Surrogate keys** (meaningless integers) decouple your warehouse "
            "from source-system ids and enable **SCD Type 2**: when a customer "
            "moves country you *close* the current dimension row (valid_to = now, "
            "is_current = false) and insert a new version with a new surrogate "
            "key. Facts keep pointing at the version that was true *at event "
            "time* — history preserved by construction. Every serious warehouse "
            "(and dbt snapshot) is this pattern."
        ),
        "exercises": [
            {
                "id": "sc-1",
                "title": "Grain police",
                "instructions": (
"Catch the double-counting bug before it ships.\n\n**Your task**\n\nImplement "
"`validate_grain(rows, grain_keys)`: rows are dicts; return the list of "
"key-tuples that appear more than once (empty list = grain holds). Then "
"`safe_to_sum(rows, grain_keys, measure)`: True only if the grain holds AND "
"the measure is present and numeric in every row. This pair is the "
"assertion you'll wire into every pipeline you ever build (Quality Gate "
"industrializes it in Stage 6)."
                ),
                "starter_code": (
                    "def validate_grain(rows, grain_keys):\n"
                    "    ...\n\n"
                    "def safe_to_sum(rows, grain_keys, measure):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "rows = [\n"
                    "    {'order_id': 1, 'line': 1, 'amount': 10.0},\n"
                    "    {'order_id': 1, 'line': 2, 'amount': 5.0},\n"
                    "    {'order_id': 2, 'line': 1, 'amount': 7.0},\n"
                    "]\n"
                    "assert validate_grain(rows, ['order_id', 'line']) == []\n"
                    "assert validate_grain(rows, ['order_id']) == [(1,)]\n"
                    "assert safe_to_sum(rows, ['order_id', 'line'], 'amount') is True\n"
                    "assert safe_to_sum(rows, ['order_id'], 'amount') is False\n"
                    "rows.append({'order_id': 3, 'line': 1, 'amount': 'oops'})\n"
                    "assert safe_to_sum(rows, ['order_id', 'line'], 'amount') is False\n"
                    "print('PASS: grain validated — no silent double counting on your watch')\n"
                ),
                "refresher": (
"**Grain = the uniqueness promise.** 'One row per X' means the X-keys form a "
"unique tuple. Checking is a Counter over key tuples (Structly's frequency "
"map, working a real job):\n\n"
"```python\nfrom collections import Counter\ncounts = Counter(tuple(r[k] for k in grain_keys) for r in rows)\ndups = [k for k, c in counts.items() if c > 1]\n```\n\n"
"Why it's the *first* check before any SUM: joining an order-grain fee onto "
"line-grain rows repeats the fee per line — revenue inflates by exactly the "
"average lines-per-order, quietly, plausibly, until finance notices. "
"`safe_to_sum` adds the second silent killer: non-numeric strays ('oops', "
"None) that either crash the sum or, worse, get coerced. In SQL the same "
"checks are `GROUP BY keys HAVING COUNT(*)>1` and a typed column — and in "
"interviews, *asking about the grain before answering a modeling question* "
"is itself the signal."
                ),
                "objectives": [
                    "Verify grain with key-tuple frequency maps",
                    "Gate aggregations on grain + type validity",
                    "Explain the join-across-grains double-count mechanism",
                ],
                "hints": [
                    "Counter over tuple(r[k] for k in grain_keys); collect keys with count > 1.",
                    "safe_to_sum: validate_grain must return [] AND every row's measure must pass isinstance(x, (int, float)) — exclude bool if you're fancy.",
                ],
                "resources": [
                    {"title": "Kimball: declaring the grain", "url": "https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/grain/"},
                    {"title": "Fact table basics (Kimball techniques)", "url": "https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/"},
                ],
            },
            {
                "id": "sc-2",
                "title": "SCD Type 2 merge, by hand",
                "instructions": (
"The dimensional-modeling interview question: implement history-preserving "
"updates.\n\n**Your task**\n\nImplement `scd2_apply(dim, updates, today)`. `dim` "
"is a list of dicts with keys: natural_key, attrs (dict), valid_from, valid_to "
"(None = open), is_current. For each update {natural_key, attrs}: unchanged "
"attrs → no-op; changed attrs → close the current row (valid_to=today, "
"is_current=False) and append a new current row (valid_from=today, "
"valid_to=None, is_current=True); brand-new key → insert as current. Return "
"dim. The checker replays a customer's country move and asserts the full "
"version chain."
                ),
                "starter_code": (
                    "def scd2_apply(dim, updates, today):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "dim = [{'natural_key': 'c1', 'attrs': {'country': 'ZW'},\n"
                    "        'valid_from': '2025-01-01', 'valid_to': None, 'is_current': True}]\n"
                    "dim = scd2_apply(dim, [{'natural_key': 'c1', 'attrs': {'country': 'ZW'}}], '2026-01-01')\n"
                    "assert len(dim) == 1 and dim[0]['is_current'], 'unchanged attrs must be a no-op'\n"
                    "dim = scd2_apply(dim, [{'natural_key': 'c1', 'attrs': {'country': 'ZA'}},\n"
                    "                       {'natural_key': 'c2', 'attrs': {'country': 'KE'}}], '2026-06-01')\n"
                    "assert len(dim) == 3\n"
                    "old = next(r for r in dim if r['natural_key'] == 'c1' and not r['is_current'])\n"
                    "new = next(r for r in dim if r['natural_key'] == 'c1' and r['is_current'])\n"
                    "assert old['valid_to'] == '2026-06-01' and old['attrs']['country'] == 'ZW'\n"
                    "assert new['valid_from'] == '2026-06-01' and new['attrs']['country'] == 'ZA' and new['valid_to'] is None\n"
                    "c2 = next(r for r in dim if r['natural_key'] == 'c2')\n"
                    "assert c2['is_current'] and c2['valid_from'] == '2026-06-01'\n"
                    "print('PASS: SCD2 — history preserved, exactly like a dbt snapshot')\n"
                ),
                "refresher": (
"**Three cases, strict order:**\n\n"
"```python\nfor u in updates:\n    current = next((r for r in dim\n                    if r['natural_key'] == u['natural_key']\n                    and r['is_current']), None)\n    if current is None:               # new key -> insert current\n        dim.append({... valid_from: today, valid_to: None, is_current: True})\n    elif current['attrs'] == u['attrs']:  # unchanged -> no-op\n        continue\n    else:                              # changed -> close + insert\n        current['valid_to'] = today\n        current['is_current'] = False\n        dim.append({...new attrs, valid_from: today ...})\n```\n\n"
"The no-op case matters enormously in production: without it, every daily "
"run would version every row (change detection is often done with a hash of "
"the tracked attrs). Point-in-time lookups then read beautifully: `WHERE "
"event_date >= valid_from AND (valid_to IS NULL OR event_date < valid_to)` — "
"half-open intervals (your binary-search invariant!) prevent boundary-day "
"double matches. In SQL this whole function is a MERGE (or dbt snapshot); "
"you now know exactly what those tools do."
                ),
                "objectives": [
                    "Implement the close-and-insert SCD2 transition",
                    "Detect no-change to avoid version spam",
                    "Write point-in-time joins over half-open validity intervals",
                ],
                "hints": [
                    "Find the current row for the key first; None → plain insert.",
                    "Compare attrs dicts for equality — equal means skip entirely.",
                    "On change: mutate old row's valid_to/is_current, then append the new version.",
                ],
                "resources": [
                    {"title": "Kimball: slowly changing dimensions", "url": "https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-2/"},
                    {"title": "dbt snapshots (SCD2 as a service)", "url": "https://docs.getdbt.com/docs/build/snapshots"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"Model this business in a star schema: a streaming service wants analytics on "
"'plays' — who watched what, when, on which device, how long. Walk through "
"grain, facts, dimensions, and one deliberate trade-off."
                ),
                "difficulty": "Medium",
                "topics": ["dimensional modeling", "grain"],
                "answer": (
"Grain: **one row per playback session** (user × title × device × start "
"time). fact_plays: surrogate FKs (user_key, title_key, device_key, "
"date_key, time_key), measures: seconds_watched, completed_flag, "
"pause_count. Dimensions: dim_user (SCD2 on plan/country), dim_title "
"(denormalize series/season/genre — yes, redundantly), dim_device, dim_date. "
"Trade-off to name: session grain vs *event* grain (play/pause/seek events). "
"Event grain preserves everything but is 100x bigger and most questions are "
"session-level — so land events in a raw table and build the session fact "
"from them, keeping both."
                ),
                "explanation": (
"Interviewers grade the *process*: declare grain FIRST, derive measures "
"(additive across which dimensions? seconds_watched sums everywhere; "
"completed_flag sums to a count), justify denormalization (joins cost more "
"than storage in analytics), and SCD2 where history matters (plan changes — "
"'revenue by plan at time of play'). The raw-events-plus-derived-fact answer "
"shows you know the medallion pattern before it's named (Stage 7). Common "
"failure the question hunts for: putting seconds_watched in dim_title or "
"mixing per-session and per-event rows in one table."
                ),
            },
            {
                "question": (
"Your fact table references dim_customer via natural key (email). A customer "
"changes email; also, marketing wants last year's revenue attributed to the "
"customer's country *at purchase time*. What breaks, and how do surrogate "
"keys + SCD2 fix both?"
                ),
                "difficulty": "Medium",
                "topics": ["surrogate keys", "SCD2"],
                "answer": (
"Natural-key references break twice: the email change orphans historical "
"facts (or forces cascading updates through billions of rows), and a single "
"customer row can only hold ONE country — so 'country at purchase time' is "
"unanswerable once they move. Fix: dimension rows get surrogate keys and "
"SCD2 versioning; each fact stores the surrogate key of the version current "
"*at event time*. The email change becomes a new version (facts untouched); "
"the attribution query is a plain join — each fact already points at the "
"historically-correct country. Current-state questions use `is_current = "
"TRUE` or join through the natural key."
                ),
                "explanation": (
"This is the whole argument for surrogate keys compressed into one scenario: "
"immutability of facts, mutability of descriptions, history as versioned "
"rows. Worth adding in an interview: the loader resolves 'which version was "
"current at event_time' during fact insertion (a range join on "
"valid_from/valid_to — the half-open intervals from the exercise), and "
"late-arriving facts are the spicy edge case — they must look up *historical* "
"versions, which is why valid_to must be maintained precisely, not just "
"is_current flags."
                ),
            },
            {
                "question": (
"When would you choose a normalized (3NF/snowflake) warehouse over a star "
"schema — and what did wide-column cloud warehouses change about this "
"debate?"
                ),
                "difficulty": "Hard",
                "topics": ["modeling trade-offs", "modern warehouses"],
                "answer": (
"Choose more normalization when: many source systems must be integrated "
"consistently (an enterprise 'integration layer' feeding multiple marts), "
"heavy dimension churn makes denormalized updates expensive, or strict "
"single-source-of-truth governance outweighs query convenience — the classic "
"Inmon-style core with Kimball-style marts on top. What changed: columnar "
"cloud warehouses (Snowflake/BigQuery/Redshift) made storage cheap and wide "
"scans fast, so the *cost* of star-schema redundancy collapsed; "
"simultaneously, cheap compute made even 'one big table' (fully denormalized) "
"viable for many teams, with dbt rebuilding it declaratively from staged "
"models. Dimensional thinking survives as the *semantic* discipline — grain, "
"conformed dimensions, SCD — even when the physical layout is one wide "
"table."
                ),
                "explanation": (
"A senior-level question about judgment, not recall. The strong answer "
"refuses absolutism: normalization serves write-side integration, "
"dimensional serves read-side clarity, and modern stacks often layer them "
"(staging → core → marts). Nodding to 'one big table' shows currency; "
"insisting grain/SCD still matter regardless of layout shows depth. If "
"pushed for a rule of thumb: model the *semantics* dimensionally, let the "
"warehouse's economics pick the physical shape, and never let 'storage is "
"cheap' excuse an undeclared grain."
                ),
            },
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "migration-master",
        "title": "Migration Master",
        "tagline": "Schema evolution, zero-downtime changes, and bulletproof upserts",
        "level": "Advanced",
        "tech": ["migrations", "ALTER TABLE", "zero-downtime patterns", "MERGE/upsert", "backfills"],
        "est_hours": 6,
        "brief": (
            "Schemas change weekly in real teams; doing it without breaking "
            "running systems is a core professional skill (and a favorite "
            "interview scenario). Build a mini migration tool — versioned, "
            "ordered, recorded SQL files, exactly like Alembic/Flyway — then "
            "practice the dangerous moves on the live warehouse: adding NOT NULL "
            "columns, backfilling a billion-row table in batches, and the "
            "expand-migrate-contract dance for renames."
        ),
        "milestones": [
            "Build migrate.py: applies databases/migrations/V###__name.sql files in order, records them in a schema_migrations table, skips already-applied ones — run it twice to prove idempotency.",
            "Write V001: add customers.email (nullable) — then backfill emails in 500-row batches with a loop that sleeps between batches, then V002: SET NOT NULL.",
            "Do a zero-downtime 'rename': V003 adds new column, trigger/dual-write keeps both in sync, backfill copies old→new, V004 drops the old — document each phase's rollback.",
            "Practice MERGE-style loads: upsert a 10k-row daily delta into customers with INSERT..ON CONFLICT DO UPDATE, verifying rerun-safety (count unchanged).",
            "Break it on purpose: attempt an ALTER that rewrites the table (type change) with a concurrent SELECT running — observe the lock; then find the safe pattern.",
        ],
        "under_the_hood": (
            "**Why migrations are files, not clicks:** the schema is code — "
            "versioned, reviewed, reproducible from zero. Tools (Alembic, Flyway, "
            "dbt) all share the same skeleton you're building: ordered scripts + "
            "a ledger table + 'apply the missing ones' — your topo-sort/state-"
            "machine skills from Airflow's internals, applied to DDL.\n\n"
            "**Locks are the danger.** Most ALTERs take brief metadata locks, but "
            "some (type changes, adding NOT NULL columns pre-PG11 style) rewrite "
            "the whole table while holding ACCESS EXCLUSIVE — blocking every "
            "reader and writer for the duration. Hence the professional patterns: "
            "add nullable → backfill in batches → add constraint NOT VALID → "
            "VALIDATE (brief locks only); CREATE INDEX CONCURRENTLY; and "
            "**expand-migrate-contract** for anything breaking: add the new "
            "shape, dual-write, migrate readers, only then remove the old. Every "
            "phase is individually deployable and reversible.\n\n"
            "**Backfills are ETL jobs in disguise:** batch them (pw-3), make them "
            "idempotent and resumable (ww-3 + watermarks — formalized in Stage "
            "6's CDC project), and throttle them so production traffic wins."
        ),
        "exercises": [
            {
                "id": "mm-1",
                "title": "A tiny migration engine",
                "instructions": (
"Build the heart of Alembic/Flyway in 25 lines.\n\n**Your task**\n\nImplement "
"`apply_migrations(conn, migrations)` where migrations is a list of (version, "
"sql) tuples, possibly unordered. Requirements: ensure a `schema_migrations"
"(version TEXT PRIMARY KEY)` ledger exists; apply unapplied migrations in "
"version order; record each in the ledger; skip applied ones. Return the list "
"of versions applied THIS run. Rerunning must return []."
                ),
                "starter_code": (
                    "import sqlite3\n\n"
                    "conn = sqlite3.connect(':memory:')\n\n"
                    "def apply_migrations(conn, migrations):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "migs = [('V002', 'ALTER TABLE t ADD COLUMN b INT'),\n"
                    "        ('V001', 'CREATE TABLE t(a INT)')]\n"
                    "applied = apply_migrations(conn, migs)\n"
                    "assert applied == ['V001', 'V002'], applied\n"
                    "assert apply_migrations(conn, migs) == []\n"
                    "migs.append(('V003', 'ALTER TABLE t ADD COLUMN c INT'))\n"
                    "assert apply_migrations(conn, migs) == ['V003']\n"
                    "cols = [r[1] for r in conn.execute('PRAGMA table_info(t)')]\n"
                    "assert cols == ['a', 'b', 'c']\n"
                    "print('PASS: ordered, ledgered, idempotent — you built Flyway-in-miniature')\n"
                ),
                "refresher": (
"**The ledger pattern** appears everywhere in data engineering — migrations, "
"processed-file tracking, CDC watermarks: durable record of 'what has been "
"done' so re-running does only the delta:\n\n"
"```python\nconn.execute('CREATE TABLE IF NOT EXISTS schema_migrations'\n             '(version TEXT PRIMARY KEY)')\ndone = {r[0] for r in conn.execute(\n        'SELECT version FROM schema_migrations')}\nfor version, sql in sorted(migrations):\n    if version in done:\n        continue\n    conn.executescript(sql)\n    conn.execute('INSERT INTO schema_migrations VALUES (?)', (version,))\n```\n\n"
"Sorting makes order deterministic regardless of discovery order (file "
"listings lie); the PRIMARY KEY on version makes double-recording impossible "
"(the DB enforces your invariant — always prefer that to app-side "
"discipline). Production tools add: checksums to detect edited-after-apply "
"scripts, per-migration transactions (DDL is transactional in Postgres — a "
"failed migration rolls back cleanly!), and down-migrations. You now "
"understand every one of those features from the inside."
                ),
                "objectives": [
                    "Implement the ledger + delta-apply pattern",
                    "Make schema evolution deterministic and idempotent",
                    "Map your engine onto Alembic/Flyway features",
                ],
                "hints": [
                    "CREATE TABLE IF NOT EXISTS the ledger first; read applied versions into a set.",
                    "sorted(migrations) orders by version string; skip members of the set.",
                    "Use executescript (SQL may be multi-statement); record the version after applying.",
                ],
                "resources": [
                    {"title": "Alembic (SQLAlchemy migrations)", "url": "https://alembic.sqlalchemy.org/en/latest/"},
                    {"title": "PostgreSQL: transactional DDL", "url": "https://wiki.postgresql.org/wiki/Transactional_DDL_in_PostgreSQL:_A_Competitive_Analysis"},
                ],
            },
            {
                "id": "mm-2",
                "title": "Resumable batched backfill",
                "instructions": (
"The billion-row problem: you can't UPDATE it in one go.\n\n**Your task**\n\n"
"Implement `backfill(conn, batch_size, compute_fn)` for the seeded table "
"`users(id, name, email)` where email is NULL: repeatedly take up to "
"batch_size rows WHERE email IS NULL ORDER BY id, set email = "
"compute_fn(name), commit per batch, until none remain. Return the number of "
"batches. It must be **resumable**: killed halfway (simulated by the checker "
"calling it after a partial manual run), a fresh call completes the rest "
"without touching finished rows (the checker counts compute_fn calls!)."
                ),
                "starter_code": (
                    "import sqlite3\n\n"
                    "conn = sqlite3.connect(':memory:')\n"
                    "conn.execute('CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT, email TEXT)')\n"
                    "conn.executemany('INSERT INTO users(name) VALUES (?)',\n"
                    "                 [(f'user{i}',) for i in range(10)])\n\n"
                    "def backfill(conn, batch_size, compute_fn):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "calls = {'n': 0}\n"
                    "def mk_email(name):\n"
                    "    calls['n'] += 1\n"
                    "    return name + '@example.com'\n"
                    "# simulate a previous partially-completed run:\n"
                    "conn.execute(\"UPDATE users SET email = name || '@example.com' WHERE id <= 4\")\n"
                    "batches = backfill(conn, 3, mk_email)\n"
                    "assert batches == 2, batches\n"
                    "assert calls['n'] == 6, f'must only compute for unfilled rows, got {calls[\"n\"]}'\n"
                    "left = conn.execute('SELECT COUNT(*) FROM users WHERE email IS NULL').fetchone()[0]\n"
                    "assert left == 0\n"
                    "assert backfill(conn, 3, mk_email) == 0, 'nothing left -> zero batches'\n"
                    "print('PASS: resumable batched backfill — the only safe way to touch huge tables')\n"
                ),
                "refresher": (
"**The WHERE-clause-as-checkpoint trick.** Selecting `WHERE email IS NULL` "
"makes the *data itself* the progress ledger — no separate bookkeeping, "
"automatic resume:\n\n"
"```python\nwhile True:\n    rows = conn.execute(\n        'SELECT id, name FROM users WHERE email IS NULL '\n        'ORDER BY id LIMIT ?', (batch_size,)).fetchall()\n    if not rows:\n        return batches\n    for id_, name in rows:\n        conn.execute('UPDATE users SET email=? WHERE id=?',\n                     (compute_fn(name), id_))\n    conn.commit()\n    batches += 1\n```\n\n"
"Each committed batch shrinks the remaining set; a crash costs at most one "
"batch of redone (idempotent!) work. On real Postgres add: ORDER BY id keeps "
"batches index-friendly and lock-local; a short sleep between batches yields "
"to production traffic; and monitor replication lag if replicas exist. The "
"same shape — *select unprocessed, process, mark, repeat* — is a work queue, "
"is your Stage-6 incremental loader, is every safe bulk operation you'll "
"ever run at 3am with the pager nearby."
                ),
                "objectives": [
                    "Use data-state as the resume checkpoint",
                    "Batch with per-batch commits for bounded failure cost",
                    "Recognize select-process-mark as the universal safe-bulk-op loop",
                ],
                "hints": [
                    "Loop: fetch LIMIT batch_size of NULL-email rows; empty → done.",
                    "Update each fetched row by id, commit once per batch, count batches.",
                    "Don't precompute the full list upfront — refetch each iteration (that's what makes it resumable).",
                ],
                "resources": [
                    {"title": "Safe Postgres operations (strong-migrations concept)", "url": "https://github.com/ankane/strong_migrations"},
                    {"title": "PostgreSQL: lock levels per command", "url": "https://www.postgresql.org/docs/current/explicit-locking.html"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"You must rename a heavily-used column `users.fullname` → `display_name` with "
"zero downtime, while old and new application versions run simultaneously "
"during deploy. Give the full sequence."
                ),
                "difficulty": "Hard",
                "topics": ["zero-downtime", "expand-migrate-contract"],
                "answer": (
"Expand-migrate-contract: **(1) Expand** — `ALTER TABLE users ADD COLUMN "
"display_name TEXT` (instant, nullable); deploy a trigger (or app dual-write) "
"syncing fullname → display_name on insert/update. **(2) Backfill** — copy "
"fullname to display_name in batches (resumable, throttled). **(3) Migrate "
"readers** — deploy app versions reading display_name (writes still dual). "
"**(4) Contract** — once no code references fullname: drop the trigger, then "
"`ALTER TABLE users DROP COLUMN fullname`. Each step is independently "
"deployable and reversible; at every instant, both old and new app versions "
"function."
                ),
                "explanation": (
"A literal `RENAME COLUMN` is metadata-fast but *atomically breaks* every "
"deployed reader of the old name — impossible during rolling deploys. The "
"sequence works because compatibility is maintained pairwise at each phase "
"transition. Points interviewers listen for: the trigger/dual-write closing "
"the write gap during backfill; batched resumable backfill (never one giant "
"UPDATE — locks + bloat); waiting a full deploy cycle before contract; and "
"rollback stories per phase (drop the new column, nothing lost, at any point "
"before contract). This pattern generalizes to type changes, table splits, "
"and cross-database moves — say that."
                ),
            },
            {
                "question": (
"Compare INSERT ... ON CONFLICT DO UPDATE (upsert) with DELETE-then-INSERT "
"and with MERGE for loading a daily snapshot into a warehouse table. When is "
"each appropriate, and what concurrency hazards does each carry?"
                ),
                "difficulty": "Medium",
                "topics": ["upserts", "MERGE", "loading patterns"],
                "answer": (
"**ON CONFLICT DO UPDATE**: row-level, atomic per row, needs a unique "
"constraint as the conflict target; ideal for incremental deltas; hazard: "
"concurrent upserts still lock rows (deadlock-order discipline applies), and "
"it can't delete rows that vanished from the source. **DELETE+INSERT** (or "
"TRUNCATE+load) of a partition/day: simplest full-refresh semantics, handles "
"deletions naturally; do it in one transaction so readers never see the "
"empty middle state; hazard: bloat from the delete and a long transaction on "
"big days. **MERGE** (PG15+): one statement expressing "
"matched-update/not-matched-insert/not-matched-by-source-delete — the full "
"snapshot reconciliation; hazard: pre-PG17 MERGE had weaker concurrency "
"guarantees than ON CONFLICT under races, so serialize writers per table."
                ),
                "explanation": (
"The meta-answer: choose by *delta semantics*. Append-only feeds → plain "
"idempotent INSERT ON CONFLICT DO NOTHING; upsert feeds without deletes → ON "
"CONFLICT DO UPDATE; true snapshots including disappearances → partition "
"swap or MERGE. Every option must pass the run-it-twice test (ww-3 — say "
"'idempotent' out loud). The partition-swap variant (load a fresh table, "
"atomic rename) deserves a mention as the zero-bloat, zero-lock heavyweight "
"champion for full refreshes — it's the create-and-swap trick, again, "
"because it's always the trick."
                ),
            },
            {
                "question": (
"A migration added an index with CREATE INDEX (not CONCURRENTLY) on a 200M-"
"row hot table and production writes froze for 40 minutes. Explain what "
"happened, the correct approach, and its extra failure mode."
                ),
                "difficulty": "Medium",
                "topics": ["locking", "CREATE INDEX CONCURRENTLY"],
                "answer": (
"Plain CREATE INDEX holds a SHARE lock for the whole build: reads proceed, "
"but ALL writes (INSERT/UPDATE/DELETE) block until the index finishes — 40 "
"minutes of frozen writes on a hot table. Correct: `CREATE INDEX "
"CONCURRENTLY`, which builds in phases with only brief weak locks, letting "
"writes continue (it scans the table twice and waits out existing "
"transactions, so it's slower overall). Its failure mode: if the build "
"fails (deadlock, duplicate violation on a UNIQUE build), it leaves an "
"INVALID index that consumes write overhead but serves no queries — you "
"must detect (pg_index.indisvalid) and DROP + retry. Also: CONCURRENTLY "
"can't run inside a transaction block, so migration tools need special "
"handling for it."
                ),
                "explanation": (
"A war-story question checking operational literacy. The lock taxonomy is "
"the core (SHARE blocks writes, not reads); the INVALID-index gotcha and the "
"no-transaction constraint are the details that prove hands-on experience. "
"Worth volunteering: long-running existing transactions delay CONCURRENTLY "
"indefinitely (it must wait for snapshots that predate it), so check "
"pg_stat_activity first — tying back to MVCC. And the meta-lesson for the "
"migration tool: classify migrations as 'safe online' vs 'needs window', "
"and make the dangerous ones opt-in explicit — process guards beat memory."
                ),
            },
        ],
    },
]
