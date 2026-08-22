from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Dayflow"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = "change_this_to_a_secure_random_string_in_production"
    ALGORITHM: str = "HS256"
    
    POSTGRES_USER: str = "dayflow_user"
    POSTGRES_PASSWORD: str = "dayflow_password"
    POSTGRES_DB: str = "dayflow"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173"]
    ENVIRONMENT: str = "development"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"

settings = Settings()
