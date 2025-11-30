-- Get Clearance - Database Initialization
-- This runs when PostgreSQL container first starts
-- Tables are created by Alembic migrations (alembic upgrade head)

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text matching

-- Grant search_path for app schema
GRANT USAGE ON SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Note: Run these commands after Alembic migrations to seed dev data:
--
-- INSERT INTO tenants (id, name, slug, plan, status)
-- VALUES (
--     '00000000-0000-0000-0000-000000000001',
--     'Demo Company',
--     'demo',
--     'starter',
--     'active'
-- ) ON CONFLICT DO NOTHING;
--
-- INSERT INTO users (id, tenant_id, email, name, role, auth0_id)
-- VALUES (
--     '00000000-0000-0000-0000-000000000002',
--     '00000000-0000-0000-0000-000000000001',
--     'admin@demo.getclearance.com',
--     'Demo Admin',
--     'admin',
--     'dev-user-123'
-- ) ON CONFLICT DO NOTHING;
