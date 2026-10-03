from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollaya_url: str = "http://localhost:11435"
    ollaya_model: str = "laya:multilingual"
    ollaya_timeout: float = 30.0

    mongodb_uri: str
    mongodb_db: str = "dublinfix"
    media_dir: str = "media"
    max_photo_bytes: int = 5_000_000


settings = Settings()
