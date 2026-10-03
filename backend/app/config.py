from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollaya_url: str = "http://localhost:11435"
    ollaya_model: str = "laya:multilingual"
    ollaya_timeout: float = 30.0


settings = Settings()
