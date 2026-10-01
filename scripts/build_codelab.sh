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

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CODELABS_DIR="${ROOT_DIR}/codelabs"
DOCS_DIR="${ROOT_DIR}/docs"
CODELAB_FILE="entra-agent-id-gemini-platform.md"
CODELAB_ID="entra-agent-id-gemini-platform"

echo "=== Building Codelab ==="

# Check claat installation
if ! command -v claat &> /dev/null; then
  echo "Error: claat CLI is not installed or not in PATH."
  echo "Install it with: go install github.com/googlecodelabs/tools/claat@latest"
  exit 1
fi

# Ensure vendored claat-public assets exist
CLAAT_PUBLIC_DIR="${CODELABS_DIR}/claat-public"
mkdir -p "${CLAAT_PUBLIC_DIR}"

if [[ ! -f "${CLAAT_PUBLIC_DIR}/codelab-elements.js" ]]; then
  echo "Downloading self-hosted claat assets..."
  curl -sL https://cdn.jsdelivr.net/npm/codelab-elements@1.0.1/codelab-elements.css -o "${CLAAT_PUBLIC_DIR}/codelab-elements.css"
  curl -sL https://cdn.jsdelivr.net/npm/codelab-elements@1.0.1/codelab-elements.js -o "${CLAAT_PUBLIC_DIR}/codelab-elements.js"
  curl -sL https://cdn.jsdelivr.net/npm/@webcomponents/custom-elements@1.2.4/src/native-shim.js -o "${CLAAT_PUBLIC_DIR}/native-shim.js"
  curl -sL https://cdn.jsdelivr.net/npm/@webcomponents/custom-elements@1.2.4/custom-elements.min.js -o "${CLAAT_PUBLIC_DIR}/custom-elements.min.js"
  curl -sL https://cdn.jsdelivr.net/npm/code-prettify@0.1.0/loader/prettify.js -o "${CLAAT_PUBLIC_DIR}/prettify.js"
fi

# Export codelab using relative prefix
echo "Exporting ${CODELAB_FILE} with claat (-prefix .)..."
cd "${CODELABS_DIR}"
claat export -prefix . "${CODELAB_FILE}"

# Sync assets
echo "Syncing assets to exported codelab and docs/..."
cp -r "${CLAAT_PUBLIC_DIR}" "${CODELABS_DIR}/${CODELAB_ID}/"
mkdir -p "${DOCS_DIR}"
cp -r "${CODELABS_DIR}/${CODELAB_ID}/"* "${DOCS_DIR}/"

echo "=== Codelab build completed successfully ==="
