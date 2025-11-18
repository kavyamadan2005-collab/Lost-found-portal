import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Lost & Found Portal API"
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/lost_found_portal")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_SECRET")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24


settings = Settings()
