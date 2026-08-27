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

"""Identity Inspector Tool for verifying the Entra Agent ID (ID-2) authentication chain."""

import logging
from typing import Dict, Any

from agent.auth.credentials import EntraFederatedCredentials
from agent.config import settings

logger = logging.getLogger(__name__)


def inspect_agent_identity() -> Dict[str, Any]:
    """Inspects and returns the currently active agent identity, token claims, and federation chain status.

    Returns:
        A dictionary containing the active identity claims, Entra ID principal, and Google STS status.
    """
    creds = EntraFederatedCredentials(settings)
    auth_error = None
    if not creds.valid:
        try:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        except Exception as exc:
            logger.warning("Identity refresh notice: %s", exc)
            auth_error = str(exc)

    diagnostics = creds.get_identity_diagnostics()
    result = {
        "status": "verified" if creds.valid else "partially_verified",
        "pattern": "Agent's Own Identity (ID-2) with Entra",
        "gcp_project": settings.gcp_project_id,
        "wif_pool": settings.wif_pool_id,
        "wif_provider": settings.wif_provider_id,
        "entra_tenant_id": settings.entra_tenant_id,
        "entra_agent_client_id": settings.entra_client_id,
        "entra_claims": diagnostics.get("entra_claims"),
        "active_gcp_principal": f"principal://iam.googleapis.com/projects/{settings.gcp_project_number or '<project_number>'}/locations/global/workloadIdentityPools/{settings.wif_pool_id}/subject/{settings.entra_agent_object_id}",
    }
    if auth_error:
        result["sts_exchange_notice"] = auth_error
    return result
