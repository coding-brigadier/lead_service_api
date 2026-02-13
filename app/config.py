from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@tryalma.com"

    ATTORNEY_EMAIL: str = "attorney@tryalma.com"

    # Storage: "local" or "s3"
    STORAGE_BACKEND: str = "local"
    UPLOAD_DIR: str = "uploads"

    # S3 (required when STORAGE_BACKEND=s3)
    S3_BUCKET: str = ""
    S3_REGION: str = "us-east-1"
    S3_PREFIX: str = "resumes/"
    S3_ENDPOINT_URL: str = ""  # optional, for MinIO / LocalStack

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
