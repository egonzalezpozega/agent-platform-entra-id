#!/usr/bin/env bash
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

# ==============================================================================
# One-Click Deployment Script for Google Cloud Components
# ==============================================================================
# Automatically sets up:
#   1. Google Cloud APIs (Agent Runtime, WIF, STS, BigQuery, GCS)
#   2. Workload Identity Federation (WIF) Pool & Provider for Microsoft Entra ID
#   3. Demo Cloud Storage Bucket & Sample Files
#   4. Fine-grained IAM Permissions for the Microsoft Entra Agent Principal
#   5. Synchronize .env & agents-cli-manifest.yaml
#   6. Deploy to Agent Runtime via agents-cli with Agent Identity
# ==============================================================================


set -euo pipefail

# Color formatting
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================================${NC}"
echo -e "${BLUE}  One-Click Google Cloud Deploy: Entra Agent ID & Agent Platform    ${NC}"
echo -e "${BLUE}====================================================================${NC}"

# Load existing .env if present
if [[ -f .env ]]; then
  echo -e "${GREEN}Loading variables from .env...${NC}"
  export GCP_PROJECT_ID=epbgonzalez-agent-gateway GCP_PROJECT_NUMBER=374927797243 GCP_REGION=us-central1 GOOGLE_AGENT_IDENTITY_SA=entra-agent-runtime-sa@epbgonzalez-agent-gateway.iam.gserviceaccount.com GOOGLE_AGENT_IDENTITY_AUDIENCE=api://AzureADTokenExchange WIF_POOL_ID=entra-agent-pool WIF_PROVIDER_ID=entra-oidc-provider ENTRA_TENANT_ID=cc2c59dc-7f33-441c-bfac-ec4e73182d0a ENTRA_CLIENT_ID=a46680b6-9643-4c22-af5e-e9e7303a6471 ENTRA_AGENT_OBJECT_ID=e5a1e0b3-ed9c-4fa4-84cb-050128d063a8 ENTRA_SCOPE=api://AzureADTokenExchange/.default DEMO_BIGQUERY_DATASET=entra_agent_demo DEMO_BIGQUERY_TABLE=sales_records MOCK_AUTH=false
fi

# Required Variables with Prompts if missing
GCP_PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo '')}"
if [[ -z "$GCP_PROJECT_ID" ]]; then
  read -rp "Enter your Google Cloud Project ID: " GCP_PROJECT_ID
fi

GCP_REGION="${GCP_REGION:-us-central1}"
ENTRA_TENANT_ID="${ENTRA_TENANT_ID:-}"
ENTRA_CLIENT_ID="${ENTRA_CLIENT_ID:-}"
ENTRA_AGENT_OBJECT_ID="${ENTRA_AGENT_OBJECT_ID:-}"

if [[ -z "$ENTRA_TENANT_ID" ]]; then
  read -rp "Enter Microsoft Entra Directory (Tenant) ID: " ENTRA_TENANT_ID
fi
if [[ -z "$ENTRA_CLIENT_ID" ]]; then
  read -rp "Enter Microsoft Entra Blueprint Application (Client) ID: " ENTRA_CLIENT_ID
fi
if [[ -z "$ENTRA_AGENT_OBJECT_ID" ]]; then
  read -rp "Enter Microsoft Entra Agent Identity Object ID: " ENTRA_AGENT_OBJECT_ID
fi

echo -e "\n${YELLOW}Deployment Parameters:${NC}"
echo "  Google Cloud Project : $GCP_PROJECT_ID"
echo "  Region               : $GCP_REGION"
echo "  Entra Tenant ID      : $ENTRA_TENANT_ID"
echo "  Entra Blueprint ID   : $ENTRA_CLIENT_ID"
echo "  Entra Agent Object ID: $ENTRA_AGENT_OBJECT_ID"
echo "--------------------------------------------------------------------"

# 1. Resolve Project Number
echo -e "\n${GREEN}[1/7] Resolving Project Number...${NC}"
GCP_PROJECT_NUMBER=$(gcloud projects describe "$GCP_PROJECT_ID" --format="value(projectNumber)")
echo "Resolved Project Number: $GCP_PROJECT_NUMBER"

# 2. Enable APIs
echo -e "\n${GREEN}[2/7] Enabling Required Google Cloud APIs...${NC}"
gcloud services enable \
  aiplatform.googleapis.com \
  iam.googleapis.com \
  sts.googleapis.com \
  bigquery.googleapis.com \
  storage.googleapis.com \
  --project="$GCP_PROJECT_ID"


# 3. Create or Update Workload Identity Pool and Provider
echo -e "\n${GREEN}[3/7] Configuring Workload Identity Federation (WIF)...${NC}"
WIF_POOL_ID="entra-agent-pool"
WIF_PROVIDER_ID="entra-oidc-provider"

