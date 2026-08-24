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

    def get_object(self, object_key: str) -> bytes:
        raise NotImplementedError

    def delete_object(self, object_key: str) -> None:
        raise NotImplementedError


class MinioStorage(BaseStorage):
    """Production storage (MinIO, S3-compatible). Client connects lazily on
    first use so importing this module never touches the network.

    Defaults to the shared `MINIO_*` settings; pass explicit args to bind an
    instance to a different (e.g. dedicated) endpoint/account/bucket — see
    `image_storage` below (PROJ-23)."""

    def __init__(self, endpoint: str | None = None, access_key: str | None = None,
                secret_key: str | None = None, bucket: str | None = None,
                secure: bool | None = None) -> None:
        self._client: Any = None
        self._endpoint = settings.minio_endpoint if endpoint is None else endpoint
        self._access_key = settings.minio_access_key if access_key is None else access_key
        self._secret_key = settings.minio_secret_key if secret_key is None else secret_key
        self._bucket = settings.minio_bucket if bucket is None else bucket
        self._secure = settings.minio_secure if secure is None else secure

    def _get_client(self):
        if self._client is None:
            from minio import Minio

            self._client = Minio(
                self._endpoint,
                access_key=self._access_key,
                secret_key=self._secret_key,
                secure=self._secure,
            )
            if not self._client.bucket_exists(self._bucket):
                self._client.make_bucket(self._bucket)
        return self._client

    def put_object(self, object_key: str, data: bytes, content_type: str) -> None:
        client = self._get_client()
        client.put_object(
            self._bucket, object_key, io.BytesIO(data),
            length=len(data), content_type=content_type,
        )

    def presigned_get_url(self, object_key: str, expires_seconds: int = 3600) -> str:
        import datetime

        client = self._get_client()
        return client.presigned_get_object(
            self._bucket, object_key,
            expires=datetime.timedelta(seconds=expires_seconds),
        )

    def get_object(self, object_key: str) -> bytes:
        response = self._get_client().get_object(self._bucket, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete_object(self, object_key: str) -> None:
        client = self._get_client()
        client.remove_object(self._bucket, object_key)


class InMemoryStorage(BaseStorage):
    """Test double: keeps bytes in-process, returns a stable fake URL."""

    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}

    def put_object(self, object_key: str, data: bytes, content_type: str) -> None:
        self._objects[object_key] = data

    def presigned_get_url(self, object_key: str, expires_seconds: int = 3600) -> str:
        return f"memory://{object_key}"

    def get_object(self, object_key: str) -> bytes:
        return self._objects[object_key]

    def delete_object(self, object_key: str) -> None:
        self._objects.pop(object_key, None)


storage: BaseStorage = MinioStorage()

# PROJ-23: dedizierter Business-OS-Bildspeicher für neue Website-Sektionsbilder
# (WEBSITE_IMAGES_MINIO_*), vollständig getrennt vom allgemeinen `storage`
# (ImmoCRM-Legacy-Ablage). Kein gemeinsamer Client, kein gemeinsamer Bucket.
image_storage: BaseStorage = MinioStorage(
    endpoint=settings.website_images_minio_endpoint,
    access_key=settings.website_images_minio_access_key,
    secret_key=settings.website_images_minio_secret_key,
    bucket=settings.website_images_minio_bucket,
    secure=settings.website_images_minio_secure,
)


def set_storage(s: BaseStorage) -> None:
    global storage
    storage = s


def set_image_storage(s: BaseStorage) -> None:
    global image_storage
    image_storage = s
