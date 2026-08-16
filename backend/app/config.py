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


settings = Settings()
