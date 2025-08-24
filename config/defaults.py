"""Default configuration values for the trading agent."""

from typing import Dict, Any

# Default strategy parameters
DEFAULT_STRATEGY_PARAMS = {
    'imbalance_threshold': 0.6,
    'min_volume_threshold': 10.0,
    'lookback_periods': 5,
    'signal_cooldown_ms': 100,
}

# Default template values
DEFAULT_TEMPLATE_VALUES = {
    'strategy_name': 'Generic Trading Strategy',
    'strategy_description': 'AI-generated cryptocurrency trading algorithm',
    'strategy_class_name': 'GenericStrategy',
    'project_name': 'generic-algo',
    'base_name': 'generic',
    **DEFAULT_STRATEGY_PARAMS
}

# API configuration
DEFAULT_API_CONFIG = {
    'host': '0.0.0.0',
    'port': 8004,
    'cors_origins': ['http://localhost:5173', 'http://localhost:3000'],
    'max_chat_history': 20,
}

# Docker configuration
DEFAULT_DOCKER_CONFIG = {
    'build_timeout': 300,  # 5 minutes
    'signal_output_port': 9999,
    'signal_output_bind_ip': '0.0.0.0',
}

# LangChain configuration
DEFAULT_LANGCHAIN_CONFIG = {
    'model': 'gemini-2.5-flash',
    'temperature': 0.1,
    'max_iterations': 5,
    'verbose': True,
}

# ChromaDB configuration
DEFAULT_CHROMADB_CONFIG = {
    'persist_directory': './algorithm_chromadb',
    'collection_name': 'trading_strategies',
    'embedding_model': 'all-MiniLM-L6-v2',
}

# File paths
DEFAULT_PATHS = {
    'generated_algorithms': 'generated_algorithms',
    'rust_template': 'rust_template.rs',
    'dockerfile_template': 'dockerfile_template.dockerfile',
    'chromadb_path': './algorithm_chromadb',
}