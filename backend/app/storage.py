from __future__ import annotations

import io
from typing import Any

from .config import settings


class BaseStorage:
    """Abstraction over object storage. DB rows store only the object key;
    URLs are resolved to short-lived presigned GET URLs at read time."""

    def put_object(self, object_key: str, data: bytes, content_type: str) -> None:
        raise NotImplementedError

    def presigned_get_url(self, object_key: str, expires_seconds: int = 3600) -> str:
        raise NotImplementedError


class MinioStorage(BaseStorage):
    """Production storage (MinIO, S3-compatible). Client connects lazily on
    first use so importing this module never touches the network."""

    def __init__(self) -> None:
        self._client: Any = None

    def _get_client(self):
        if self._client is None:
            from minio import Minio

            self._client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure,
            )
            if not self._client.bucket_exists(settings.minio_bucket):
                self._client.make_bucket(settings.minio_bucket)
        return self._client

    def put_object(self, object_key: str, data: bytes, content_type: str) -> None:
        client = self._get_client()
        client.put_object(
            settings.minio_bucket, object_key, io.BytesIO(data),
            length=len(data), content_type=content_type,
        )

    def presigned_get_url(self, object_key: str, expires_seconds: int = 3600) -> str:
        import datetime

        client = self._get_client()
        return client.presigned_get_object(
            settings.minio_bucket, object_key,
            expires=datetime.timedelta(seconds=expires_seconds),
        )


class InMemoryStorage(BaseStorage):
    """Test double: keeps bytes in-process, returns a stable fake URL."""

    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}

    def put_object(self, object_key: str, data: bytes, content_type: str) -> None:
        self._objects[object_key] = data

    def presigned_get_url(self, object_key: str, expires_seconds: int = 3600) -> str:
        return f"memory://{object_key}"


storage: BaseStorage = MinioStorage()


def set_storage(s: BaseStorage) -> None:
    global storage
    storage = s
