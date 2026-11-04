CREATE TABLE IF NOT EXISTS audit_logs (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    actor_id UUID,
    actor_type VARCHAR(50) NOT NULL,
    actor_ip VARCHAR(45),
    actor_user_agent TEXT,
    resource_type VARCHAR(100),
    resource_id UUID,
    resource_name VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    outcome VARCHAR(20) NOT NULL,
    request_id VARCHAR(255),
    session_id VARCHAR(255),
    correlation_id VARCHAR(255),
    details_json JSONB DEFAULT '{}',
    risk_score INT DEFAULT 0,
    risk_factors_json JSONB DEFAULT '[]',
    compliance_tags_json JSONB DEFAULT '[]',
    data_classification VARCHAR(50),
    previous_hash VARCHAR(64),
    event_hash VARCHAR(64) UNIQUE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_logs(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_compliance ON audit_logs USING GIN (compliance_tags_json);
CREATE INDEX IF NOT EXISTS idx_audit_actor_time ON audit_logs(actor_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_resource_time ON audit_logs(resource_type, resource_id, timestamp);

CREATE TABLE IF NOT EXISTS mfa_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    method_type VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending_setup',
    secret_encrypted TEXT,
    secret_iv VARCHAR(64),
    backup_codes_json JSONB DEFAULT '[]',
    used_backup_codes_json JSONB DEFAULT '[]',
    credential_id VARCHAR(255) UNIQUE,
    public_key TEXT,
    sign_count BIGINT DEFAULT 0,
    aaguid VARCHAR(36),
    contact_value VARCHAR(255),
    verified_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    failed_attempts INT DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, method_type, name)
);

CREATE INDEX IF NOT EXISTS idx_mfa_user ON mfa_methods(user_id);
CREATE INDEX IF NOT EXISTS idx_mfa_credential ON mfa_methods(credential_id);
CREATE INDEX IF NOT EXISTS idx_mfa_user_type_status ON mfa_methods(user_id, method_type, status);

-- Add MFA columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_password_change TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_history JSONB DEFAULT '[]';
ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INT DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_ip VARCHAR(45);