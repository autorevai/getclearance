#!/usr/bin/env python3
"""
Set up Auth0 Action to add custom claims (tenant_id, role, permissions) to JWT tokens.

This script uses the Auth0 Management API to create/update a post-login Action
that enriches JWT tokens with user context from the GetClearance backend.

Usage:
    cd backend
    python -m scripts.setup_auth0_action

Environment Variables Required:
    AUTH0_DOMAIN - Your Auth0 tenant domain (e.g., dev-xxx.us.auth0.com)
    AUTH0_M2M_CLIENT_ID - Machine-to-Machine client ID
    AUTH0_M2M_CLIENT_SECRET - Machine-to-Machine client secret
    API_BASE_URL - Backend API URL (e.g., https://getclearance-production.up.railway.app)
"""

import os
import sys
import httpx
import json
from pathlib import Path

# Load .env file if present
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

# Configuration from environment
AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "dev-8z4blmy3c8wvkp4k.us.auth0.com")
AUTH0_M2M_CLIENT_ID = os.environ.get("AUTH0_M2M_CLIENT_ID", "WRg39V3xwkWKeZhpKVIvoJaQbg0n4QxW")
AUTH0_M2M_CLIENT_SECRET = os.environ.get("AUTH0_M2M_CLIENT_SECRET", "")
API_BASE_URL = os.environ.get("API_BASE_URL", "https://getclearance-production.up.railway.app")

# Custom claims namespace (must be a URL we control to avoid collisions)
CLAIMS_NAMESPACE = "https://getclearance.dev"

# The Action code that runs post-login
ACTION_CODE = '''
/**
 * GetClearance Post-Login Action
 *
 * Adds custom claims to the access token:
 * - tenant_id: UUID of the user's tenant
 * - role: User's role (admin, reviewer, analyst, viewer)
 * - permissions: Array of permission strings
 * - email: User's email address
 *
 * On first login, creates a new tenant and user in the backend.
 */
exports.onExecutePostLogin = async (event, api) => {
  const namespace = "https://getclearance.dev";
  const apiBaseUrl = event.secrets.API_BASE_URL || "https://getclearance-production.up.railway.app";

  try {
    // Check if user already has tenant_id in app_metadata
    let tenantId = event.user.app_metadata?.tenant_id;
    let role = event.user.app_metadata?.role || "admin";
    let permissions = event.user.app_metadata?.permissions || ["read:applicants", "write:applicants", "admin:*"];

    if (!tenantId) {
      // First login - call backend to provision user
      console.log("First login for user:", event.user.email);

      try {
        const response = await fetch(`${apiBaseUrl}/api/v1/auth/provision`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Auth0-User-Id": event.user.user_id,
          },
          body: JSON.stringify({
            auth0_id: event.user.user_id,
            email: event.user.email,
            name: event.user.name || event.user.email.split("@")[0],
          }),
        });

        if (response.ok) {
          const data = await response.json();
          tenantId = data.tenant_id;
          role = data.role;
          permissions = data.permissions;

          // Store in app_metadata for future logins
          api.user.setAppMetadata("tenant_id", tenantId);
          api.user.setAppMetadata("role", role);
          api.user.setAppMetadata("permissions", permissions);
        } else {
          console.log("Provision API returned:", response.status);
          // Fall back to demo tenant for development
          tenantId = "00000000-0000-0000-0000-000000000001";
        }
      } catch (fetchError) {
        console.log("Provision API error:", fetchError.message);
        // Fall back to demo tenant for development
        tenantId = "00000000-0000-0000-0000-000000000001";
      }
    }

    // Add custom claims to the access token
    api.accessToken.setCustomClaim(`${namespace}/tenant_id`, tenantId);
    api.accessToken.setCustomClaim(`${namespace}/role`, role);
    api.accessToken.setCustomClaim(`${namespace}/permissions`, permissions);
    api.accessToken.setCustomClaim(`${namespace}/email`, event.user.email);

    // Also add to ID token for frontend use
    api.idToken.setCustomClaim(`${namespace}/tenant_id`, tenantId);
    api.idToken.setCustomClaim(`${namespace}/role`, role);

  } catch (error) {
    console.log("Action error:", error.message);
    // Don't block login on errors - use fallback tenant
    const fallbackTenantId = "00000000-0000-0000-0000-000000000001";
    api.accessToken.setCustomClaim(`${namespace}/tenant_id`, fallbackTenantId);
    api.accessToken.setCustomClaim(`${namespace}/role`, "admin");
    api.accessToken.setCustomClaim(`${namespace}/permissions`, ["read:applicants", "write:applicants", "admin:*"]);
    api.accessToken.setCustomClaim(`${namespace}/email`, event.user.email);
  }
};
'''


