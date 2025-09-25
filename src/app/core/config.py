import os
from enum import Enum
from typing import List

from starlette.datastructures import CommaSeparatedStrings

from pydantic_settings import BaseSettings
from pydantic import ConfigDict, field_validator, validator
from starlette.config import Config
from pydantic import Json

current_file_dir = os.path.dirname(os.path.realpath(__file__))
env_path = os.path.join(current_file_dir, "..", "..", ".env")
config = Config(env_path)


class AppSettings(BaseSettings):
    APP_NAME: str = config("APP_NAME", default="FastAPI app")
    APP_DESCRIPTION: str | None = config("APP_DESCRIPTION", default=None)
    APP_VERSION: str | None = config("APP_VERSION", default=None)
    LICENSE_NAME: str | None = config("LICENSE", default=None)
    CONTACT_NAME: str | None = config("CONTACT_NAME", default=None)
    CONTACT_EMAIL: str | None = config("CONTACT_EMAIL", default=None)
    ENVIRONMENT: str = config("ENVIRONMENT", cast=str, default="local")


class CryptSettings(BaseSettings):
    SECRET_KEY: str = config("SECRET_KEY")
    ALGORITHM: str = config("ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = config("REFRESH_TOKEN_EXPIRE_DAYS", default=7)


class DatabaseSettings(BaseSettings):
    pass


class SQLiteSettings(DatabaseSettings):
    SQLITE_URI: str = config("SQLITE_URI", default="./sql_app.db")
    SQLITE_SYNC_PREFIX: str = config("SQLITE_SYNC_PREFIX", default="sqlite:///")
    SQLITE_ASYNC_PREFIX: str = config("SQLITE_ASYNC_PREFIX", default="sqlite+aiosqlite:///")


class MySQLSettings(DatabaseSettings):
    MYSQL_USER: str = config("MYSQL_USER", default="username")
    MYSQL_PASSWORD: str = config("MYSQL_PASSWORD", default="password")
    MYSQL_SERVER: str = config("MYSQL_SERVER", default="localhost")
    MYSQL_PORT: int = config("MYSQL_PORT", default=5432)
    MYSQL_DB: str = config("MYSQL_DB", default="dbname")
    MYSQL_URI: str = f"{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_SERVER}:{MYSQL_PORT}/{MYSQL_DB}"
    MYSQL_SYNC_PREFIX: str = config("MYSQL_SYNC_PREFIX", default="mysql://")
    MYSQL_ASYNC_PREFIX: str = config("MYSQL_ASYNC_PREFIX", default="mysql+aiomysql://")
    MYSQL_URL: str = config("MYSQL_URL", default=None)


class PostgresSettings(DatabaseSettings):
    POSTGRES_USER: str = config("POSTGRES_USER", default="postgres")
    POSTGRES_PASSWORD: str = config("POSTGRES_PASSWORD", default="postgres")
    POSTGRES_SERVER: str = config("POSTGRES_SERVER", default="localhost")
    POSTGRES_PORT: int = config("POSTGRES_PORT", default=5432)
    POSTGRES_DB: str = config("POSTGRES_DB", default="postgres")
    POSTGRES_SYNC_PREFIX: str = config("POSTGRES_SYNC_PREFIX", default="postgresql://")
    POSTGRES_ASYNC_PREFIX: str = config("POSTGRES_ASYNC_PREFIX", default="postgresql+asyncpg://")
    POSTGRES_URI: str = f"{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    POSTGRES_URL: str | None = config("POSTGRES_URL", default=None)


class FirstUserSettings(BaseSettings):
    ADMIN_NAME: str = config("ADMIN_NAME", default="admin")
    ADMIN_EMAIL: str = config("ADMIN_EMAIL", default="admin@admin.com")
    ADMIN_USERNAME: str = config("ADMIN_USERNAME", default="admin")
    ADMIN_PASSWORD: str = config("ADMIN_PASSWORD", default="!Ch4ng3Th1sP4ssW0rd!")


class TestSettings(BaseSettings):
    ...


class RedisCacheSettings(BaseSettings):
    REDIS_CACHE_HOST: str = config("REDIS_CACHE_HOST", default="localhost")
    REDIS_CACHE_PORT: int = config("REDIS_CACHE_PORT", default=6379)
    REDIS_CACHE_URL: str = f"redis://{REDIS_CACHE_HOST}:{REDIS_CACHE_PORT}"


class ClientSideCacheSettings(BaseSettings):
    CLIENT_CACHE_MAX_AGE: int = config("CLIENT_CACHE_MAX_AGE", default=60)


class RedisQueueSettings(BaseSettings):
    REDIS_QUEUE_HOST: str = config("REDIS_QUEUE_HOST", default="localhost")
    REDIS_QUEUE_PORT: int = config("REDIS_QUEUE_PORT", default=6379)


class RedisRateLimiterSettings(BaseSettings):
    REDIS_RATE_LIMIT_HOST: str = config("REDIS_RATE_LIMIT_HOST", default="localhost")
    REDIS_RATE_LIMIT_PORT: int = config("REDIS_RATE_LIMIT_PORT", default=6379)
    REDIS_RATE_LIMIT_URL: str = f"redis://{REDIS_RATE_LIMIT_HOST}:{REDIS_RATE_LIMIT_PORT}"


class DefaultRateLimitSettings(BaseSettings):
    DEFAULT_RATE_LIMIT_LIMIT: int = config("DEFAULT_RATE_LIMIT_LIMIT", default=10)
    DEFAULT_RATE_LIMIT_PERIOD: int = config("DEFAULT_RATE_LIMIT_PERIOD", default=3600)


class LiveKitSettings(BaseSettings):
    LIVEKIT_HOST: str = config("LIVEKIT_URL")
    LIVEKIT_API_KEY: str = config("LIVEKIT_API_KEY")
    LIVEKIT_API_SECRET: str = config("LIVEKIT_API_SECRET")
    LIVEKIT_ENABLE_WORKER: bool = config("LIVEKIT_ENABLE_WORKER", default=True)
    LIVEKIT_SIP_HOST: str = config("LIVEKIT_SIP_HOST")  # Added this line

class LLMSettings(BaseSettings):
    CARTESIA_API_KEY: str = config("CARTESIA_API_KEY", default="")
    OPENAI_API_KEY: str = config("OPENAI_API_KEY", default="")
    DEEPGRAM_API_KEY: str = config("DEEPGRAM_API_KEY", default="")
    GOOGLE_API_KEY: str = config("GOOGLE_API_KEY", default="")
    ELEVENLABS_API_KEY: str = config("ELEVENLABS_API_KEY", default="")
    UPLIFT_API_KEY: str = config("UPLIFT_API_KEY", default="")


class QdrantSettings(BaseSettings):
    QDRANT_API_KEY: str = config("QDRANT_API_KEY")
    QDRANT_URL: str = config("QDRANT_URL")

class TwilioSettings(BaseSettings):
    TWILIO_ACCOUNT_SID: str = config("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = config("TWILIO_AUTH_TOKEN")

class S3Settings(BaseSettings):
    S3_BUCKET_NAME: str = config("S3_BUCKET_NAME", default="convoi-backend-call-logs")
    AWS_ACCESS_KEY_ID: str = config("AWS_ACCESS_KEY_ID", default="")
    AWS_SECRET_ACCESS_KEY: str = config("AWS_SECRET_ACCESS_KEY", default="")
    AWS_REGION: str = config("AWS_REGION", default="")

class SIPSettings(BaseSettings):
    LIVEKIT_SIP_INBOUND_USERNAME: str = config("LIVEKIT_SIP_INBOUND_USERNAME")  # Added this line
    LIVEKIT_SIP_INBOUND_PASSWORD: str = config("LIVEKIT_SIP_INBOUND_PASSWORD")  # Added this line

class EnvironmentOption(Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentSettings(BaseSettings):
    ENVIRONMENT: EnvironmentOption = config("ENVIRONMENT", default="local")

class CORSSettings(BaseSettings):
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://dashboard.convoi.ai",
        "http://dashboard.convoi.ai/backend",
        "https://3bf380aaf6c0.ngrok-free.app"
    ]

# class CORSSettings(BaseSettings):
#     CORS_ORIGINS: Json[List[str]] = '["http://localhost:3000", "http://51.21.44.167:3002", "http://51.21.44.167:8888", "https://3bf380aaf6c0.ngrok-free.app"]'

class Settings(
    AppSettings,
    PostgresSettings,
    CryptSettings,
    FirstUserSettings,
    TestSettings,
    RedisCacheSettings,
    ClientSideCacheSettings,
    RedisQueueSettings,
    RedisRateLimiterSettings,
    DefaultRateLimitSettings,
    EnvironmentSettings,
    LiveKitSettings,
    LLMSettings,
    QdrantSettings,
    S3Settings,
    TwilioSettings,
    CORSSettings,
    SIPSettings
):
    pass

settings = Settings()