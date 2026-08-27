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

"""Unit tests for Entra Agent execution and tools."""

import pytest
from unittest.mock import MagicMock, patch
from agent.agent import root_agent
from agent.tools.identity_inspector import inspect_agent_identity
from agent.tools.gcp_data_tools import list_storage_documents, read_storage_document


def test_agent_tool_registry():
    tool_names = [getattr(t, "__name__", getattr(t, "name", str(t))) for t in root_agent.tools]
    assert "inspect_agent_identity" in tool_names
    assert "list_storage_documents" in tool_names
    assert "read_storage_document" in tool_names


def test_inspect_agent_identity_mock():
    with patch("agent.tools.identity_inspector.settings.mock_auth", True):
        res = inspect_agent_identity()
        assert res["status"] == "verified"
        assert "principal" in res["active_gcp_principal"]


def test_list_storage_documents_mock():
    with patch("agent.tools.gcp_data_tools.settings.mock_auth", True):
        res = list_storage_documents()
        assert res["status"] == "success"
        assert len(res["files"]) > 0


def test_read_storage_document_mock():
    with patch("agent.tools.gcp_data_tools.settings.mock_auth", True):
        res = read_storage_document("sales_audit_2026.txt")
        assert res["status"] == "success"
        assert "sales_audit_2026.txt" in res["file_name"]
        assert "Mock content" in res["content"]