POOL_STATE=$(gcloud iam workload-identity-pools describe "$WIF_POOL_ID" --location="global" --project="$GCP_PROJECT_ID" --format="value(state)" 2>/dev/null || true)
if [[ -z "$POOL_STATE" ]]; then
  echo "Creating Workload Identity Pool: $WIF_POOL_ID..."
  gcloud iam workload-identity-pools create "$WIF_POOL_ID" \
    --location="global" \
    --display-name="Entra Agent ID Pool" \
    --description="Workload Identity Pool for Microsoft Entra Agent ID federation" \
    --project="$GCP_PROJECT_ID"
elif [[ "$POOL_STATE" == "DELETED" ]]; then
  echo "Undeleting Workload Identity Pool: $WIF_POOL_ID..."
  gcloud iam workload-identity-pools undelete "$WIF_POOL_ID" \
    --location="global" \
    --project="$GCP_PROJECT_ID"
else
  echo "Workload Identity Pool $WIF_POOL_ID is active."
fi

AUDIENCES="fb60f99c-7a34-4190-8149-302f77469936"
AUDIENCES+=",api://AzureADTokenExchange"
AUDIENCES+=",https://graph.microsoft.com"
AUDIENCES+=",00000003-0000-0000-c000-000000000000"
AUDIENCES+=",${ENTRA_CLIENT_ID}"
AUDIENCES+=",api://${ENTRA_CLIENT_ID}"

MAPPINGS="google.subject=assertion.sub"
MAPPINGS+=",attribute.tid=assertion.tid"
MAPPINGS+=",attribute.oid=assertion.oid"
MAPPINGS+=",attribute.appid=assertion.appid"
MAPPINGS+=",attribute.agent_id=assertion.sub"

PROVIDER_STATE=$(gcloud iam workload-identity-pools providers describe "$WIF_PROVIDER_ID" \
  --workload-identity-pool="$WIF_POOL_ID" --location="global" --project="$GCP_PROJECT_ID" --format="value(state)" 2>/dev/null || true)

if [[ -z "$PROVIDER_STATE" ]]; then
  echo "Creating OIDC Provider: $WIF_PROVIDER_ID..."
  gcloud iam workload-identity-pools providers create-oidc "$WIF_PROVIDER_ID" \
    --workload-identity-pool="$WIF_POOL_ID" \
    --location="global" \
    --display-name="Microsoft Entra IdP Provider" \
    --issuer-uri="https://login.microsoftonline.com/${ENTRA_TENANT_ID}/v2.0" \
    --allowed-audiences="${AUDIENCES}" \
    --attribute-mapping="${MAPPINGS}" \
    --attribute-condition="assertion.tid == '${ENTRA_TENANT_ID}'" \
    --project="$GCP_PROJECT_ID"
elif [[ "$PROVIDER_STATE" == "DELETED" ]]; then
  echo "Undeleting OIDC Provider: $WIF_PROVIDER_ID..."
  gcloud iam workload-identity-pools providers undelete "$WIF_PROVIDER_ID" \
    --workload-identity-pool="$WIF_POOL_ID" \
    --location="global" \
    --project="$GCP_PROJECT_ID"
  echo "Updating OIDC Provider configuration..."
  gcloud iam workload-identity-pools providers update-oidc "$WIF_PROVIDER_ID" \
    --workload-identity-pool="$WIF_POOL_ID" \
    --location="global" \
    --display-name="Microsoft Entra IdP Provider" \
    --issuer-uri="https://login.microsoftonline.com/${ENTRA_TENANT_ID}/v2.0" \
    --allowed-audiences="${AUDIENCES}" \
    --attribute-mapping="${MAPPINGS}" \
    --attribute-condition="assertion.tid == '${ENTRA_TENANT_ID}'" \
    --project="$GCP_PROJECT_ID"
else
  echo "Updating OIDC Provider: $WIF_PROVIDER_ID..."
  gcloud iam workload-identity-pools providers update-oidc "$WIF_PROVIDER_ID" \
    --workload-identity-pool="$WIF_POOL_ID" \
    --location="global" \
    --display-name="Microsoft Entra IdP Provider" \
    --issuer-uri="https://login.microsoftonline.com/${ENTRA_TENANT_ID}/v2.0" \
    --allowed-audiences="${AUDIENCES}" \
    --attribute-mapping="${MAPPINGS}" \
    --attribute-condition="assertion.tid == '${ENTRA_TENANT_ID}'" \
    --project="$GCP_PROJECT_ID"
fi

# 4. Provision Demo Data (Cloud Storage)
echo -e "\n${GREEN}[4/7] Setting up Demo Data (Cloud Storage)...${NC}"

