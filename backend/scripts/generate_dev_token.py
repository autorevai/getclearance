#!/usr/bin/env python3
"""
Development Token Generator
===========================
Generate dev tokens for local API testing without Auth0.

Usage:
    python scripts/generate_dev_token.py
    python scripts/generate_dev_token.py --user-id myuser --tenant-id <uuid> --role admin

Token Format:
    dev_{user_id}_{tenant_id}_{role}

Example:
    dev_testuser_00000000-0000-0000-0000-000000000001_admin

Use the generated token in the Authorization header:
    Authorization: Bearer dev_testuser_00000000-0000-0000-0000-000000000001_admin
"""

import argparse
import sys


def generate_dev_token(user_id: str, tenant_id: str, role: str) -> str:
    """Generate a development token."""
    return f"dev_{user_id}_{tenant_id}_{role}"


def main():
    parser = argparse.ArgumentParser(
        description="Generate development tokens for local API testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--user-id",
        default="testuser",
        help="User ID for the token (default: testuser)",
    )
    parser.add_argument(
        "--tenant-id",
        default="00000000-0000-0000-0000-000000000001",
        help="Tenant UUID for the token (default: demo tenant)",
    )
    parser.add_argument(
        "--role",
        choices=["admin", "reviewer", "analyst", "viewer"],
        default="admin",
        help="Role for the token (default: admin)",
    )
    parser.add_argument(
        "--curl",
        action="store_true",
        help="Output as curl command example",
    )

    args = parser.parse_args()

    token = generate_dev_token(args.user_id, args.tenant_id, args.role)

    if args.curl:
        print(f"""
# Development Token Generated
# User: {args.user_id}
# Tenant: {args.tenant_id}
# Role: {args.role}

# Example curl command:
curl -X GET "http://localhost:8000/api/v1/applicants" \\
  -H "Authorization: Bearer {token}" \\
  -H "Content-Type: application/json"

# Example with POST:
curl -X POST "http://localhost:8000/api/v1/applicants" \\
  -H "Authorization: Bearer {token}" \\
  -H "Content-Type: application/json" \\
  -d '{{"first_name": "John", "last_name": "Doe", "email": "john@example.com"}}'
""")
    else:
        print(f"""
Development Token Generated
===========================
User ID:   {args.user_id}
Tenant ID: {args.tenant_id}
Role:      {args.role}

Token:
{token}

Usage:
  Authorization: Bearer {token}

Permissions for {args.role}:""")

        permissions = {
            "admin": [
                "read:applicants", "write:applicants", "delete:applicants",
                "read:documents", "write:documents",
                "read:screening", "write:screening",
                "read:cases", "write:cases",
                "read:settings", "write:settings",
                "admin:*",
            ],
            "reviewer": [
                "read:applicants", "write:applicants",
                "read:documents", "write:documents",
                "read:screening", "write:screening",
                "read:cases", "write:cases",
            ],
            "analyst": [
                "read:applicants", "read:documents",
                "read:screening", "read:cases", "write:cases",
            ],
            "viewer": [
                "read:applicants", "read:documents",
                "read:screening", "read:cases",
            ],
        }

        for perm in permissions.get(args.role, []):
            print(f"  - {perm}")


if __name__ == "__main__":
    main()
