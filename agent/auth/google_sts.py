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

"""Google Cloud Security Token Service (STS) Module.

Exchanges a Microsoft Entra Agent ID token with Google Cloud STS using OAuth 2.0 Token Exchange (RFC 8693) to produce a Google Access Token bound to the Entra Principal.
"""

import logging
from typing import Dict, Any
import requests
import jwt

logger = logging.getLogger(__name__)

STS_URL = "https://sts.googleapis.com/v1/token"


def exchange_entra_for_google_sts_token(
    entra_token: str,
    project_number: str,
    pool_id: str,
    provider_id: str,
    scope: str = "https://www.googleapis.com/auth/cloud-platform",
) -> Dict[str, Any]:
    """Exchanges an Entra Agent ID token for a Google federated access token.

    Args:
        entra_token: Entra Agent ID access or ID token.
        project_number: GCP Project Number hosting the Workload Identity Pool.
        pool_id: ID of the Workload Identity Pool.
        provider_id: ID of the Workload Identity Provider configured for Entra.
        scope: GCP OAuth scope.

    Returns:
        JSON response from Google STS containing 'access_token', 'expires_in', and 'token_type'.
    """
    audience = (
        f"//iam.googleapis.com/projects/{project_number}/locations/global/"
        f"workloadIdentityPools/{pool_id}/providers/{provider_id}"
    )

    # Decode and log Entra claims
    try:
        claims = jwt.decode(entra_token, options={"verify_signature": False})
        logger.info(
            "Entra Token Claims -> iss: %s, sub: %s, aud: %s, oid: %s, appid: %s",
            claims.get("iss"),
            claims.get("sub"),
            claims.get("aud"),
            claims.get("oid"),
            claims.get("appid"),
        )
    except Exception as exc:
        logger.warning("Could not decode Entra token claims: %s", exc)

    payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "audience": audience,
        "scope": scope,
        "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "subject_token": entra_token,
        "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
    }

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
    }

    logger.info("Calling Google STS at %s with audience: %s...", STS_URL, audience)
    response = requests.post(STS_URL, json=payload, headers=headers, timeout=10)

    if not response.ok:
        logger.error("Google STS token exchange failed (%s): %s", response.status_code, response.text)
        response.raise_for_status()

    sts_data = response.json()
    logger.info("Successfully acquired Google STS Federated Access Token bound to Entra Principal.")
    return sts_data
