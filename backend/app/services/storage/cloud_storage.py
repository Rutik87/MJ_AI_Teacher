import os
import hashlib
from pathlib import Path
from typing import Optional, Union
import httpx

from app.config import settings
from app.utils.logger import logger

class CloudStorageService:
    """
    Production cloud storage service for persistent PDF and media management.
    Supports private Supabase Storage buckets with secure signed URL generation,
    streaming, SHA-256 checksums, and resilient local fallback for offline development.
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        service_role_key: Optional[str] = None,
        bucket_name: Optional[str] = None
    ):
        self.supabase_url = (supabase_url or getattr(settings, "SUPABASE_URL", "") or "").rstrip("/")
        self.service_key = (
            service_role_key or
            getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "") or
            getattr(settings, "SUPABASE_KEY", "") or
            ""
        )
        self.bucket = bucket_name or getattr(settings, "SUPABASE_STORAGE_BUCKET", "mpsc-books")
        self.local_base_dir = Path(getattr(settings, "DATA_PATH", "./data")) / "cloud_storage_local" / self.bucket
        self.local_base_dir.mkdir(parents=True, exist_ok=True)
        self._bucket_initialized = False

    @property
    def is_supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.service_key)

    def calculate_checksum(self, data: bytes) -> str:
        """Computes SHA-256 checksum for duplicate detection."""
        return hashlib.sha256(data).hexdigest()

    def _get_headers(self, content_type: str = "application/pdf") -> dict:
        return {
            "Authorization": f"Bearer {self.service_key}",
            "apikey": self.service_key,
            "Content-Type": content_type
        }

    async def ensure_bucket_exists(self):
        """Ensures the private Supabase Storage bucket exists."""
        if not self.is_supabase_configured or self._bucket_initialized:
            return

        try:
            url = f"{self.supabase_url}/storage/v1/bucket"
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    url,
                    headers=self._get_headers("application/json"),
                    json={
                        "id": self.bucket,
                        "name": self.bucket,
                        "public": False,
                        "file_size_limit": 157286400,  # 150MB
                        "allowed_mime_types": ["application/pdf"]
                    }
                )
                if res.status_code in [200, 201, 400, 409]:
                    # 400/409 means bucket already exists
                    self._bucket_initialized = True
                    logger.info(f"Supabase Storage bucket [{self.bucket}] initialized/verified.")
        except Exception as e:
            logger.warning(f"Note: Could not verify Supabase bucket (proceeding): {e}")

    async def upload_file(
        self,
        file_bytes: bytes,
        storage_path: str,
        content_type: str = "application/pdf"
    ) -> str:
        """
        Uploads file to private Supabase Storage bucket.
        Returns the persistent storage path.
        """
        storage_path = storage_path.lstrip("/")
        
        if self.is_supabase_configured:
            await self.ensure_bucket_exists()
            url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{storage_path}"
            headers = self._get_headers(content_type)
            headers["x-upsert"] = "true"

            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(url, headers=headers, content=file_bytes)
                if res.status_code not in [200, 201]:
                    # Try PUT if POST returns 400 or already exists
                    res = await client.put(url, headers=headers, content=file_bytes)
                
                if res.status_code in [200, 201]:
                    logger.info(f"Successfully uploaded [{storage_path}] to Supabase Storage bucket [{self.bucket}].")
                    return storage_path
                else:
                    logger.error(f"Supabase Storage upload failed ({res.status_code}): {res.text}")
                    raise RuntimeError(f"Storage upload failed: {res.status_code} - {res.text}")

        # Local storage fallback for local development without Supabase keys
        local_target = self.local_base_dir / storage_path
        local_target.parent.mkdir(parents=True, exist_ok=True)
        with open(local_target, "wb") as f:
            f.write(file_bytes)
        logger.info(f"Saved to local persistent storage fallback: {local_target}")
        return storage_path

    async def download_file(self, storage_path: str) -> bytes:
        """Downloads file content as bytes from Supabase Storage."""
        storage_path = storage_path.lstrip("/")

        if self.is_supabase_configured:
            url = f"{self.supabase_url}/storage/v1/object/authenticated/{self.bucket}/{storage_path}"
            headers = {
                "Authorization": f"Bearer {self.service_key}",
                "apikey": self.service_key
            }
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    return res.content
                
                # Fallback to standard object path
                url2 = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{storage_path}"
                res2 = await client.get(url2, headers=headers)
                if res2.status_code == 200:
                    return res2.content
                
                logger.error(f"Failed to download [{storage_path}] from Supabase Storage: {res.status_code}")
                raise FileNotFoundError(f"Storage file not found: {storage_path}")

        # Local fallback
        local_target = self.local_base_dir / storage_path
        if local_target.exists():
            with open(local_target, "rb") as f:
                return f.read()
        
        raise FileNotFoundError(f"Local storage file not found: {storage_path}")

    async def delete_file(self, storage_path: str) -> bool:
        """Deletes file from Supabase Storage bucket."""
        storage_path = storage_path.lstrip("/")

        if self.is_supabase_configured:
            url = f"{self.supabase_url}/storage/v1/object/{self.bucket}"
            headers = self._get_headers("application/json")
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.request(
                    "DELETE",
                    url,
                    headers=headers,
                    json={"prefixes": [storage_path]}
                )
                if res.status_code in [200, 204]:
                    logger.info(f"Deleted [{storage_path}] from Supabase Storage.")
                    return True
                logger.warning(f"Delete storage file status ({res.status_code}): {res.text}")
                return False

        # Local fallback
        local_target = self.local_base_dir / storage_path
        if local_target.exists():
            try:
                local_target.unlink()
                return True
            except Exception as e:
                logger.warning(f"Could not delete local file: {e}")
                return False
        return True

    async def file_exists(self, storage_path: str) -> bool:
        """Checks if a file exists in Supabase Storage."""
        storage_path = storage_path.lstrip("/")

        if self.is_supabase_configured:
            try:
                folder = "/".join(storage_path.split("/")[:-1])
                filename = storage_path.split("/")[-1]
                url = f"{self.supabase_url}/storage/v1/object/list/{self.bucket}"
                headers = self._get_headers("application/json")
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.post(
                        url,
                        headers=headers,
                        json={"prefix": folder, "limit": 100}
                    )
                    if res.status_code == 200:
                        files = res.json()
                        return any(f.get("name") == filename for f in files)
            except Exception:
                pass
            return False

        return (self.local_base_dir / storage_path).exists()

    async def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """Generates a secure temporary signed URL for private bucket access."""
        storage_path = storage_path.lstrip("/")

        if self.is_supabase_configured:
            url = f"{self.supabase_url}/storage/v1/object/sign/{self.bucket}/{storage_path}"
            headers = self._get_headers("application/json")
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    url,
                    headers=headers,
                    json={"expiresIn": expires_in}
                )
                if res.status_code == 200:
                    data = res.json()
                    signed_part = data.get("signedURL", "")
                    if signed_part.startswith("http"):
                        return signed_part
                    return f"{self.supabase_url}/storage/v1{signed_part}"
                else:
                    logger.error(f"Failed to generate signed URL ({res.status_code}): {res.text}")

        # Local fallback signed URL
        return f"/api/books/file/{storage_path}"

cloud_storage = CloudStorageService()
