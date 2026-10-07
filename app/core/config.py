from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List, Union

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    GEMINI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    
    OPENAI_MODEL_NAME: str = "gpt-4o"
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash"
    DEEPSEEK_MODEL_NAME: str = "deepseek-chat"
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 1
    
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str

    # Where the service listens. PORT is also what docker-compose publishes,
    # so one line in .env moves both.
    HOST: str = "0.0.0.0"
    PORT: int = 5011

    # The public address report links are built from - it goes into every
    # report_url handed back to the portal, so it must match how the service
    # is reached (behind nginx: https://psychometry.meshilogic.com/StudentProfile).
    BASE_URL: str = "http://localhost:5011"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8',
        case_sensitive=True
    )

settings = Settings()