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

"""Google Base Credential Bootstrap Module.

Acquires a Google OIDC token or SPIFFE assertion to bootstrap the federated identity exchange with Microsoft Entra ID.
"""

import logging
import urllib.request
import urllib.error
import google.auth
from google.auth.transport.requests import Request
import google.oauth2.id_token

logger = logging.getLogger(__name__)

METADATA_IDENTITY_URL = (
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity"
)


def get_google_bootstrap_token(audience: str = "api://AzureADTokenExchange") -> str:
    """Acquires a Google OIDC identity token for federating with Entra ID.

    Args:
        audience: The expected audience claim configured on Entra's Federated Identity Credential
                  (default: api://AzureADTokenExchange).

    Returns:
        A signed Google OIDC JWT token string.
    """
    # 1. First attempt to fetch from Google Compute / Agent Runtime metadata server
    try:
        url = f"{METADATA_IDENTITY_URL}?audience={audience}&format=full"
        req = urllib.request.Request(url, headers={"Metadata-Flavor": "Google"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            token = resp.read().decode("utf-8").strip()
            logger.info("Successfully acquired Google bootstrap ID token from Metadata Server.")
            return token
    except Exception as exc:
        logger.debug("Metadata server not available or failed: %s. Falling back to ADC / local auth.", exc)

    # 2. Fallback for local development using Application Default Credentials (ADC)
    try:
        auth_req = Request()
        token = google.oauth2.id_token.fetch_id_token(auth_req, audience)
        logger.info("Acquired Google bootstrap ID token via ADC.")
        return token
    except Exception as exc:
        logger.debug("Direct ADC ID token fetch not supported for user credentials (%s), trying impersonation...", exc)

    # 3. Fallback for local user ADC via Service Account Impersonation
    try:
        from google.auth import impersonated_credentials
        from agent.config import settings

        credentials, _ = google.auth.default()
        source_creds = impersonated_credentials.Credentials(
            source_credentials=credentials,
            target_principal=settings.google_agent_identity_sa,
            target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        id_creds = impersonated_credentials.IDTokenCredentials(
            target_credentials=source_creds,
            target_audience=audience,
            include_email=True,
        )
        id_creds.refresh(Request())
        logger.info("Acquired Google bootstrap ID token via SA impersonation (%s).", settings.google_agent_identity_sa)
        return id_creds.token
    except Exception as exc:
        logger.warning("Failed to fetch Google ID token via SA impersonation: %s.", exc)
        raise RuntimeError(
            f"Unable to acquire Google bootstrap credential. Error: {exc}"
        ) from exc