# Cloud Storage Buckets & Files
for GCS_BUCKET in "${GCP_PROJECT_ID}-agent-docs" "${GCP_PROJECT_ID}-entra-agent-docs"; do
  if ! gcloud storage buckets describe "gs://${GCS_BUCKET}" >/dev/null 2>&1; then
    echo "Creating Cloud Storage Bucket: gs://${GCS_BUCKET}..."
    gcloud storage buckets create "gs://${GCS_BUCKET}" --project="$GCP_PROJECT_ID" --location="$GCP_REGION"
  fi

  echo "Uploading sample documents to gs://${GCS_BUCKET}..."
  echo "Sales audit summary for Q1 2026: All transactions verified against Microsoft Entra Agent ID governance." | \
    gcloud storage cp - "gs://${GCS_BUCKET}/sales_audit_2026.txt"
  echo "Federation Guide: Google Agent Runtime SPIFFE bootstrapped and federated to Entra Agent ID." | \
    gcloud storage cp - "gs://${GCS_BUCKET}/entra_federation_guide.txt"
done

# 5. Grant IAM Roles to the Entra Agent Principal
echo -e "\n${GREEN}[5/7] Granting IAM Roles to Entra Agent Principal...${NC}"
POOL_PATH="projects/${GCP_PROJECT_NUMBER}/locations/global/workloadIdentityPools/${WIF_POOL_ID}"
ENTRA_PRINCIPAL="principal://iam.googleapis.com/${POOL_PATH}/subject/${ENTRA_AGENT_OBJECT_ID}"

echo "Principal: $ENTRA_PRINCIPAL"

gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
  --member="${ENTRA_PRINCIPAL}" \
  --role="roles/storage.objectViewer" \
  --condition=None --quiet >/dev/null

# 6. Synchronize Configuration (.env and agents-cli-manifest.yaml)
echo -e "\n${GREEN}[6/7] Updating Project Configuration...${NC}"
cat << EOV > .env
GCP_PROJECT_ID=${GCP_PROJECT_ID}
GCP_PROJECT_NUMBER=${GCP_PROJECT_NUMBER}
GCP_REGION=${GCP_REGION}
WIF_POOL_ID=${WIF_POOL_ID}
WIF_PROVIDER_ID=${WIF_PROVIDER_ID}
ENTRA_TENANT_ID=${ENTRA_TENANT_ID}
ENTRA_CLIENT_ID=${ENTRA_CLIENT_ID}
ENTRA_AGENT_OBJECT_ID=${ENTRA_AGENT_OBJECT_ID}
ENTRA_SCOPE=api://AzureADTokenExchange/.default
DEMO_GCS_BUCKET=${GCS_BUCKET}
MOCK_AUTH=false
EOV

cat << EOV > agents-cli-manifest.yaml
name: agent-platform-entra-id
description: "Microsoft Entra Agent ID on Google Cloud Agent Runtime"
version: "1.4.1"
agent_directory: agent
create_params:
  deployment_target: agent_runtime
  session_type: none
  cicd_runner: skip
project: ${GCP_PROJECT_ID}
region: ${GCP_REGION}
agent_identity: true
update_env_vars: GCP_PROJECT_ID=${GCP_PROJECT_ID},GCP_PROJECT_NUMBER=${GCP_PROJECT_NUMBER},GCP_REGION=${GCP_REGION},WIF_POOL_ID=${WIF_POOL_ID},WIF_PROVIDER_ID=${WIF_PROVIDER_ID},ENTRA_TENANT_ID=${ENTRA_TENANT_ID},ENTRA_CLIENT_ID=${ENTRA_CLIENT_ID},ENTRA_AGENT_OBJECT_ID=${ENTRA_AGENT_OBJECT_ID},ENTRA_SCOPE=api://AzureADTokenExchange/.default,DEMO_GCS_BUCKET=${GCS_BUCKET},MOCK_AUTH=false
EOV

# 7. Deploy to Agent Runtime
echo -e "\n${GREEN}[7/7] Deploying Agent to Agent Runtime with Agent Identity...${NC}"
agents-cli deploy \
  --deployment-target agent_runtime \
  --project "$GCP_PROJECT_ID" \
  --region "$GCP_REGION" \
  --agent-identity \
  --no-confirm-project


echo -e "\n${GREEN}====================================================================${NC}"
echo -e "${GREEN}  One-Click Deployment Complete!                                    ${NC}"
echo -e "${GREEN}====================================================================${NC}"
echo -e "You can now test the live agent using:"
echo -e "${YELLOW}agents-cli run --mode adk \"Inspect your active identity, list documents from Cloud Storage, and read 'sales_audit_2026.txt'.\"${NC}\n"
