from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    access_token_expire_minutes: int 
    refresh_token_expire_days: int 
    algorithm: str
    upload_directory: str
    max_upload_size_bytes: int 
    enable_sla_worker: bool = False
    sla_worker_interval_seconds: int

    model_config = SettingsConfigDict(
        env_file=".env"
    )


settings = Settings()