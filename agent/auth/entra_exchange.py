# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Microsoft Entra Agent ID (ID 2b) Token Exchange Module.

Exchanges a Google bootstrap assertion (ID 2a) with Microsoft Entra ID via Workload Identity Federation (RFC 7523) to obtain an Entra Agent ID token.
"""

import logging
from typing import Dict, Any, Optional
import requests
import jwt

logger = logging.getLogger(__name__)


def exchange_google_for_entra_token(
    google_assertion: str,
    tenant_id: str,
    client_id: str,
    agent_identity_id: Optional[str] = None,
    scope: Optional[str] = None,
) -> Dict[str, Any]:
    """Exchanges a Google ID token for an Entra Agent ID access token using the official Entra Autonomous App Flow.

    Reference: https://learn.microsoft.com/en-us/entra/agent-id/agent-autonomous-app-oauth-flow

    Step 1: Blueprint requests exchange token T1 with fmi_path={agent_identity_id} using Google SPIFFE assertion.
    Step 2: Agent identity requests resource access token using T1 as client assertion.

    Args:
        google_assertion: Signed Google OIDC ID token (ID 2a).
        tenant_id: Microsoft Entra Directory (Tenant) ID.
        client_id: Application (Client) ID of the Entra Agent Blueprint.
        agent_identity_id: Client ID / Object ID of the instantiated Agent Identity.
        scope: Resource scope for the Entra token.

    Returns:
        JSON response from Entra containing 'access_token', 'expires_in', etc.
    """
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    # Decode and log Google assertion claims for troubleshooting
    assertion_claims = inspect_jwt_claims(google_assertion)
    logger.info(
        "Google Assertion Claims -> iss: %s, sub: %s, email: %s, aud: %s",
        assertion_claims.get("iss"),
        assertion_claims.get("sub"),
        assertion_claims.get("email"),
        assertion_claims.get("aud"),
    )

    # Step 1: Request exchange token T1
    logger.info("Entra Exchange Step 1: Blueprint '%s' requesting T1 token with fmi_path='%s'...", client_id, agent_identity_id)
    step1_payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "scope": "api://AzureADTokenExchange/.default",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": google_assertion,
    }
    if agent_identity_id:
        step1_payload["fmi_path"] = agent_identity_id

    res1 = requests.post(token_url, data=step1_payload, headers=headers, timeout=10)
    if not res1.ok:
        logger.warning(
            "Step 1 with fmi_path failed (%s): %s. Falling back to direct exchange.",
            res1.status_code,
            res1.text,
        )
        # Fallback to direct exchange
        fallback_payload = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "scope": scope or "https://graph.microsoft.com/.default",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": google_assertion,
        }
        res_fallback = requests.post(token_url, data=fallback_payload, headers=headers, timeout=10)
        if not res_fallback.ok:
            error_msg = f"Entra token exchange failed ({res_fallback.status_code}): {res_fallback.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        return res_fallback.json()

    t1_data = res1.json()
    t1_token = t1_data["access_token"]
    logger.info("Entra Exchange Step 1 successful: T1 token acquired.")

    # If no separate agent identity, return T1
    if not agent_identity_id:
        return t1_data

    # Step 2: Agent Identity requests resource access token using T1
    effective_scope = scope or "https://graph.microsoft.com/.default"
    logger.info("Entra Exchange Step 2: Agent identity '%s' requesting resource token with scope '%s'...", agent_identity_id, effective_scope)
    step2_payload = {
        "grant_type": "client_credentials",
        "client_id": agent_identity_id,
        "scope": effective_scope,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": t1_token,
    }

    res2 = requests.post(token_url, data=step2_payload, headers=headers, timeout=10)
    if not res2.ok:
        logger.warning(
            "Step 2 exchange failed (%s): %s. Returning T1 token.",
            res2.status_code,
            res2.text,
        )
        return t1_data

    token_data = res2.json()
    logger.info("Successfully acquired Entra Agent ID resource token (ID 2b).")
    return token_data



def inspect_jwt_claims(token: str) -> Dict[str, Any]:
    """Decodes unverified JWT claims for diagnostics and logging."""
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except Exception as exc:
        logger.warning("Failed to parse JWT claims: %s", exc)
        return {"error": str(exc)}
