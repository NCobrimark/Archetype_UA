from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    from pydantic import field_validator
    
    BOT_TOKEN: str = ""
    
    @field_validator("BOT_TOKEN", mode="before")
    @classmethod
    def clean_token(cls, v):
        return v.strip() if v else v

    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "google/gemini-2.0-flash-exp:free"
    DATABASE_URL: str = "sqlite+aiosqlite:///./archetype.db"
    ADMIN_EMAIL: str = "admin@example.com"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()