def get_management_token() -> str:
    """Get Auth0 Management API access token."""
    if not AUTH0_M2M_CLIENT_SECRET:
        raise ValueError("AUTH0_M2M_CLIENT_SECRET not set. Please provide the M2M client secret.")

    response = httpx.post(
        f"https://{AUTH0_DOMAIN}/oauth/token",
        json={
            "client_id": AUTH0_M2M_CLIENT_ID,
            "client_secret": AUTH0_M2M_CLIENT_SECRET,
            "audience": f"https://{AUTH0_DOMAIN}/api/v2/",
            "grant_type": "client_credentials",
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]


def find_existing_action(token: str) -> dict | None:
    """Find existing GetClearance action if any."""
    response = httpx.get(
        f"https://{AUTH0_DOMAIN}/api/v2/actions/actions",
        headers={"Authorization": f"Bearer {token}"},
        params={"triggerId": "post-login"},
    )
    response.raise_for_status()

    for action in response.json().get("actions", []):
        if action.get("name") == "GetClearance Add Custom Claims":
            return action
    return None


def create_or_update_action(token: str) -> dict:
    """Create or update the Auth0 Action."""
    existing = find_existing_action(token)

    action_payload = {
        "name": "GetClearance Add Custom Claims",
        "code": ACTION_CODE,
        "supported_triggers": [{"id": "post-login", "version": "v3"}],
        "runtime": "node18",
        "secrets": [
            {"name": "API_BASE_URL", "value": API_BASE_URL},
        ],
    }

    if existing:
        # Update existing action
        action_id = existing["id"]
        response = httpx.patch(
            f"https://{AUTH0_DOMAIN}/api/v2/actions/actions/{action_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=action_payload,
        )
        response.raise_for_status()
        print(f"Updated existing action: {action_id}")
        return response.json()
    else:
        # Create new action
        response = httpx.post(
            f"https://{AUTH0_DOMAIN}/api/v2/actions/actions",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=action_payload,
        )
        response.raise_for_status()
        print(f"Created new action: {response.json()['id']}")
        return response.json()


def deploy_action(token: str, action_id: str) -> None:
    """Deploy the action to make it live."""
    response = httpx.post(
        f"https://{AUTH0_DOMAIN}/api/v2/actions/actions/{action_id}/deploy",
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    print(f"Deployed action: {action_id}")


def add_to_flow(token: str, action_id: str) -> None:
    """Add action to the post-login flow."""
    # Get current flow bindings
    response = httpx.get(
        f"https://{AUTH0_DOMAIN}/api/v2/actions/triggers/post-login/bindings",
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    current_bindings = response.json().get("bindings", [])

    # Check if already in flow
    for binding in current_bindings:
        if binding.get("action", {}).get("id") == action_id:
            print("Action already in post-login flow")
            return

    # Add to flow
    new_bindings = current_bindings + [
        {"ref": {"type": "action_id", "value": action_id}, "display_name": "GetClearance Add Custom Claims"}
    ]

    response = httpx.patch(
        f"https://{AUTH0_DOMAIN}/api/v2/actions/triggers/post-login/bindings",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"bindings": new_bindings},
    )
    response.raise_for_status()
    print("Added action to post-login flow")


def main():
    print("=" * 60)
    print("Auth0 Action Setup for GetClearance")
    print("=" * 60)
    print(f"Domain: {AUTH0_DOMAIN}")
    print(f"API Base URL: {API_BASE_URL}")
    print()

    if not AUTH0_M2M_CLIENT_SECRET:
        print("ERROR: AUTH0_M2M_CLIENT_SECRET environment variable not set.")
        print("Please set it to the M2M client secret from Auth0 dashboard.")
        sys.exit(1)

    try:
        print("Getting Management API token...")
        token = get_management_token()

        print("Creating/updating Action...")
        action = create_or_update_action(token)
        action_id = action["id"]

        print("Deploying Action...")
        deploy_action(token, action_id)

        print("Adding Action to post-login flow...")
        add_to_flow(token, action_id)

        print()
        print("=" * 60)
        print("SUCCESS! Auth0 Action configured.")
        print("=" * 60)
        print()
        print("The Action will add these claims to JWT tokens:")
        print(f"  - {CLAIMS_NAMESPACE}/tenant_id")
        print(f"  - {CLAIMS_NAMESPACE}/role")
        print(f"  - {CLAIMS_NAMESPACE}/permissions")
        print(f"  - {CLAIMS_NAMESPACE}/email")
        print()
        print("Next steps:")
        print("1. Log out and log back in to get a new token with claims")
        print("2. The backend will read these claims for authorization")
        print()

    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
