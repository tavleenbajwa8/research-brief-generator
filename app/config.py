"""
Configuration settings for the Research Brief Generator application.
"""

from typing import Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    google_api_key: Optional[str] = Field(None, env="GOOGLE_API_KEY")
    
    # LangSmith Configuration
    langsmith_api_key: Optional[str] = Field(None, env="LANGSMITH_API_KEY")
    langsmith_project: str = Field("research-brief-generator", env="LANGSMITH_PROJECT")
    langsmith_tracing_v2: bool = Field(True, env="LANGSMITH_TRACING_V2")
    
    # Database Configuration
    database_url: str = Field("sqlite:///./research_briefs.db", env="DATABASE_URL")
    
    # Application Settings
    app_name: str = Field("Research Brief Generator", env="APP_NAME")
    app_version: str = Field("1.0.0", env="APP_VERSION")
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # Server Configuration
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    
    # Search Configuration
    max_search_results: int = Field(10, env="MAX_SEARCH_RESULTS")
    search_timeout: int = Field(30, env="SEARCH_TIMEOUT")
    
    # LLM Configuration
    default_model: str = Field("gpt-4", env="DEFAULT_MODEL")
    summarization_model: str = Field("gemini-1.5-pro", env="SUMMARIZATION_MODEL")
    max_tokens: int = Field(4000, env="MAX_TOKENS")
    temperature: float = Field(0.1, env="TEMPERATURE")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(10, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(100, env="RATE_LIMIT_PER_HOUR")
    
    model_config = ConfigDict(env_file=".env", case_sensitive=False)


# Global settings instance
settings = Settings() 