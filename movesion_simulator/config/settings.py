"""Application settings and configuration management."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Movesion Business Model Simulator"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    
    # Data paths
    data_dir: Path = Path(__file__).resolve().parent.parent / "data"
    pricing_plan_file: str = "pricing_plan_wallester.json"
    scenario_presets_file: str = "scenario_presets.json"
    
    # Simulation defaults
    default_horizon_months: int = 36
    max_horizon_months: int = 120
    
    # CORS settings
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    @property
    def pricing_plan_path(self) -> Path:
        """Full path to pricing plan JSON file."""
        return self.data_dir / self.pricing_plan_file
    
    @property
    def scenario_presets_path(self) -> Path:
        """Full path to scenario presets JSON file."""
        return self.data_dir / self.scenario_presets_file
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
