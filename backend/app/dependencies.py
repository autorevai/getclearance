"""
Get Clearance - Dependency Injection
=====================================
FastAPI dependencies for authentication, authorization, and common patterns.

Dependencies provide:
- JWT token validation via Auth0
- Tenant context extraction
- User context and permissions
- Database session with tenant filtering
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.config import settings
from app.database import get_db, set_tenant_context


# ===========================================
# AUTH0 TOKEN VALIDATION
# ===========================================

# HTTP Bearer scheme for extracting tokens
security = HTTPBearer(auto_error=True)

# Cache for JWKS (refreshed periodically)
_jwks_cache: dict | None = None


class TokenPayload(BaseModel):
    """Decoded JWT token payload."""
    sub: str  # User ID (Auth0 user_id)
    aud: str | list[str]  # Audience
    iss: str  # Issuer
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    
    # Custom claims (set in Auth0 Actions/Rules)
    tenant_id: str | None = None
    email: str | None = None
    role: str | None = None
    permissions: list[str] = []


class CurrentUser(BaseModel):
    """Current authenticated user context."""
    id: str  # Auth0 user_id
    tenant_id: UUID
    email: str | None
    role: str
    permissions: list[str]


async def get_jwks() -> dict:
    """
    Fetch JWKS from Auth0 for token verification.
    
    Caches the result to avoid repeated HTTP calls.
    TODO: Add TTL-based cache refresh.
    """
    global _jwks_cache
    
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.auth0_jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
    
    return _jwks_cache


def get_signing_key(jwks: dict, kid: str) -> str:
    """
    Find the signing key in JWKS matching the token's kid.
    
    Args:
        jwks: JWKS response from Auth0
        kid: Key ID from token header
    
    Returns:
        RSA public key for verification
    
    Raises:
        HTTPException: If key not found
    """
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unable to find signing key",
    )


async def verify_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(security)],
) -> TokenPayload:
    """
    Verify and decode JWT token from Auth0.
    
    Args:
        credentials: Bearer token from Authorization header
    
    Returns:
        TokenPayload: Decoded token claims
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    # Skip validation in development if no Auth0 configured
    if settings.is_development() and not settings.auth0_domain:
        # Return mock payload for development
        return TokenPayload(
            sub="dev-user-123",
            aud=settings.auth0_audience,
            iss=settings.auth0_issuer,
            exp=9999999999,
            iat=0,
            tenant_id="00000000-0000-0000-0000-000000000001",
            email="dev@getclearance.local",
            role="admin",
            permissions=["read:applicants", "write:applicants", "admin:*"],
        )
    
    try:
        # Get unverified header to find key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing key ID",
            )
        
        # Fetch JWKS and find matching key
        jwks = await get_jwks()
        signing_key = get_signing_key(jwks, kid)
        
        # Verify and decode token
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=settings.auth0_algorithms,
            audience=settings.auth0_audience,
            issuer=settings.auth0_issuer,
        )
        
        return TokenPayload(**payload)
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )


async def get_current_user(
    token: Annotated[TokenPayload, Depends(verify_token)],
) -> CurrentUser:
    """
    Get current authenticated user from token.
    
    Args:
        token: Verified JWT token payload
    
    Returns:
        CurrentUser: User context with tenant and permissions
    
    Raises:
        HTTPException: If tenant_id not in token
    """
    if not token.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not associated with a tenant",
        )
    
    return CurrentUser(
        id=token.sub,
        tenant_id=UUID(token.tenant_id),
        email=token.email,
        role=token.role or "viewer",
        permissions=token.permissions,
    )


# ===========================================
# TENANT-SCOPED DATABASE
# ===========================================

async def get_tenant_db(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AsyncSession:
    """
    Get database session with tenant context set.
    
    This sets the PostgreSQL session variable for RLS policies.
    All queries through this session will be filtered to the user's tenant.
    
    Usage:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_tenant_db)):
            # Queries automatically filtered to current tenant
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    await set_tenant_context(db, str(user.tenant_id))
    return db


# ===========================================
# PERMISSION CHECKING
# ===========================================

def require_permission(permission: str):
    """
    Dependency factory that requires a specific permission.
    
    Usage:
        @router.post("/items")
        async def create_item(
            user: CurrentUser = Depends(require_permission("write:items")),
        ):
            ...
    """
    async def check_permission(
        user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        # Admin has all permissions
        if "admin:*" in user.permissions:
            return user
        
        if permission not in user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}",
            )
        
        return user
    
    return check_permission


def require_role(*roles: str):
    """
    Dependency factory that requires one of the specified roles.
    
    Usage:
        @router.delete("/items/{id}")
        async def delete_item(
            user: CurrentUser = Depends(require_role("admin", "manager")),
        ):
            ...
    """
    async def check_role(
        user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(roles)}",
            )
        
        return user
    
    return check_role


# ===========================================
# TYPE ALIASES FOR CLEANER SIGNATURES
# ===========================================

# Use these in route handlers for cleaner code
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
TenantDB = Annotated[AsyncSession, Depends(get_tenant_db)]
