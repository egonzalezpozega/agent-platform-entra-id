# How to Integrate Microsoft Entra Agent ID with Google Cloud Agent Runtime

[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Platform%20%26%20Agent%20Runtime-blue?logo=google-cloud)](https://cloud.google.com/)
[![Microsoft Entra](https://img.shields.io/badge/Identity-Microsoft%20Entra%20Agent%20ID-0078D4?logo=microsoft-azure)](https://learn.microsoft.com/en-us/entra/agent-id/)
[![ADK](https://img.shields.io/badge/Agent-Google%20ADK%20Python-EA4335?logo=python)](https://google.github.io/agent-development-kit/)
[![Interactive Guide](https://img.shields.io/badge/Guide-Interactive%20HTML-brightgreen?logo=html5)](https://egonzalezpozega.github.io/agent-platform-entra-id/)
[![Documentation](https://img.shields.io/badge/Format-Codelab%20Markdown-green)](#repository-structure)

This repository contains a comprehensive, step-by-step **Google Cloud Codelab** that guides you through integrating **Microsoft Entra Agent ID** with **Google Cloud Agent Runtime** and **Google Cloud Workload Identity Federation (WIF)** for secret-free, autonomous multi-cloud AI agent governance.

---

## 📖 Overview

[Microsoft Entra Agent ID](https://learn.microsoft.com/en-us/entra/agent-id/) and [Google Cloud Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation) allow private, secure, and secret-free identity governance across multi-cloud environments.

In this lab, you learn how to:
1. **Understand multi-cloud agent identity patterns** (Native Google Agent Identity vs. Federated Microsoft Entra Agent ID).
2. **Create a parent Agent Blueprint and child Agent Identity** in Microsoft Entra Admin Center.
3. **Deploy the ADK agent and Google Cloud infrastructure** (Workload Identity Pool, OIDC Provider, Cloud Storage) using automated one-click scripts.
4. **Configure Federated Identity Credentials (FIC)** in Microsoft Entra to establish cryptographic trust with Google Agent Runtime.
5. **Deep-dive into the token exchange adapters** implementing the official [Microsoft Entra Autonomous App OAuth Flow](https://learn.microsoft.com/en-us/entra/agent-id/agent-autonomous-app-oauth-flow) ([RFC 7523](https://datatracker.ietf.org/doc/html/rfc7523) / [RFC 8693](https://datatracker.ietf.org/doc/html/rfc8693)) and Google STS WIF.
6. **Verify and test live agent execution** using `agents-cli run` to inspect identity and access governed Cloud Storage documents.
7. **Clean up all cloud resources** to prevent unwanted billing.

---

## 🌐 Interactive HTML Guide

This repository includes an interactive, browser-based version of the codelab:

👉 **[Hosted Live Codelab](https://egonzalezpozega.github.io/agent-platform-entra-id/)** (or local [`docs/index.html`](docs/index.html))

**Features:**
- 📋 **Ready-to-copy code blocks**: One-click copy buttons with instant feedback for all `gcloud`, `agents-cli`, and configuration commands.
- 📑 **Live Step-by-Step Navigation**: Clean sidebar navigation and time estimates per section.
- ⏱️ **Duration & progress tracking**: Reading progress bar and completion tracking.
- 🔍 **Syntax highlighting**: Clear color formatting for Bash, Python, and JSON/YAML syntax.

---

## 🏛️ Architecture Overview

```
                                      CROSS-CLOUD IDENTITY FEDERATION
                     ┌─────────────────────────────────────────────────────────────┐
                     │                                                             │
┌────────────────────┼──────────────┐                               ┌──────────────┼──────────────────-┐
│ Google Cloud Agent │ Runtime      │                               │ Microsoft    │ Entra ID          │
│                    ▼              │                               │              ▼                   │
│   ┌───────────────────────────┐   │  1. SPIFFE Token Assertion    │   ┌───────────────────────────┐  │
│   │   Agent Runtime Metadata  │──────────────────────────────────────▶│ Microsoft Entra Blueprint │  │
│   │    (SPIFFE Subject ID)    │   │                               │   │ (Federated Credential FIC)│  │
│   └───────────────────────────┘   │                               │   └─────────────┬─────────────┘  │
│                                   │                               │                 │ 2. Issues      │
│   ┌───────────────────────────┐   │  3. Exchanges Entra Token     │    _____________▼_____________   │
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

## 📂 Repository Structure

```text
.
├── README.md                                  # Repository documentation and overview (this file)
├── agent/                                     # ADK agent implementation
│   ├── agent.py                               # Root ADK Agent & App definition
│   ├── auth/                                  # Autonomous Token Exchange & WIF Adapters
│   │   ├── credentials.py                     # Custom Google Auth Credentials Provider
│   │   ├── entra_exchange.py                  # RFC 7523 / RFC 8693 2-step token exchange
│   │   ├── google_sts.py                      # Google STS / WIF token exchange
│   │   └── settings.py                        # Environment & Auth configuration
│   └── tools/                                 # Agent tools (Storage inspection & document reading)
├── codelabs/                                  # Codelab source and static assets
│   ├── entra-agent-id-gemini-platform.md      # Complete step-by-step tutorial (Markdown / Claat format)
│   └── img/                                   # Architecture flow diagrams and assets
│       └── flow-diagram.png
├── docs/                                      # Exported interactive HTML codelab (GitHub Pages)
│   └── index.html
├── scripts/                                   # Automated deployment & teardown scripts
│   ├── deploy_all.sh                          # One-click end-to-end deployment
│   └── destroy_all.sh                         # Clean teardown script
├── tests/                                     # Unit & integration test suite
└── pyproject.toml                             # Python package & dependency configuration
```

---

## 📋 Prerequisites & Requirements

- A **Google Cloud Account** and **Project** with billing enabled.
- A **Microsoft Entra ID Tenant** with the **Microsoft Entra Agent ID (Preview)** feature enabled.
- A modern web browser (e.g., [Google Chrome](https://www.google.com/chrome/)).
- Basic familiarity with:
  - Google Cloud Console & `gcloud` CLI
  - Microsoft Entra Admin Center
  - Python 3.11+, `uv`, and `google-agents-cli`

---

## 🚀 Lab Outline

| Step | Topic | Description |
| :--- | :--- | :--- |
| **1** | **[Introduction](codelabs/entra-agent-id-gemini-platform.md#introduction)** | Overview of multi-cloud agent identity, prerequisites, and what you'll build. |
| **2** | **[Multi-Cloud Architecture & Identity Topology](codelabs/entra-agent-id-gemini-platform.md#multi-cloud-architecture--identity-topology)** | Comparison between Native GCP Agent Identity vs. Federated Microsoft Entra Agent ID. |
| **3** | **[Create Microsoft Entra Blueprint & Agent Identity](codelabs/entra-agent-id-gemini-platform.md#create-microsoft-entra-blueprint--agent-identity)** | Provision parent Agent Blueprint and instantiate child Agent Identity in Microsoft Entra Admin Center. |
| **4** | **[Deploy Google Cloud Components & Agent Runtime](codelabs/entra-agent-id-gemini-platform.md#deploy-google-cloud-components--agent-runtime)** | Automated deployment of Workload Identity Pool, OIDC Provider, Cloud Storage bucket, and ADK agent. |
| **5** | **[Configure Federated Identity Credential in Microsoft Entra](codelabs/entra-agent-id-gemini-platform.md#configure-federated-identity-credential-in-microsoft-entra)** | Establish cryptographic trust link between Google Agent Runtime and Microsoft Entra Blueprint. |
| **6** | **[Understanding Workload Identity Federation & IAM](codelabs/entra-agent-id-gemini-platform.md#understanding-workload-identity-federation--iam-for-review)** | Deep dive into WIF pool, OIDC provider audiences, attribute mappings, and granular IAM policies. |
| **7** | **[Understanding ADK Agent Code & Token Adapters](codelabs/entra-agent-id-gemini-platform.md#understanding-adk-agent-code--token-adapters-for-review)** | Deep dive into RFC 7523 / RFC 8693 token exchange adapters and custom Google credentials providers. |
| **8** | **[Test & Verify End-to-End Execution](codelabs/entra-agent-id-gemini-platform.md#test--verify-end-to-end-execution)** | Execute live prompt with `agents-cli run` to verify identity federation and Cloud Storage access. |
| **9** | **[Congratulations](codelabs/entra-agent-id-gemini-platform.md#congratulations)** | Summary of learnings, security takeaways, and official documentation references. |

---

## 🛠 Quick Start / How to Run

### Option A: Interactive HTML Guide (Recommended)
Simply open the **[Live Hosted Codelab](https://egonzalezpozega.github.io/agent-platform-entra-id/)** or open [`docs/index.html`](docs/index.html) in your browser for the full interactive experience.

### Option B: Markdown Guide
1. Open [`codelabs/entra-agent-id-gemini-platform.md`](codelabs/entra-agent-id-gemini-platform.md) in your editor or markdown previewer.
2. In VS Code / Jetski, press **`Cmd + K, V`** (macOS) or **`Ctrl + K, V`** (Windows/Linux) to view the rendered codelab side-by-side.
3. Follow the instructions and copy/paste commands into your terminal or **Google Cloud Shell**.

Alternatively, if you use the [Codelabs CLI (`claat`)](https://github.com/googlecodelabs/tools), you can export the lab into standard Google Codelabs format:

```bash
cd codelabs && claat export entra-agent-id-gemini-platform.md
cp -r entra-agent-id-gemini-platform/* ../docs/
```

---

## 🧹 Resource Clean Up

Upon completing the exercises, clean up resources in your Google Cloud project using the provided teardown script:

```bash
chmod +x scripts/destroy_all.sh
./scripts/destroy_all.sh
```

This will automatically delete:
- Reasoning Engine deployment on Agent Runtime
- Cloud Storage bucket and test objects
- Workload Identity Pool and OIDC Provider
- Entra IAM policy bindings

---

## 📄 License

Apache 2.0 - Copyright 2026 Google LLC

