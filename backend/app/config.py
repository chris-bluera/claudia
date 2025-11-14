"""
Configuration management for Claudia backend
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Database
    database_url: str = Field(
        default="postgresql://claudia:password@localhost:5432/claudia",
        description="PostgreSQL connection URL"
    )

    # Backend server
    backend_host: str = Field(default="0.0.0.0")
    backend_port: int = Field(default=8000)
    backend_log_level: str = Field(default="INFO")

    # Claude Code paths
    claude_projects_path: Path = Field(
        default=Path.home() / ".claude" / "projects",
        description="Path to Claude Code projects directory"
    )
    claude_settings_path: Path = Field(
        default=Path.home() / ".claude",
        description="Path to Claude Code settings directory"
    )

    # pgvector settings (for future use)
    embedding_model: str = Field(
        default="openai/text-embedding-3-small",
        description="Embedding model for pgvector (via OpenRouter)"
    )
    openrouter_api_key: Optional[str] = Field(
        default=None,
        description="OpenRouter API key for embeddings"
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL"
    )

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        case_sensitive = False

        # Allow reading from environment variables
        # Variables will be read as CLAUDIA_<field_name>
        env_prefix = ""

# Create global settings instance
settings = Settings()

# Ensure required directories exist
def ensure_directories():
    """Ensure required directories exist"""
    directories = [
        settings.claude_projects_path,
        settings.claude_settings_path,
    ]

    for directory in directories:
        if not directory.exists():
            print(f"Warning: Directory {directory} does not exist")

# Run on import
ensure_directories()