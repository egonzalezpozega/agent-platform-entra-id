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

#
# Clean up all Google Cloud demo resources for Entra Agent ID Demo
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo -e "${YELLOW}================================================================${NC}"
echo -e "${YELLOW} Google Cloud Resource Cleanup: Entra Agent ID & Agent Gateway ${NC}"
echo -e "${YELLOW}================================================================${NC}"

# Load environment variables if present
if [[ -f "${ROOT_DIR}/.env" ]]; then
  log_info "Loading configuration from .env..."
  set -a
  source "${ROOT_DIR}/.env"
  set +a
fi

GCP_PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || true)}"
GCP_REGION="${GCP_REGION:-us-central1}"
WIF_POOL_ID="${WIF_POOL_ID:-entra-agent-pool}"
WIF_PROVIDER_ID="${WIF_PROVIDER_ID:-entra-oidc-provider}"
DEMO_BQ_DATASET="${DEMO_BIGQUERY_DATASET:-entra_agent_demo}"
ENTRA_AGENT_OBJECT_ID="${ENTRA_AGENT_OBJECT_ID:-}"

if [[ -z "${GCP_PROJECT_ID}" ]]; then
  read -rp "Enter your Google Cloud Project ID: " GCP_PROJECT_ID
fi

log_info "Target Project: ${GCP_PROJECT_ID} (Region: ${GCP_REGION})"
GCP_PROJECT_NUMBER=$(gcloud projects describe "${GCP_PROJECT_ID}" --format="value(projectNumber)" 2>/dev/null || true)

# 1. Delete Deployed Reasoning Engines for agent-gateway-entra
log_info "Step 1: Checking for deployed Agent Runtime Reasoning Engines..."
ACCESS_TOKEN=$(gcloud auth print-access-token 2>/dev/null || true)
if [[ -n "${ACCESS_TOKEN}" ]]; then
  REASONING_ENGINES_JSON=$(curl -s -H "Authorization: Bearer ${ACCESS_TOKEN}"     "https://${GCP_REGION}-aiplatform.googleapis.com/v1/projects/${GCP_PROJECT_ID}/locations/${GCP_REGION}/reasoningEngines")
  
  MATCHING_ENGINES=$(echo "${REASONING_ENGINES_JSON}" | jq -r '.reasoningEngines[]? | select(.displayName=="agent-gateway-entra") | .name' 2>/dev/null || true)
  
  if [[ -n "${MATCHING_ENGINES}" ]]; then
    for ENGINE_NAME in ${MATCHING_ENGINES}; do
      log_warn "Deleting Reasoning Engine: ${ENGINE_NAME}..."
      DELETE_RES=$(curl -s -X DELETE -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        "https://${GCP_REGION}-aiplatform.googleapis.com/v1/${ENGINE_NAME}?force=true")
      log_success "Delete result: ${DELETE_RES}"
    done
  else
    log_info "No deployed Reasoning Engines found with displayName 'agent-gateway-entra'."
  fi
else
  log_warn "Could not retrieve access token to list Reasoning Engines."
fi

# 2. Remove IAM Policy Bindings on Entra Principal
log_info "Step 2: Cleaning up IAM Policy Bindings..."
if [[ -n "${GCP_PROJECT_NUMBER}" && -n "${ENTRA_AGENT_OBJECT_ID}" ]]; then
  POOL_PATH="projects/${GCP_PROJECT_NUMBER}/locations/global/workloadIdentityPools/${WIF_POOL_ID}"
  ENTRA_PRINCIPAL="principal://iam.googleapis.com/${POOL_PATH}/subject/${ENTRA_AGENT_OBJECT_ID}"

  for ROLE in "roles/storage.objectViewer"; do
    log_info "Removing IAM role: ${ROLE} from ${ENTRA_PRINCIPAL}..."
    gcloud projects remove-iam-policy-binding "${GCP_PROJECT_ID}" \
      --member="${ENTRA_PRINCIPAL}" \
      --role="${ROLE}" \
      --quiet 2>/dev/null || log_warn "Role ${ROLE} was not bound or already removed."
  done
else
  log_info "Skipping explicit IAM binding removal (ENTRA_AGENT_OBJECT_ID not set)."
fi

# 3. Delete Demo Cloud Storage Buckets
log_info "Step 3: Cleaning up Cloud Storage buckets..."
for BUCKET_NAME in "${GCP_PROJECT_ID}-entra-agent-docs" "${GCP_PROJECT_ID}-agent-docs"; do
  if gcloud storage ls "gs://${BUCKET_NAME}" &>/dev/null; then
    log_warn "Deleting bucket gs://${BUCKET_NAME}..."
    gcloud storage rm -r "gs://${BUCKET_NAME}" --quiet || true
    log_success "Bucket gs://${BUCKET_NAME} deleted."
  fi
done

# 4. Delete Workload Identity Provider
log_info "Step 5: Cleaning up Workload Identity Provider..."
if gcloud iam workload-identity-pools providers describe "${WIF_PROVIDER_ID}"   --workload-identity-pool="${WIF_POOL_ID}"   --location=global   --project="${GCP_PROJECT_ID}" &>/dev/null; then
  log_warn "Deleting Workload Identity Provider ${WIF_PROVIDER_ID}..."
  gcloud iam workload-identity-pools providers delete "${WIF_PROVIDER_ID}"     --workload-identity-pool="${WIF_POOL_ID}"     --location=global     --project="${GCP_PROJECT_ID}"     --quiet || true
  log_success "Provider ${WIF_PROVIDER_ID} deleted."
else
  log_info "Provider ${WIF_PROVIDER_ID} does not exist."
fi

# 6. Delete Workload Identity Pool
log_info "Step 6: Cleaning up Workload Identity Pool..."
if gcloud iam workload-identity-pools describe "${WIF_POOL_ID}"   --location=global   --project="${GCP_PROJECT_ID}" &>/dev/null; then
  log_warn "Deleting Workload Identity Pool ${WIF_POOL_ID}..."
  gcloud iam workload-identity-pools delete "${WIF_POOL_ID}"     --location=global     --project="${GCP_PROJECT_ID}"     --quiet || true
  log_success "Pool ${WIF_POOL_ID} deleted."
else
  log_info "Pool ${WIF_POOL_ID} does not exist."
fi

echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN} Cleanup Completed Successfully!${NC}"
echo -e "${GREEN}================================================================${NC}"
