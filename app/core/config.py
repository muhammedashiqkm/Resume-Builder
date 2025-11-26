from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, AnyHttpUrl
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

    BACKEND_CORS_ORIGINS: Union[List[str], str] = []

    BASE_URL: str = "http://localhost:8000"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """
        Parses a comma-separated string OR a JSON-formatted list.
        """
        if isinstance(v, str):
            if v.strip().startswith("["):
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        
        return v or []

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8',
        case_sensitive=True
    )

settings = Settings()