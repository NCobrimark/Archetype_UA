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
    
    @field_validator("OPENAI_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY", mode="before")
    @classmethod
    def clean_keys(cls, v):
        return v.strip().replace('"', '').replace("'", "") if isinstance(v, str) else v

    def model_post_init(self, __context):
        # Fallback: if user provided OpenRouter key in OPENAI_API_KEY slot (common mistake)
        if self.OPENAI_API_KEY.startswith("sk-or-") and not self.OPENROUTER_API_KEY:
            self.OPENROUTER_API_KEY = self.OPENAI_API_KEY
        # If OPENROUTER_API_KEY is still empty but OPENAI_API_KEY has something, use it as fallback
        elif self.OPENAI_API_KEY and not self.OPENROUTER_API_KEY:
            self.OPENROUTER_API_KEY = self.OPENAI_API_KEY

    DATABASE_URL: str = "sqlite+aiosqlite:///./archetype.db"
    ADMIN_EMAIL: str = "admin@example.com"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    @field_validator("SMTP_PASSWORD", "SMTP_USER", mode="before")
    @classmethod
    def clean_smtp(cls, v):
        return v.strip() if isinstance(v, str) else v
    
    class Config:
        env_file = ".env"

settings = Settings()
