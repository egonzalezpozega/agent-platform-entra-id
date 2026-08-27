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

"""GCP Data Tools demonstrating IAM access authorized via the Entra Agent ID principal."""

import logging
from typing import List, Dict, Any

from google.cloud import storage

from agent.auth.credentials import EntraFederatedCredentials
from agent.config import settings

logger = logging.getLogger(__name__)


def read_storage_document(file_name: str) -> Dict[str, Any]:
    """Reads and returns the text content of a document in Cloud Storage using federated Entra credentials.

    Args:
        file_name: The name/path of the file in the bucket to read (e.g. 'sales_audit_2026.txt').

    Returns:
        A dictionary with the file content or error details.
    """
    logger.info("Reading document '%s' from Cloud Storage...", file_name)

    if settings.mock_auth:
        return {
            "status": "success",
            "mode": "mock",
            "file_name": file_name,
            "content": f"Mock content for {file_name} under Entra governance.",
        }

    try:
        credentials = EntraFederatedCredentials(settings)
        client = storage.Client(project=settings.gcp_project_id, credentials=credentials)
        raw_bucket = getattr(settings, "demo_gcs_bucket", "agent-docs")
        bucket_name = (
            raw_bucket
            if raw_bucket.startswith(settings.gcp_project_id)
            else f"{settings.gcp_project_id}-{raw_bucket}"
        )
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        content = blob.download_as_text()
        return {
            "status": "success",
            "bucket": bucket_name,
            "file_name": file_name,
            "content": content,
        }
    except Exception as exc:
        logger.error("Storage read execution failed: %s", exc)
        return {
            "status": "error",
            "error_type": type(exc).__name__,
            "message": str(exc),
            "hint": "The Entra Agent ID token exchange back to Google STS failed or requires custom App ID URI scope configuration.",
        }


def list_storage_documents(prefix: str = "") -> Dict[str, Any]:
    """Lists enterprise documents from Google Cloud Storage using the federated Entra Agent ID credentials.

    Args:
        prefix: Object prefix to filter files.

    Returns:
        A dictionary with the file list or diagnostic error details.
    """
    logger.info("Initializing Cloud Storage client with EntraFederatedCredentials...")

    if settings.mock_auth:
        return {
            "status": "success",
            "mode": "mock",
            "files": ["contracts/2026-q1-report.pdf", "compliance/entra_spiffe_audit.json", "sales/q4_forecast.xlsx"],
        }

    try:
        credentials = EntraFederatedCredentials(settings)
        client = storage.Client(project=settings.gcp_project_id, credentials=credentials)
        raw_bucket = getattr(settings, "demo_gcs_bucket", "agent-docs")
        bucket_name = (
            raw_bucket
            if raw_bucket.startswith(settings.gcp_project_id)
            else f"{settings.gcp_project_id}-{raw_bucket}"
        )
        bucket = client.bucket(bucket_name)
        blobs = client.list_blobs(bucket, prefix=prefix)
        files = [blob.name for blob in blobs]
        return {
            "status": "success",
            "bucket": bucket_name,
            "files": files,
        }
    except Exception as exc:
        logger.error("Storage list execution failed: %s", exc)
        return {
            "status": "error",
            "error_type": type(exc).__name__,
            "message": str(exc),
            "hint": "The Entra Agent ID token exchange back to Google STS failed or requires custom App ID URI scope configuration.",
        }
