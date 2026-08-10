-- Single-use OAuth state nonces (consumed after callback).
CREATE TABLE IF NOT EXISTS oauth_consumed (
    nonce       TEXT PRIMARY KEY,
    consumed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS oauth_consumed_at_idx ON oauth_consumed (consumed_at);
