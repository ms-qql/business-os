from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    database_url: str = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/business_os"
    )
    jwt_secret: str = os.environ.get("JWT_SECRET", "dev-only-insecure-change-me")
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = int(os.environ.get("ACCESS_TTL_MIN", "60"))
    argon_time_cost: int = int(os.environ.get("ARGON_TIME_COST", "2"))
    argon_memory_cost: int = int(os.environ.get("ARGON_MEMORY_COST", "102400"))
    argon_parallelism: int = int(os.environ.get("ARGON_PARALLELISM", "8"))
    throttle_max_failures: int = 5
    throttle_window_minutes: int = 15
    invitation_ttl_hours: int = int(os.environ.get("INVITE_TTL_H", "72"))
    reset_ttl_minutes: int = int(os.environ.get("RESET_TTL_MIN", "60"))
    minio_endpoint: str = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
    minio_access_key: str = os.environ.get("MINIO_ACCESS_KEY", "")
    minio_secret_key: str = os.environ.get("MINIO_SECRET_KEY", "")
    minio_bucket: str = os.environ.get("MINIO_BUCKET", "business-os")
    minio_secure: bool = os.environ.get("MINIO_SECURE", "false").lower() == "true"
    anfrage_rate_limit_max: int = int(os.environ.get("ANFRAGE_RATE_LIMIT_MAX", "20"))
    anfrage_rate_limit_window_minutes: int = int(os.environ.get("ANFRAGE_RATE_LIMIT_WINDOW_MIN", "15"))
    # Shared Secret, das nur der interne Next.js-Proxy kennt. Nur wenn dieses
    # Secret im Request-Header mitgeschickt wird, ist X-Forwarded-Host vertrauenswürdig
    # (siehe SEC-1: der Header ist sonst clientseitig spoofbar).
    internal_proxy_secret: str = os.environ.get("INTERNAL_PROXY_SECRET", "")


settings = Settings()
