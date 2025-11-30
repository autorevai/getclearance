-- SignalWeave Database Initialization
-- This runs automatically when the postgres container starts

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text matching

-- Create initial schema (tables will be created by Alembic migrations)
-- This file is just for extensions and any bootstrap data

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE signalweave TO postgres;
