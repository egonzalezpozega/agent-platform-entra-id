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

"""Unit tests for the Entra Agent ID (ID-2) authentication and token-chaining flow."""

from unittest.mock import patch, MagicMock
import pytest
from agent.config import Settings
from agent.auth.credentials import EntraFederatedCredentials
from agent.auth.entra_exchange import exchange_google_for_entra_token
from agent.auth.google_sts import exchange_entra_for_google_sts_token


@pytest.fixture
def test_settings():
    return Settings(
        gcp_project_id="test-project",
        gcp_project_number="123456789012",
        wif_pool_id="test-pool",
        wif_provider_id="test-provider",
        entra_tenant_id="test-tenant-id",
        entra_client_id="test-client-id",
        entra_agent_object_id="entra-agent-oid-999",
        mock_auth=False,
    )


def test_entra_token_exchange_success():
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "access_token": "mock-entra-token-jwt",
        "token_type": "Bearer",
        "expires_in": 3599,
    }

    with patch("requests.post", return_value=mock_response) as mock_post:
        res = exchange_google_for_entra_token(
            google_assertion="fake-google-id-token",
            tenant_id="test-tenant-id",
            client_id="test-client-id",
        )
        assert res["access_token"] == "mock-entra-token-jwt"
        assert mock_post.called
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["data"]["grant_type"] == "client_credentials"
        assert call_kwargs["data"]["client_assertion"] == "fake-google-id-token"


def test_google_sts_exchange_success():
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "access_token": "mock-google-sts-token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    with patch("requests.post", return_value=mock_response) as mock_post:
        res = exchange_entra_for_google_sts_token(
            entra_token="mock-entra-token-jwt",
            project_number="123456789012",
            pool_id="test-pool",
            provider_id="test-provider",
        )
        assert res["access_token"] == "mock-google-sts-token"
        assert mock_post.called
        payload = mock_post.call_args[1]["json"]
        assert payload["grant_type"] == "urn:ietf:params:oauth:grant-type:token-exchange"
        assert payload["subject_token"] == "mock-entra-token-jwt"


def test_entra_federated_credentials_mock_mode():
    mock_config = Settings(mock_auth=True, entra_agent_object_id="agent-001")
    creds = EntraFederatedCredentials(mock_config)
    assert not creds.valid

    request_mock = MagicMock()
    creds.refresh(request_mock)

    assert creds.valid
    assert creds.token == "mock-google-sts-entra-federated-token"
    diag = creds.get_identity_diagnostics()
    assert diag["valid"] is True
    assert diag["entra_subject"] == "agent-001"


def test_entra_federated_credentials_full_chain(test_settings):
    with patch("agent.auth.credentials.get_google_bootstrap_token", return_value="google-bootstrap-token"), \
         patch("agent.auth.credentials.exchange_google_for_entra_token", return_value={"access_token": "entra-token-123"}), \
         patch("agent.auth.credentials.exchange_entra_for_google_sts_token", return_value={"access_token": "google-sts-final-token", "expires_in": 3600}):
        
        creds = EntraFederatedCredentials(test_settings)
        request_mock = MagicMock()
        creds.refresh(request_mock)

        assert creds.valid
        assert creds.token == "google-sts-final-token"
