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

"""Configuration settings for the Entra Agent ID demo."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 1. Google Agent Identity (Bootstrap Identity)
    gcp_project_id: str = "your-gcp-project-id"
    gcp_project_number: Optional[str] = "123456789012"
    gcp_region: str = "us-central1"
    google_agent_identity_sa: str = "entra-agent-runtime-sa@your-gcp-project-id.iam.gserviceaccount.com"
    google_agent_identity_audience: str = "api://AzureADTokenExchange"


    # 2. Workload Identity Federation (WIF) Configuration (Google STS)
    wif_pool_id: str = "entra-agent-pool"
    wif_provider_id: str = "entra-oidc-provider"

    # 3. Microsoft Entra Agent ID (Enterprise Federated Identity)
    entra_tenant_id: str = "00000000-0000-0000-0000-000000000000"
    entra_client_id: str = "00000000-0000-0000-0000-000000000000"
    entra_agent_object_id: str = "00000000-0000-0000-0000-000000000000"
    entra_scope: Optional[str] = None

    # Target Demo Resources
    demo_gcs_bucket: str = "agent-docs"

    # Testing & Mock Mode
    mock_auth: bool = False


settings = Settings()
