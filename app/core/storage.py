from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
import os
from io import BytesIO
from app.config import settings
import logging

# Azure imports (lazy loaded in AzureBlobStorageClient)
try:
    from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
except ImportError:
    BlobServiceClient = None
    generate_blob_sas = None
    BlobSasPermissions = None

logger = logging.getLogger(__name__)


class BaseStorageClient(ABC):
    """Abstract base class for storage clients."""
    
    @abstractmethod
    async def upload_file(self, file_content: bytes, blob_path: str, content_type: Optional[str] = None) -> str:
        """
        Upload a file to storage.
        
        Args:
            file_content: File content as bytes
            blob_path: Path where file should be stored
            content_type: MIME type of the file
            
        Returns:
            URL of the uploaded file
        """
        pass
    
    @abstractmethod
    async def upload_file_from_path(self, local_path: str, blob_path: str, content_type: Optional[str] = None) -> str:
        """
        Upload a file from local filesystem to storage.
        
        Args:
            local_path: Local file path
            blob_path: Path where file should be stored
            content_type: MIME type of the file
            
        Returns:
            URL of the uploaded file
        """
        pass
    
    @abstractmethod
    async def download_file(self, blob_path: str) -> bytes:
        """
        Download a file from storage.
        
        Args:
            blob_path: Path to the file in storage
            
        Returns:
            File content as bytes
        """
        pass
    
    @abstractmethod
    async def delete_file(self, blob_path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            blob_path: Path to the file in storage
            
        Returns:
            True if deleted successfully
        """
        pass
    
    @abstractmethod
    async def get_file_url(self, blob_path: str, expiry_seconds: int = 3600) -> str:
        """
        Get a signed URL for downloading/accessing the file.
        
        Args:
            blob_path: Path to the file in storage
            expiry_seconds: URL expiry time in seconds
            
        Returns:
            Signed download URL
        """
        pass
    
    @abstractmethod
    async def get_upload_url(self, blob_path: str, expiry_seconds: int = 3600, content_type: Optional[str] = None) -> str:
        """
        Get a presigned URL for uploading a file directly to storage.
        
        Args:
            blob_path: Path where file should be uploaded
            expiry_seconds: URL expiry time in seconds
            content_type: MIME type of the file to upload
            
        Returns:
            Presigned upload URL
        """
        pass
    
    @abstractmethod
    async def file_exists(self, blob_path: str) -> bool:
        """
        Check if a file exists in storage.
        
        Args:
            blob_path: Path to the file in storage
            
        Returns:
            True if file exists
        """
        pass
    
    @staticmethod
    def generate_blob_path(org_id: str, project_id: str, file_id: str, stage: str, filename: str) -> str:
        """
        Generate standardized blob storage path.
        
        Args:
            org_id: Organization ID (for data isolation and migration)
            project_id: Project ID
            file_id: File ID
            stage: Processing stage (raw, converted, enriched, chunks)
            filename: Original filename (preserved for RAG context)
            
        Returns:
            Blob path string
        
        Examples:
            - org_id/project_id/file_id/raw/document.pdf
            - org_id/project_id/file_id/converted/document.pdf
            - org_id/project_id/file_id/enriched/document.json
            
        Benefits of org_id prefix:
            - Easy data export/migration per organization
            - Physical isolation at storage level
            - Backup/restore by organization
            - Future sharding capabilities
        """
        return f"{org_id}/{project_id}/{file_id}/{stage}/{filename}"


class AzureBlobStorageClient(BaseStorageClient):
    """Azure Blob Storage implementation."""
    
    def __init__(self):
        """Initialize Azure Blob Storage client."""
        if not settings.azure_storage_connection_string:
            raise ValueError("Azure Storage connection string not configured")
        
        self.connection_string = settings.azure_storage_connection_string
        self.container_name = settings.azure_storage_container_name
        
        # Initialize blob service client
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string
        )
        
        # Get or create container
        self.container_client: ContainerClient = self.blob_service_client.get_container_client(
            self.container_name
        )
        
        # Create container if it doesn't exist
        try:
            self.container_client.create_container()
            logger.info(f"Created container: {self.container_name}")
        except Exception as e:
            # Container might already exist
            logger.debug(f"Container {self.container_name} already exists or error: {str(e)}")
    
    async def upload_file(self, file_content: bytes, blob_path: str, content_type: Optional[str] = None) -> str:
        """Upload file to Azure Blob Storage."""
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            
            # Upload with content type
            content_settings = None
            if content_type:
                from azure.storage.blob import ContentSettings
                content_settings = ContentSettings(content_type=content_type)
            
            blob_client.upload_blob(
                file_content,
                overwrite=True,
                content_settings=content_settings
            )
            
            logger.info(f"Uploaded file to {blob_path}")
            return blob_client.url
            
        except Exception as e:
            logger.error(f"Error uploading file to {blob_path}: {str(e)}")
            raise
    
    async def upload_file_from_path(self, local_path: str, blob_path: str, content_type: Optional[str] = None) -> str:
        """Upload file from local path to Azure Blob Storage."""
        try:
            with open(local_path, "rb") as data:
                file_content = data.read()
            
            return await self.upload_file(file_content, blob_path, content_type)
            
        except Exception as e:
            logger.error(f"Error uploading file from {local_path} to {blob_path}: {str(e)}")
            raise
    
    async def download_file(self, blob_path: str) -> bytes:
        """Download file from Azure Blob Storage."""
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            download_stream = blob_client.download_blob()
            file_content = download_stream.readall()
            
            logger.info(f"Downloaded file from {blob_path}")
            return file_content
            
        except Exception as e:
            logger.error(f"Error downloading file from {blob_path}: {str(e)}")
            raise
    
    async def delete_file(self, blob_path: str) -> bool:
        """Delete file from Azure Blob Storage."""
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            blob_client.delete_blob()
            
            logger.info(f"Deleted file from {blob_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file from {blob_path}: {str(e)}")
            return False
    
    async def get_file_url(self, blob_path: str, expiry_seconds: int = 3600) -> str:
        """Get signed download URL for Azure Blob Storage file."""
        try:
            from datetime import datetime, timedelta
            from azure.storage.blob import generate_blob_sas, BlobSasPermissions
            
            blob_client = self.container_client.get_blob_client(blob_path)
            
            # Generate SAS token for download (read permission)
            sas_token = generate_blob_sas(
                account_name=blob_client.account_name,
                container_name=self.container_name,
                blob_name=blob_path,
                account_key=self.blob_service_client.credential.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(seconds=expiry_seconds)
            )
            
            # Construct URL with SAS token
            signed_url = f"{blob_client.url}?{sas_token}"
            
            logger.info(f"Generated signed download URL for {blob_path}")
            return signed_url
            
        except Exception as e:
            logger.error(f"Error generating signed URL for {blob_path}: {str(e)}")
            raise
    
    async def get_upload_url(self, blob_path: str, expiry_seconds: int = 3600, content_type: Optional[str] = None) -> str:
        """Get presigned upload URL for Azure Blob Storage."""
        try:
            from datetime import datetime, timedelta
            from azure.storage.blob import generate_blob_sas, BlobSasPermissions
            
            blob_client = self.container_client.get_blob_client(blob_path)
            
            # Generate SAS token for upload (create, write permissions)
            sas_token = generate_blob_sas(
                account_name=blob_client.account_name,
                container_name=self.container_name,
                blob_name=blob_path,
                account_key=self.blob_service_client.credential.account_key,
                permission=BlobSasPermissions(create=True, write=True),
                expiry=datetime.utcnow() + timedelta(seconds=expiry_seconds)
            )
            
            # Construct URL with SAS token
            upload_url = f"{blob_client.url}?{sas_token}"
            
            logger.info(f"Generated presigned upload URL for {blob_path}")
            return upload_url
            
        except Exception as e:
            logger.error(f"Error generating upload URL for {blob_path}: {str(e)}")
            raise
    
    async def file_exists(self, blob_path: str) -> bool:
        """Check if file exists in Azure Blob Storage."""
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            return blob_client.exists()
            
        except Exception as e:
            logger.error(f"Error checking file existence for {blob_path}: {str(e)}")
            return False


class SupabaseStorageClient(BaseStorageClient):
    """Supabase Storage implementation."""
    
    def __init__(self):
        """Initialize Supabase Storage client."""
        if not settings.supabase_url or not settings.supabase_key:
            raise ValueError("Supabase URL and Key not configured")
        
        from supabase import create_client, Client
        
        self.supabase_url = settings.supabase_url
        self.supabase_key = settings.supabase_key
        self.bucket_name = settings.supabase_bucket_name
        
        # Initialize Supabase client
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Get or create bucket
        try:
            # Try to get bucket
            buckets = self.client.storage.list_buckets()
            bucket_exists = any(b.name == self.bucket_name for b in buckets)
            
            if not bucket_exists:
                # Create bucket if it doesn't exist
                self.client.storage.create_bucket(self.bucket_name, options={"public": False})
                logger.info(f"Created Supabase bucket: {self.bucket_name}")
            else:
                logger.info(f"Using existing Supabase bucket: {self.bucket_name}")
        except Exception as e:
            logger.warning(f"Note: {str(e)}. Bucket might already exist.")
    
    async def upload_file(self, file_content: bytes, blob_path: str, content_type: Optional[str] = None) -> str:
        """Upload file to Supabase Storage."""
        try:
            # Prepare file options
            file_options = {"content-type": content_type} if content_type else {}
            
            # Upload to Supabase
            self.client.storage.from_(self.bucket_name).upload(
                path=blob_path,
                file=file_content,
                file_options=file_options
            )
            
            # Get public URL
            url = self.client.storage.from_(self.bucket_name).get_public_url(blob_path)
            
            logger.info(f"Uploaded file to Supabase: {blob_path}")
            return url
            
        except Exception as e:
            logger.error(f"Error uploading file to Supabase {blob_path}: {str(e)}")
            raise
    
    async def upload_file_from_path(self, local_path: str, blob_path: str, content_type: Optional[str] = None) -> str:
        """Upload file from local path to Supabase Storage."""
        try:
            with open(local_path, "rb") as data:
                file_content = data.read()
            
            return await self.upload_file(file_content, blob_path, content_type)
            
        except Exception as e:
            logger.error(f"Error uploading file from {local_path} to {blob_path}: {str(e)}")
            raise
    
    async def download_file(self, blob_path: str) -> bytes:
        """Download file from Supabase Storage."""
        try:
            file_content = self.client.storage.from_(self.bucket_name).download(blob_path)
            
            logger.info(f"Downloaded file from Supabase: {blob_path}")
            return file_content
            
        except Exception as e:
            logger.error(f"Error downloading file from Supabase {blob_path}: {str(e)}")
            raise
    
    async def delete_file(self, blob_path: str) -> bool:
        """Delete file from Supabase Storage."""
        try:
            self.client.storage.from_(self.bucket_name).remove([blob_path])
            
            logger.info(f"Deleted file from Supabase: {blob_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file from Supabase {blob_path}: {str(e)}")
            return False
    
    async def get_file_url(self, blob_path: str, expiry_seconds: int = 3600) -> str:
        """Get signed download URL for Supabase Storage file."""
        try:
            # Create signed URL with expiry
            signed_url = self.client.storage.from_(self.bucket_name).create_signed_url(
                blob_path,
                expiry_seconds
            )
            
            logger.info(f"Generated signed download URL for Supabase file: {blob_path}")
            return signed_url['signedURL']
            
        except Exception as e:
            logger.error(f"Error generating signed URL for {blob_path}: {str(e)}")
            raise
    
    async def get_upload_url(self, blob_path: str, expiry_seconds: int = 3600, content_type: Optional[str] = None) -> str:
        """Get presigned upload URL for Supabase Storage."""
        try:
            # Supabase upload URL
            # Create signed upload URL with expiry
            signed_upload_url = self.client.storage.from_(self.bucket_name).create_signed_upload_url(
                blob_path
            )
            
            logger.info(f"Generated presigned upload URL for Supabase: {blob_path}")
            return signed_upload_url['signedURL']
            
        except Exception as e:
            logger.error(f"Error generating upload URL for {blob_path}: {str(e)}")
            raise
    
    async def file_exists(self, blob_path: str) -> bool:
        """Check if file exists in Supabase Storage."""
        try:
            # Try to get file info
            self.client.storage.from_(self.bucket_name).download(blob_path)
            return True
        except:
            return False


def get_storage_client() -> BaseStorageClient:
    """
    Factory function to get the appropriate storage client.
    Prioritizes Azure Blob Storage (better Python 3.14 compatibility than Supabase).
    Can be extended to support other storage backends (AWS S3, GCS, etc.)
    """
    # Use Azure Blob Storage (no Python 3.14 compatibility issues)
    if settings.azure_storage_connection_string:
        logger.info("Using Azure Blob Storage")
        return AzureBlobStorageClient()
    
    # Fall back to Supabase (has Python 3.14 issues)
    elif settings.supabase_url and settings.supabase_key:
        logger.warning("Using Supabase Storage (may have Python 3.14 compatibility issues)")
        return SupabaseStorageClient()
    
    else:
        raise ValueError(
            "No storage backend configured. Please set AZURE_STORAGE_CONNECTION_STRING "
            "in your .env file"
        )

