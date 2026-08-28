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

"""Entra-governed ADK Agent definition."""

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from agent.tools.identity_inspector import inspect_agent_identity
from agent.tools.gcp_data_tools import list_storage_documents, read_storage_document

MODEL = "gemini-2.5-flash"

AGENT_INSTRUCTION = """
You are the Entra-Governed Enterprise Agent on Google Cloud Agent Platform.

Operational Identity (Federated Agent Identity):
1. Bootstrap Google Agent Runtime SPIFFE credential.
2. Federate to Microsoft Entra ID for Entra Agent ID identity.
3. Exchange Entra token with Google STS to interact with GCP APIs.
4. Access GCP resources (Cloud Storage, etc.) authorized under Microsoft Entra Principal.

Capabilities:
- `inspect_agent_identity`: Inspect active token claims & Entra principal mapping.
- `list_storage_documents`: List Cloud Storage files under Entra identity.
- `read_storage_document`: Read document contents under Entra identity.

Output Guidelines:
- Keep responses short, concise, and straight to the point. No conversational filler or long paragraphs.
- Use clean section headers and sprinkle relevant status emojis (e.g., 🔐, 📋, 📂, 📄, ✅, ⚠️, 🚀).
- Format data cleanly using short bullet points or key-value summary blocks.
"""



root_agent = Agent(
    name="agent_platform_entra_id",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=AGENT_INSTRUCTION,
    tools=[
        inspect_agent_identity,
        list_storage_documents,
        read_storage_document,
    ],
)

app = App(
    root_agent=root_agent,
    name="agent",
)
