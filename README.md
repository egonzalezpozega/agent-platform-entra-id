# Microsoft Entra Agent ID on Google Cloud Agent Runtime

This repository demonstrates the integration of **Microsoft Entra Agent ID** with **Google Cloud Agent Runtime** and **Google Cloud Workload Identity Federation (WIF)**, providing autonomous cross-cloud identity governance for AI agents built with the **Agent Development Kit (ADK)**.

---

## 🏛️ Architecture Overview

```
                                      CROSS-CLOUD IDENTITY FEDERATION
                     ┌─────────────────────────────────────────────────────────────┐
                     │                                                             │
┌────────────────────┼──────────────┐                               ┌──────────────┼──────────────────┐
│ Google Cloud Agent │ Runtime      │                               │ Microsoft    │ Entra ID         │
│                    ▼              │                               │              ▼                  │
│   ┌───────────────────────────┐   │  1. SPIFFE Token Assertion    │   ┌───────────────────────────┐  │
│   │   Agent Runtime Metadata  │──────────────────────────────────────▶│ Microsoft Entra Blueprint  │  │
│   │    (SPIFFE Subject ID)    │   │                               │   │ (Federated Credential FIC)│  │
│   └───────────────────────────┘   │                               │   └─────────────┬─────────────┘  │
│                                   │                               │                 │ 2. Issues      │
│   ┌───────────────────────────┐   │  3. Exchanges Entra Token     │                 ▼                │
│   │  Google STS / WIF Pool    │◀──────────────────────────────────────│ Child Agent Identity (ID) │  │
│   │ (Subject: ENTRA_AGENT_ID) │   │     (fmi_path exchange)       │   │  (Autonomous Bearer Token)│  │
│   └─────────────┬─────────────┘   │                               │   └───────────────────────────┘  │
│                 │ 4. Issues       │                               └──────────────────────────────────┘
│                 ▼    Federated SA │
│   ┌───────────────────────────┐   │
│   │   Google Cloud Storage    │   │
│   │ (roles/storage.objViewer) │   │
│   └───────────────────────────┘   │
└───────────────────────────────────┘
```

1. **Bootstrap**: Agent boots in **Google Cloud Agent Runtime** and retrieves its cryptographically signed SPIFFE identity token.
2. **Entra Exchange**: Exchanges the Google SPIFFE assertion with **Microsoft Entra ID** using the Blueprint's Federated Identity Credential (FIC) and child `fmi_path` parameter.
3. **Google STS Exchange**: Exchanges the Microsoft Entra Agent ID token with **Google Cloud Workload Identity Federation (WIF)**.
4. **Governed Execution**: Accesses enterprise resources (Google Cloud Storage) under the authoritative identity of the Microsoft Entra Agent ID (`principal://iam.googleapis.com/.../subject/<ENTRA_AGENT_OBJECT_ID>`).

---

## 🚀 Quickstart

### 1. Prerequisites
- [uv](https://docs.astral.sh/uv/) installed.
- [Google Cloud CLI (`gcloud`)](https://cloud.google.com/sdk/docs/install) authenticated.
- `google-agents-cli` installed:
  ```bash
  uv tool install google-agents-cli
  ```

### 2. Configure Environment
Copy `.env.example` to `.env` and fill in your identifiers:
```bash
cp .env.example .env
```

### 3. Deploy to Google Cloud Agent Runtime
Run the one-click automated deployment script:
```bash
chmod +x scripts/deploy_all.sh
./scripts/deploy_all.sh
```

### 4. Test Live Agent
Execute the live agent query:
```bash
agents-cli run \
  --url "https://us-central1-aiplatform.googleapis.com/v1/projects/<PROJECT_NUMBER>/locations/us-central1/reasoningEngines/<REASONING_ENGINE_ID>" \
  --mode adk \
  "Inspect your active identity, list documents from Cloud Storage, and read 'sales_audit_2026.txt'."
```

---

## 📖 Codelab Guide

An interactive step-by-step Codelab is included in [`codelabs/`](file:///Users/epbgonzalez/Development/adk/agent-gateway-entra/codelabs/entra-agent-id-gemini-platform.md):
- Markdown source: `codelabs/entra-agent-id-gemini-platform.md`
- Exported HTML: `codelabs/entra-agent-id-gemini-platform/index.html`

To re-export the codelab using `claat`:
```bash
cd codelabs && claat export entra-agent-id-gemini-platform.md
```

---

## 🧪 Unit Tests

Run local unit tests with `pytest`:
```bash
uv run pytest tests/ -v
```

---

## 📄 License

Apache 2.0 - Copyright 2026 Google LLC

