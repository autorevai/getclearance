"""
Get Clearance - WebSocket Handler
==================================
Real-time updates via WebSocket connections.

Clients connect to /ws with a JWT token as a query parameter.
Events are broadcast to all connections within the same tenant.
"""

import asyncio
import json
import logging
from typing import Optional
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect, Query, HTTPException, status
from jose import jwt, JWTError
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections grouped by tenant.

    Provides:
    - Connection tracking per tenant
    - Broadcast to all connections within a tenant
    - Heartbeat/ping support
    """

    def __init__(self):
        # Map: tenant_id -> list of WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, tenant_id: str) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            if tenant_id not in self.active_connections:
                self.active_connections[tenant_id] = []
            self.active_connections[tenant_id].append(websocket)
        logger.info(f"WebSocket connected for tenant {tenant_id[:8]}...")

    async def disconnect(self, websocket: WebSocket, tenant_id: str) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            if tenant_id in self.active_connections:
                if websocket in self.active_connections[tenant_id]:
                    self.active_connections[tenant_id].remove(websocket)
                # Clean up empty tenant lists
                if not self.active_connections[tenant_id]:
                    del self.active_connections[tenant_id]
        logger.info(f"WebSocket disconnected for tenant {tenant_id[:8]}...")

    async def broadcast_to_tenant(self, tenant_id: str, message: dict) -> None:
        """Send a message to all connections for a tenant."""
        if tenant_id not in self.active_connections:
            return

        # Copy list to avoid modification during iteration
        connections = list(self.active_connections.get(tenant_id, []))

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                # Remove dead connections
                await self.disconnect(connection, tenant_id)

    async def send_personal(self, websocket: WebSocket, message: dict) -> None:
        """Send a message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send personal WebSocket message: {e}")

    def get_connection_count(self, tenant_id: Optional[str] = None) -> int:
        """Get number of active connections."""
        if tenant_id:
            return len(self.active_connections.get(tenant_id, []))
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager instance
manager = ConnectionManager()


# Cache for JWKS keys
_jwks_cache: dict = {}
_jwks_cache_time: float = 0


async def get_jwks() -> dict:
    """Fetch and cache Auth0 JWKS keys."""
    global _jwks_cache, _jwks_cache_time
    import time

    # Cache for 1 hour
    if _jwks_cache and (time.time() - _jwks_cache_time) < 3600:
        return _jwks_cache

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.auth0_jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
            _jwks_cache_time = time.time()
            return _jwks_cache
    except Exception as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        if _jwks_cache:
            return _jwks_cache
        raise


async def verify_websocket_token(token: str) -> dict:
    """
    Verify JWT token and extract tenant_id.

    Returns dict with user_id and tenant_id if valid.
    Raises HTTPException if invalid.
    """
    try:
        # Get JWKS for verification
        jwks = await get_jwks()

        # Get the key ID from token header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Find the matching key
        rsa_key = {}
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
                break

        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token key",
            )

        # Verify the token
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=settings.auth0_algorithms,
            audience=settings.auth0_audience,
            issuer=settings.auth0_issuer,
        )

        # Extract tenant_id from custom claims
        tenant_id = payload.get("https://getclearance.dev/tenant_id")
        user_id = payload.get("sub")

        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenant_id in token",
            )

        return {
            "user_id": user_id,
            "tenant_id": tenant_id,
        }

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
        )


async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT token for authentication"),
):
    """
    WebSocket endpoint for real-time updates.

    Connect: ws://host/ws?token=<jwt_token>

    Events sent to client:
    - applicant.created / applicant.updated / applicant.reviewed
    - screening.completed
    - document.processed
    - case.created / case.resolved
    - ping (heartbeat)
    """
    tenant_id = None

    try:
        # Verify token and get tenant_id
        auth_info = await verify_websocket_token(token)
        tenant_id = auth_info["tenant_id"]

        # Connect
        await manager.connect(websocket, tenant_id)

        # Send connection confirmation
        await manager.send_personal(websocket, {
            "type": "connected",
            "message": "WebSocket connection established",
        })

        # Keep connection alive and listen for messages
        while True:
            try:
                # Wait for any message (or disconnect)
                # The client doesn't need to send messages, but we need to detect disconnects
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0  # Ping timeout
                )

                # Handle client messages (mostly for pong responses)
                try:
                    message = json.loads(data)
                    if message.get("type") == "pong":
                        pass  # Client responded to ping
                except json.JSONDecodeError:
                    pass

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await manager.send_personal(websocket, {"type": "ping"})
                except Exception:
                    break

    except WebSocketDisconnect:
        logger.debug(f"WebSocket disconnected normally for tenant {tenant_id[:8] if tenant_id else 'unknown'}...")
    except HTTPException as e:
        # Auth failed - close with appropriate code
        logger.warning(f"WebSocket auth failed: {e.detail}")
        await websocket.close(code=4001, reason=e.detail)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal error")
    finally:
        if tenant_id:
            await manager.disconnect(websocket, tenant_id)


# Event broadcasting helper functions
async def broadcast_applicant_created(tenant_id: str, applicant_id: str) -> None:
    """Broadcast applicant created event."""
    await manager.broadcast_to_tenant(tenant_id, {
        "type": "applicant.created",
        "applicant_id": applicant_id,
    })


async def broadcast_applicant_updated(tenant_id: str, applicant_id: str) -> None:
    """Broadcast applicant updated event."""
    await manager.broadcast_to_tenant(tenant_id, {
        "type": "applicant.updated",
        "applicant_id": applicant_id,
    })


async def broadcast_applicant_reviewed(tenant_id: str, applicant_id: str, decision: str) -> None:
    """Broadcast applicant reviewed event."""
    await manager.broadcast_to_tenant(tenant_id, {
        "type": "applicant.reviewed",
        "applicant_id": applicant_id,
        "decision": decision,
    })


async def broadcast_screening_completed(
    tenant_id: str,
    applicant_id: str,
    hit_count: int,
) -> None:
    """Broadcast screening completed event."""
    await manager.broadcast_to_tenant(tenant_id, {
        "type": "screening.completed",
        "applicant_id": applicant_id,
        "hit_count": hit_count,
    })


async def broadcast_document_processed(tenant_id: str, applicant_id: str) -> None:
    """Broadcast document processed event."""
    await manager.broadcast_to_tenant(tenant_id, {
        "type": "document.processed",
        "applicant_id": applicant_id,
    })


async def broadcast_case_created(tenant_id: str, case_id: str) -> None:
    """Broadcast case created event."""
    await manager.broadcast_to_tenant(tenant_id, {
        "type": "case.created",
        "case_id": case_id,
    })


async def broadcast_case_resolved(tenant_id: str, case_id: str) -> None:
    """Broadcast case resolved event."""
    await manager.broadcast_to_tenant(tenant_id, {
        "type": "case.resolved",
        "case_id": case_id,
    })
