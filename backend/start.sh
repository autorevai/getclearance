#!/bin/bash
set -e

# Railway sets PORT, but we need to ensure consistency
export PORT=${PORT:-8000}

echo "🚀 Starting GetClearance Backend..."
echo "   Environment: ${ENVIRONMENT:-development}"
echo "   Port: ${PORT}"

# Fix alembic version if needed (one-time fix for migration conflict)
echo "📦 Checking database migrations..."
python -c "
from sqlalchemy import create_engine, text
import os

db_url = os.environ.get('DATABASE_URL', '')
if db_url:
    # Remove asyncpg driver for sync operations
    db_url = db_url.replace('+asyncpg', '')
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Check current version
            result = conn.execute(text('SELECT version_num FROM alembic_version'))
            current = result.scalar()
            print(f'   Current alembic version: {current}')

            # If stuck on non-existent migration 005, fix it
            if current == '005':
                conn.execute(text('DELETE FROM alembic_version'))
                conn.execute(text(\"INSERT INTO alembic_version (version_num) VALUES ('004')\"))
                conn.commit()
                print('   ✓ Fixed alembic version (005 -> 004)')
    except Exception as e:
        print(f'   Note: Could not check alembic version: {e}')
"

# Run migrations
echo "📦 Running database migrations..."
alembic upgrade head
echo "   ✓ Migrations complete"

# Start the server
echo "🌐 Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
