"""Centralized configuration management for the trading agent."""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

from .defaults import (
    DEFAULT_STRATEGY_PARAMS,
    DEFAULT_TEMPLATE_VALUES,
    DEFAULT_API_CONFIG,
    DEFAULT_DOCKER_CONFIG,
    DEFAULT_LANGCHAIN_CONFIG,
    DEFAULT_CHROMADB_CONFIG,
    DEFAULT_PATHS
)

# Load environment variables
load_dotenv()


class Settings:
    """Centralized settings management with environment variable support."""
    
    def __init__(self):
        self._strategy_params = None
        self._template_values = None
        self._api_config = None
        self._docker_config = None
        self._langchain_config = None
        self._chromadb_config = None
        self._paths = None
    
    @property
    def google_api_key(self) -> Optional[str]:
        """Get Google API key from environment."""
        return os.getenv("GOOGLE_API_KEY")
    
    @property
    def strategy_params(self) -> Dict[str, Any]:
        """Get strategy parameters with environment variable overrides."""
        if self._strategy_params is None:
            self._strategy_params = {
                'imbalance_threshold': self._get_env_float('IMBALANCE_THRESHOLD', DEFAULT_STRATEGY_PARAMS['imbalance_threshold']),
                'min_volume_threshold': self._get_env_float('MIN_VOLUME_THRESHOLD', DEFAULT_STRATEGY_PARAMS['min_volume_threshold']),
                'lookback_periods': self._get_env_int('LOOKBACK_PERIODS', DEFAULT_STRATEGY_PARAMS['lookback_periods']),
                'signal_cooldown_ms': self._get_env_int('SIGNAL_COOLDOWN_MS', DEFAULT_STRATEGY_PARAMS['signal_cooldown_ms']),
            }
        return self._strategy_params
    
    @property
    def template_values(self) -> Dict[str, Any]:
        """Get template values with strategy parameters included."""
        if self._template_values is None:
            self._template_values = {
                **DEFAULT_TEMPLATE_VALUES,
                **self.strategy_params
            }
        return self._template_values
    
    @property
    def api_config(self) -> Dict[str, Any]:
        """Get API configuration with environment overrides."""
        if self._api_config is None:
            self._api_config = {
                'host': os.getenv('API_HOST', DEFAULT_API_CONFIG['host']),
                'port': self._get_env_int('API_PORT', DEFAULT_API_CONFIG['port']),
                'cors_origins': self._get_env_list('CORS_ORIGINS', DEFAULT_API_CONFIG['cors_origins']),
                'max_chat_history': self._get_env_int('MAX_CHAT_HISTORY', DEFAULT_API_CONFIG['max_chat_history']),
            }
        return self._api_config
    
    @property
    def docker_config(self) -> Dict[str, Any]:
        """Get Docker configuration with environment overrides."""
        if self._docker_config is None:
            self._docker_config = {
                'build_timeout': self._get_env_int('DOCKER_BUILD_TIMEOUT', DEFAULT_DOCKER_CONFIG['build_timeout']),
                'signal_output_port': self._get_env_int('SIGNAL_OUTPUT_PORT', DEFAULT_DOCKER_CONFIG['signal_output_port']),
                'signal_output_bind_ip': os.getenv('SIGNAL_OUTPUT_BIND_IP', DEFAULT_DOCKER_CONFIG['signal_output_bind_ip']),
            }
        return self._docker_config
    
    @property
    def langchain_config(self) -> Dict[str, Any]:
        """Get LangChain configuration with environment overrides."""
        if self._langchain_config is None:
            self._langchain_config = {
                'model': os.getenv('LANGCHAIN_MODEL', DEFAULT_LANGCHAIN_CONFIG['model']),
                'temperature': self._get_env_float('LANGCHAIN_TEMPERATURE', DEFAULT_LANGCHAIN_CONFIG['temperature']),
                'max_iterations': self._get_env_int('LANGCHAIN_MAX_ITERATIONS', DEFAULT_LANGCHAIN_CONFIG['max_iterations']),
                'verbose': self._get_env_bool('LANGCHAIN_VERBOSE', DEFAULT_LANGCHAIN_CONFIG['verbose']),
            }
        return self._langchain_config
    
    @property
    def chromadb_config(self) -> Dict[str, Any]:
        """Get ChromaDB configuration with environment overrides."""
        if self._chromadb_config is None:
            self._chromadb_config = {
                'persist_directory': os.getenv('CHROMADB_PERSIST_DIR', DEFAULT_CHROMADB_CONFIG['persist_directory']),
                'collection_name': os.getenv('CHROMADB_COLLECTION', DEFAULT_CHROMADB_CONFIG['collection_name']),
                'embedding_model': os.getenv('CHROMADB_EMBEDDING_MODEL', DEFAULT_CHROMADB_CONFIG['embedding_model']),
            }
        return self._chromadb_config
    
    @property
    def paths(self) -> Dict[str, str]:
        """Get file paths with environment overrides."""
        if self._paths is None:
            base_dir = Path.cwd()
            self._paths = {
                'generated_algorithms': str(base_dir / os.getenv('GENERATED_ALGORITHMS_DIR', DEFAULT_PATHS['generated_algorithms'])),
                'rust_template': str(base_dir / os.getenv('RUST_TEMPLATE_PATH', DEFAULT_PATHS['rust_template'])),
                'dockerfile_template': str(base_dir / os.getenv('DOCKERFILE_TEMPLATE_PATH', DEFAULT_PATHS['dockerfile_template'])),
                'chromadb_path': str(base_dir / os.getenv('CHROMADB_PATH', DEFAULT_PATHS['chromadb_path'])),
            }
        return self._paths
    
    def _get_env_int(self, key: str, default: int) -> int:
        """Get integer from environment variable with fallback to default."""
        try:
            return int(os.getenv(key, default))
        except (ValueError, TypeError):
            return default
    
    def _get_env_float(self, key: str, default: float) -> float:
        """Get float from environment variable with fallback to default."""
        try:
            return float(os.getenv(key, default))
        except (ValueError, TypeError):
            return default
    
    def _get_env_bool(self, key: str, default: bool) -> bool:
        """Get boolean from environment variable with fallback to default."""
        value = os.getenv(key, '').lower()
        if value in ('true', '1', 'yes', 'on'):
            return True
        elif value in ('false', '0', 'no', 'off'):
            return False
        return default
    
    def _get_env_list(self, key: str, default: list) -> list:
        """Get list from environment variable (comma-separated) with fallback to default."""
        value = os.getenv(key)
        if value:
            return [item.strip() for item in value.split(',')]
        return default
    
    def validate_required_settings(self) -> None:
        """Validate that required settings are present."""
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        # Validate paths exist
        rust_template_path = Path(self.paths['rust_template'])
        if not rust_template_path.exists():
            raise FileNotFoundError(f"Rust template not found: {rust_template_path}")
        
        dockerfile_template_path = Path(self.paths['dockerfile_template'])
        if not dockerfile_template_path.exists():
            raise FileNotFoundError(f"Dockerfile template not found: {dockerfile_template_path}")


# Global settings instance
settings = Settings()