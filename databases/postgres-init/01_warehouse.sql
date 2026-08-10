-- ============================================================================
-- PyForge warehouse seed — runs automatically on first start of the postgres
-- container. A small but realistic e-commerce dataset, reused by the SQL, ETL,
-- Spark and AI projects. Safe to reset with: docker compose down -v (db data
-- lives in a volume).
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;   -- pgvector, used in Stage 9

-- ---------------------------------------------------------------- dimensions
CREATE TABLE customers (
    customer_id  SERIAL PRIMARY KEY,
    name         TEXT NOT NULL,
    country      TEXT NOT NULL,
    signup_date  DATE NOT NULL
);

CREATE TABLE products (
    product_id   SERIAL PRIMARY KEY,
    name         TEXT NOT NULL,
    category     TEXT NOT NULL,
    price        NUMERIC(10,2) NOT NULL
);

-- ---------------------------------------------------------------- facts
CREATE TABLE orders (
    order_id     SERIAL PRIMARY KEY,
    customer_id  INT NOT NULL REFERENCES customers(customer_id),
    order_date   DATE NOT NULL,
    status       TEXT NOT NULL DEFAULT 'completed'
);

CREATE TABLE order_items (
    order_id     INT NOT NULL REFERENCES orders(order_id),
    product_id   INT NOT NULL REFERENCES products(product_id),
    quantity     INT NOT NULL,
    unit_price   NUMERIC(10,2) NOT NULL,
    PRIMARY KEY (order_id, product_id)
);

-- Landing zone used by the ETL projects (Pipeline Blueprint, CDC, Airflow Pro)
CREATE TABLE raw_events (
    event_id     BIGSERIAL PRIMARY KEY,
    source       TEXT NOT NULL,
    event_type   TEXT NOT NULL,
    payload      JSONB NOT NULL,
    event_time   TIMESTAMPTZ NOT NULL,
    loaded_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Vector playground used by Vector Vault / RAG Works (Stage 9)
CREATE TABLE doc_chunks (
    chunk_id     SERIAL PRIMARY KEY,
    doc_name     TEXT NOT NULL,
    chunk_text   TEXT NOT NULL,
    embedding    vector(64)          -- small dim: fast + didactic
);

-- ---------------------------------------------------------------- seed data
-- Deterministic pseudo-random data via setseed so every learner sees the same
-- warehouse (nice for checking your query results against the course).
SELECT setseed(0.42);

INSERT INTO customers (name, country, signup_date)
SELECT
    'customer_' || g,
    (ARRAY['ZW','ZA','KE','NG','US','GB','DE','IN'])[1 + floor(random()*8)::int],
    DATE '2024-01-01' + (floor(random()*720))::int
FROM generate_series(1, 500) g;

INSERT INTO products (name, category, price)
SELECT
    'product_' || g,
    (ARRAY['electronics','books','clothing','home','sports'])[1 + floor(random()*5)::int],
    round((5 + random()*495)::numeric, 2)
FROM generate_series(1, 100) g;

INSERT INTO orders (customer_id, order_date, status)
SELECT
    1 + floor(random()*500)::int,
    DATE '2025-01-01' + (floor(random()*570))::int,
    CASE WHEN random() < 0.9 THEN 'completed'
         WHEN random() < 0.5 THEN 'cancelled'
         ELSE 'returned' END
FROM generate_series(1, 5000) g;

-- DISTINCT on the pair keeps the (order_id, product_id) primary key satisfied;
-- the join pulls each product's list price as the line's unit_price.
INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT pairs.o, pairs.p,
       1 + floor(random()*4)::int,
       pr.price
FROM (
    SELECT DISTINCT
           1 + floor(random()*5000)::int AS o,
           1 + floor(random()*100)::int  AS p
    FROM generate_series(1, 12000)
) pairs
JOIN products pr ON pr.product_id = pairs.p;

-- Helpful indexes learners will inspect with EXPLAIN in PG Warehouse
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date     ON orders(order_date);
CREATE INDEX idx_items_product   ON order_items(product_id);

ANALYZE;
