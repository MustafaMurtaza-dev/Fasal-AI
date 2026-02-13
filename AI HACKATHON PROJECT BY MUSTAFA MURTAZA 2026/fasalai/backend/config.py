from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "FasalAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    ROUTEWAY_API_KEY: str = ""
    ROUTEWAY_API_URL: str = "https://api.routeway.ai/v1"

    PRIMARY_MODEL: str = "gpt-oss-120b:free"
    FAST_MODEL: str = "gpt-oss-120b:free"
    BACKUP_MODEL: str = "deepseek-r1:free"

    DISEASE_MODEL_PATH: str = "app/data/trained_models/disease_classifier_v1.pth"

    OPENWEATHER_API_KEY: str = ""
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"

    MAX_IMAGE_SIZE_MB: int = 10
    LLM_MAX_RETRIES: int = 2
    LLM_TIMEOUT: int = 60

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
