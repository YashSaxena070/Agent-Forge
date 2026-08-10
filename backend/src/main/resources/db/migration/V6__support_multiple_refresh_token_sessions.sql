ALTER TABLE refresh_tokens
    DROP CONSTRAINT IF EXISTS uk_refresh_tokens_user_id;

ALTER TABLE refresh_tokens
    DROP CONSTRAINT IF EXISTS refresh_tokens_user_id_key;

ALTER TABLE refresh_tokens
    ADD COLUMN IF NOT EXISTS device_name VARCHAR(255);

ALTER TABLE refresh_tokens
    ADD COLUMN IF NOT EXISTS device_type VARCHAR(50);

ALTER TABLE refresh_tokens
    ADD COLUMN IF NOT EXISTS user_agent TEXT;

ALTER TABLE refresh_tokens
    ADD COLUMN IF NOT EXISTS ip_address VARCHAR(100);

ALTER TABLE refresh_tokens
    ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_refresh_token_token
    ON refresh_tokens(token);

CREATE INDEX IF NOT EXISTS idx_refresh_token_user
    ON refresh_tokens(user_id);