from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    MAX_FILE_SIZE: int = Field(default=5 * 1024 * 1024, gt=0)
    MAX_INFLIGHT: int = Field(default=4, gt=0)
    EXTRACT_URL: str = "http://extract:8080"
    DOCUMENTS_URL: str = "http://documents:8000"
    UPSTREAM_TIMEOUT: float = Field(default=20, gt=0)
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
