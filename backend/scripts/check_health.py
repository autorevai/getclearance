#!/usr/bin/env python3
"""
Health check script for monitoring service connectivity.

Usage:
    cd backend
    python -m scripts.check_health

Exit codes:
    0 - All services healthy
    1 - One or more services unhealthy

Output format: JSON for easy parsing by monitoring tools.
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


async def check_database() -> dict[str, Any]:
    """Check PostgreSQL database connectivity."""
    start = time.monotonic()
    try:
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine
        from app.config import settings

        engine = create_async_engine(settings.database_url_async)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.fetchone()
        await engine.dispose()

        latency_ms = round((time.monotonic() - start) * 1000)
        return {
            "status": "ok",
            "latency_ms": latency_ms,
        }
    except ImportError as e:
        return {
            "status": "error",
            "error": f"Missing dependency: {e}",
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "latency_ms": round((time.monotonic() - start) * 1000),
        }


async def check_redis() -> dict[str, Any]:
    """Check Redis connectivity."""
    start = time.monotonic()
    try:
        import redis.asyncio as redis
        from app.config import settings

        client = redis.from_url(settings.redis_url_str)
        await client.ping()
        await client.aclose()

        latency_ms = round((time.monotonic() - start) * 1000)
        return {
            "status": "ok",
            "latency_ms": latency_ms,
        }
    except ImportError as e:
        return {
            "status": "error",
            "error": f"Missing dependency: {e}",
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "latency_ms": round((time.monotonic() - start) * 1000),
        }


async def check_r2_storage() -> dict[str, Any]:
    """Check Cloudflare R2 storage connectivity."""
    start = time.monotonic()
    try:
        import aioboto3
        from app.config import settings

        if not settings.r2_access_key_id or not settings.r2_endpoint:
            return {
                "status": "skipped",
                "reason": "R2 credentials not configured",
            }

        session = aioboto3.Session()
        async with session.client(
            's3',
            endpoint_url=settings.r2_endpoint,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name='auto',  # R2 requires 'auto' as region
        ) as s3:
            # List objects is more reliable than head_bucket for R2
            await s3.list_objects_v2(Bucket=settings.r2_bucket, MaxKeys=1)

        latency_ms = round((time.monotonic() - start) * 1000)
        return {
            "status": "ok",
            "bucket": settings.r2_bucket,
            "latency_ms": latency_ms,
        }
    except ImportError as e:
        return {
            "status": "error",
            "error": f"Missing dependency: {e}",
        }
    except Exception as e:
        error_msg = str(e)
        # Handle common S3 errors gracefully
        if "NoSuchBucket" in error_msg:
            return {
                "status": "error",
                "error": f"Bucket '{settings.r2_bucket}' does not exist",
            }
        if "AccessDenied" in error_msg or "403" in error_msg:
            return {
                "status": "error",
                "error": "Access denied - check R2 credentials",
            }
        return {
            "status": "error",
            "error": error_msg,
            "latency_ms": round((time.monotonic() - start) * 1000),
        }


async def check_opensanctions() -> dict[str, Any]:
    """Check OpenSanctions API connectivity."""
    start = time.monotonic()
    try:
        import httpx
        from app.config import settings

        if not settings.opensanctions_api_key:
            return {
                "status": "skipped",
                "reason": "OpenSanctions API key not configured",
            }

        # Use a simple test query
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.opensanctions_api_url,
                headers={
                    "Authorization": f"ApiKey {settings.opensanctions_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "queries": {
                        "test": {
                            "schema": "Person",
                            "properties": {
                                "name": ["Health Check Test"],
                            },
                        }
                    }
                },
            )
            response.raise_for_status()

        latency_ms = round((time.monotonic() - start) * 1000)
        return {
            "status": "ok",
            "latency_ms": latency_ms,
        }
    except ImportError as e:
        return {
            "status": "error",
            "error": f"Missing dependency: {e}",
        }
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "403" in error_msg:
            return {
                "status": "error",
                "error": "Authentication failed - check API key",
            }
        if "timeout" in error_msg.lower():
            return {
                "status": "error",
                "error": "Request timed out",
                "latency_ms": round((time.monotonic() - start) * 1000),
            }
        return {
            "status": "error",
            "error": error_msg,
            "latency_ms": round((time.monotonic() - start) * 1000),
        }


async def check_anthropic() -> dict[str, Any]:
    """Check Anthropic (Claude) API connectivity."""
    start = time.monotonic()
    try:
        from app.config import settings

        if not settings.anthropic_api_key:
            return {
                "status": "skipped",
                "reason": "Anthropic API key not configured",
            }

        # Just verify the API key format and basic connectivity
        # We don't make an actual API call to avoid costs
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check if API is reachable (not a full completion request)
            response = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                },
            )
            # 401 means key is invalid, 200 means valid
            if response.status_code == 401:
                return {
                    "status": "error",
                    "error": "Invalid API key",
                }

        latency_ms = round((time.monotonic() - start) * 1000)
        return {
            "status": "ok",
            "latency_ms": latency_ms,
        }
    except ImportError as e:
        return {
            "status": "error",
            "error": f"Missing dependency: {e}",
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "latency_ms": round((time.monotonic() - start) * 1000),
        }


async def run_all_checks(verbose: bool = False) -> dict[str, Any]:
    """Run all health checks concurrently."""
    checks = {
        "database": check_database(),
        "redis": check_redis(),
        "r2_storage": check_r2_storage(),
        "opensanctions": check_opensanctions(),
        "anthropic": check_anthropic(),
    }

    results = {}
    for name, coro in checks.items():
        if verbose:
            print(f"Checking {name}...", end=" ", flush=True)
        results[name] = await coro
        if verbose:
            status = results[name]["status"]
            print(f"[{status.upper()}]")

    # Determine overall status
    # - "healthy" if all critical services (database, redis) are ok
    # - "degraded" if optional services are down
    # - "unhealthy" if critical services are down
    critical_services = ["database", "redis"]
    optional_services = ["r2_storage", "opensanctions", "anthropic"]

    critical_ok = all(
        results[s]["status"] in ("ok", "skipped")
        for s in critical_services
    )
    optional_ok = all(
        results[s]["status"] in ("ok", "skipped")
        for s in optional_services
    )

    if critical_ok and optional_ok:
        overall_status = "healthy"
    elif critical_ok:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "checks": results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Check health of all services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
    0 - All services healthy or degraded (optional services down)
    1 - Critical services unhealthy (database or redis)

Examples:
    python -m scripts.check_health
    python -m scripts.check_health --verbose
    python -m scripts.check_health --quiet  # Just exit code
        """
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show progress as checks run"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress output (only return exit code)"
    )
    parser.add_argument(
        "--pretty", "-p",
        action="store_true",
        help="Pretty-print JSON output"
    )

    args = parser.parse_args()

    result = asyncio.run(run_all_checks(verbose=args.verbose))

    if not args.quiet:
        if args.pretty:
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps(result))

    # Exit with appropriate code
    if result["status"] == "unhealthy":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
