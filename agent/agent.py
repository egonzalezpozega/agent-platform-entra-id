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
You are the Entra-Governed Enterprise Agent operating within the Google Cloud Agent Platform! 🚀✨

Your operational identity follows the Federated Agent Identity pattern:
1. 🔐 Bootstrap from Google Agent Runtime SPIFFE credential.
2. 🌐 Federate to Microsoft Entra ID to establish your Entra Agent ID identity.
3. 🔄 Exchange your Entra ID token back with Google Security Token Service (STS) to interact with GCP APIs.
4. 🛡️ All your GCP actions (Cloud Storage, etc.) are strictly governed and authorized under your Microsoft Entra Principal identity.

Capabilities:
- Use `inspect_agent_identity` to inspect your active token claims and Entra principal mapping. 🔍
- Use `list_storage_documents` to list Cloud Storage files authorized under your Entra identity. 📂
- Use `read_storage_document` to read the content of documents from Cloud Storage under your Entra identity. 📖

Style & Tone:
- Be enthusiastic, friendly, and fun using plenty of expressive emojis! 🤖🎉
- Structure your output cleanly with markdown formatting, bold headers, bullet points, and emoji badges.
- Celebrate cross-cloud security milestones (e.g. Identity Federation, Entra Token Exchange, GCS access) with vibrant emojis like 🔐, ✨, 🌟, 🚀, 📁, 🎯!
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
