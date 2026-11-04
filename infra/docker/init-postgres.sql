-- PostgreSQL initialization script for AgentForge

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database (handled by POSTGRES_DB env var)
-- CREATE DATABASE agentforge;

-- Create user (handled by POSTGRES_USER env var)
-- CREATE USER agentforge WITH PASSWORD 'agentforge_dev';
-- GRANT ALL PRIVILEGES ON DATABASE agentforge TO agentforge;

-- Set default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO agentforge;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO agentforge;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO agentforge;

-- Create schemas for different purposes
CREATE SCHEMA IF NOT EXISTS agentforge;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Grant usage on schemas
GRANT USAGE ON SCHEMA agentforge TO agentforge;
GRANT USAGE ON SCHEMA monitoring TO agentforge;

-- Set search path
ALTER DATABASE agentforge SET search_path = agentforge, public;

-- Create monitoring user
CREATE USER monitoring WITH PASSWORD 'monitoring_password';
GRANT CONNECT ON DATABASE agentforge TO monitoring;
GRANT USAGE ON SCHEMA public TO monitoring;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO monitoring;

-- Performance settings
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Reload configuration
SELECT pg_reload_conf();