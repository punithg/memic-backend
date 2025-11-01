"""
Storage helper for parsing module.

Provides utilities for reading and writing files to Azure Blob Storage
specifically for the parsing pipeline.
"""

import json
import logging
from typing import Any

from app.services.azure_storage import AzureStorageClient

logger = logging.getLogger(__name__)


class ParsingStorageHelper:
    """Helper class for parsing-related storage operations."""

    def __init__(self, storage_client: AzureStorageClient):
        """
        Initialize storage helper.

        Args:
            storage_client: Azure storage client instance
        """
        self.storage_client = storage_client

    async def download_file(self, blob_path: str) -> bytes:
        """
        Download file from Azure Blob Storage.

        Args:
            blob_path: Path to blob in storage

        Returns:
            bytes: File content

        Raises:
            RuntimeError: If download fails
        """
        try:
            logger.info(f"Downloading file from: {blob_path}")
            content = await self.storage_client.download_file(blob_path)
            logger.info(f"Downloaded {len(content)} bytes from {blob_path}")
            return content
        except Exception as e:
            logger.error(f"Failed to download file from {blob_path}: {str(e)}")
            raise RuntimeError(f"Failed to download file: {str(e)}")

    async def upload_enriched_json(
        self, enriched_json: dict[str, Any], blob_path: str
    ) -> str:
        """
        Upload enriched JSON to Azure Blob Storage.

        Args:
            enriched_json: Enriched document JSON
            blob_path: Destination path in storage

        Returns:
            str: Blob path where file was uploaded

        Raises:
            RuntimeError: If upload fails
        """
        try:
            # Convert to JSON string
            json_content = json.dumps(enriched_json, indent=2, ensure_ascii=False)
            json_bytes = json_content.encode("utf-8")

            logger.info(f"Uploading enriched JSON to: {blob_path}")
            await self.storage_client.upload_file(
                file_content=json_bytes,
                blob_name=blob_path,
                content_type="application/json",
            )

            logger.info(
                f"Uploaded {len(json_bytes)} bytes of enriched JSON to {blob_path}"
            )
            return blob_path

        except Exception as e:
            logger.error(f"Failed to upload enriched JSON to {blob_path}: {str(e)}")
            raise RuntimeError(f"Failed to upload enriched JSON: {str(e)}")

    def generate_enriched_json_path(
        self, org_id: str, project_id: str, file_id: str
    ) -> str:
        """
        Generate standardized path for enriched JSON files.

        Args:
            org_id: Organization ID
            project_id: Project ID
            file_id: File ID

        Returns:
            str: Blob path for enriched JSON
        """
        return f"{org_id}/{project_id}/{file_id}/enriched/enriched.json"
