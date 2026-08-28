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

"""Custom Google Auth Credentials wrapping the full Entra Agent ID federation chain."""

import datetime
import logging
from typing import Optional, Dict, Any

import google.auth.credentials
from google.auth.transport import Request

from agent.config import Settings, settings as default_settings
from agent.auth.bootstrap import get_google_bootstrap_token
from agent.auth.entra_exchange import exchange_google_for_entra_token, inspect_jwt_claims
from agent.auth.google_sts import exchange_entra_for_google_sts_token

logger = logging.getLogger(__name__)


class EntraFederatedCredentials(google.auth.credentials.Credentials):
    """Google Cloud Credentials implementation that authenticates via Federated Entra Agent Identity.

    Chaining Workflow:
    1. Base Google Credential ->
    2. Microsoft Entra Agent ID Token ->
    3. Google STS Federated Token ->
    4. Google Cloud IAM Authorization (attributed to Entra Principal).
    """

    def __init__(self, config: Optional[Settings] = None):
        super().__init__()
        self.config = config or default_settings
        self.token: Optional[str] = None
        self.expiry: Optional[datetime.datetime] = None
        self._entra_token: Optional[str] = None
        self._entra_claims: Dict[str, Any] = {}
        self._bootstrap_token: Optional[str] = None

    @property
    def valid(self) -> bool:
        """Returns True if the credentials have a non-expired Google STS token."""
        if not self.token or not self.expiry:
            return False
        # Buffer of 60 seconds
        return datetime.datetime.now(datetime.timezone.utc) < (self.expiry - datetime.timedelta(seconds=60))

    @property
    def requires_scopes(self) -> bool:
        return False

    def refresh(self, request: Request) -> None:
        """Executes the full two-way identity federation exchange."""
        logger.info("Executing Entra Agent ID identity federation chain...")

        if self.config.mock_auth:
            logger.info("Mock auth enabled: returning simulated Entra-federated credentials.")
            self.token = "mock-google-sts-entra-federated-token"
            self.expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
            self._entra_token = "mock-entra-token"
            self._entra_claims = {
                "sub": self.config.entra_agent_object_id,
                "oid": self.config.entra_agent_object_id,
                "tid": self.config.entra_tenant_id,
                "app_displayname": "EntraAgentID-Demo",
                "iss": f"https://sts.windows.net/{self.config.entra_tenant_id}/",
            }
            return

        # 1. Step 1: Bootstrap Google ID Token
        logger.info("Step 1: Acquiring Google base bootstrap credential...")
        self._bootstrap_token = get_google_bootstrap_token()

        # 2. Step 2: Exchange with Microsoft Entra ID
        scope = self.config.entra_scope or f"api://{self.config.entra_client_id}/.default"
        logger.info("Step 2: Federating to Microsoft Entra for Entra Agent ID token with scope '%s'...", scope)
        entra_res = exchange_google_for_entra_token(
            google_assertion=self._bootstrap_token,
            tenant_id=self.config.entra_tenant_id,
            client_id=self.config.entra_client_id,
            agent_identity_id=self.config.entra_agent_object_id,
            scope=scope,
        )
        self._entra_token = entra_res["access_token"]
        self._entra_claims = inspect_jwt_claims(self._entra_token)

        # 3. Step 3: Federate Entra token back to Google STS
        logger.info("Step 3: Federating Entra token back to Google STS...")
        if not self.config.gcp_project_number:
            raise ValueError(
                "GCP project number is required for STS token exchange audience. "
                "Please configure GCP_PROJECT_NUMBER in environment settings."
            )

        sts_res = exchange_entra_for_google_sts_token(
            entra_token=self._entra_token,
            project_number=self.config.gcp_project_number,
            pool_id=self.config.wif_pool_id,
            provider_id=self.config.wif_provider_id,
        )

        self.token = sts_res["access_token"]
        expires_in = sts_res.get("expires_in", 3600)
        self.expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_in)

        logger.info("Successfully established Entra-backed Google credentials (valid until %s).", self.expiry)

    def get_identity_diagnostics(self) -> Dict[str, Any]:
        """Returns diagnostic metadata about the current identity chain."""
        return {
            "valid": self.valid,
            "expiry": str(self.expiry) if self.expiry else None,
            "entra_claims": self._entra_claims,
            "entra_subject": self._entra_claims.get("sub") or self._entra_claims.get("oid"),
            "entra_tenant_id": self._entra_claims.get("tid"),
            "google_token_preview": f"{self.token[:10]}...{self.token[-6:]}" if self.token else None,
        }
