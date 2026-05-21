from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_port: int
    postgres_domain: str
    database_url: str
    
    SECRET_KEY: str
    ALGORITHM: str
    
    cloudinary_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()