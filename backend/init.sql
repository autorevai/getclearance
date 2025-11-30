-- Get Clearance - Database Initialization
-- This runs when PostgreSQL container first starts
-- For production, use Alembic migrations instead

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text matching

-- Create development tenant
INSERT INTO tenants (id, name, slug, plan, status)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Demo Company',
    'demo',
    'starter',
    'active'
) ON CONFLICT DO NOTHING;

-- Create development admin user
INSERT INTO users (id, tenant_id, email, name, role, auth0_id)
VALUES (
    '00000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000001',
    'admin@demo.getclearance.com',
    'Demo Admin',
    'admin',
    'dev-user-123'
) ON CONFLICT DO NOTHING;

-- Grant search_path for app schema
GRANT USAGE ON SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
