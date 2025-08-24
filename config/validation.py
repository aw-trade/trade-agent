"""Input validation functions for the trading agent."""

import re
from typing import Dict, Any, List, Optional
from pathlib import Path


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_strategy_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate strategy parameters."""
    validated = {}
    
    # Imbalance threshold (0.0 to 1.0)
    threshold = params.get('imbalance_threshold', 0.6)
    if not isinstance(threshold, (int, float)) or not 0.0 <= threshold <= 1.0:
        raise ValidationError("imbalance_threshold must be a number between 0.0 and 1.0")
    validated['imbalance_threshold'] = float(threshold)
    
    # Min volume threshold (positive number)
    volume = params.get('min_volume_threshold', 10.0)
    if not isinstance(volume, (int, float)) or volume < 0:
        raise ValidationError("min_volume_threshold must be a positive number")
    validated['min_volume_threshold'] = float(volume)
    
    # Lookback periods (positive integer)
    lookback = params.get('lookback_periods', 5)
    if not isinstance(lookback, int) or lookback < 1:
        raise ValidationError("lookback_periods must be a positive integer")
    validated['lookback_periods'] = lookback
    
    # Signal cooldown (positive integer)
    cooldown = params.get('signal_cooldown_ms', 100)
    if not isinstance(cooldown, int) or cooldown < 0:
        raise ValidationError("signal_cooldown_ms must be a non-negative integer")
    validated['signal_cooldown_ms'] = cooldown
    
    return validated


def validate_project_name(name: str) -> str:
    """Validate and sanitize project name."""
    if not name or not isinstance(name, str):
        raise ValidationError("Project name must be a non-empty string")
    
    # Remove invalid characters and convert to lowercase
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', name.strip().lower())
    
    if not sanitized:
        raise ValidationError("Project name contains no valid characters")
    
    if len(sanitized) > 50:
        sanitized = sanitized[:50]
    
    # Ensure it doesn't start with a number or hyphen
    if sanitized[0].isdigit() or sanitized[0] == '-':
        sanitized = 'algo_' + sanitized
    
    return sanitized


def validate_docker_name(name: str) -> str:
    """Validate and sanitize Docker image name."""
    if not name or not isinstance(name, str):
        raise ValidationError("Docker name must be a non-empty string")
    
    # Docker image names must be lowercase and follow specific rules
    sanitized = re.sub(r'[^a-z0-9_.-]', '', name.strip().lower())
    
    if not sanitized:
        raise ValidationError("Docker name contains no valid characters")
    
    # Remove leading/trailing separators
    sanitized = sanitized.strip('.-_')
    
    if not sanitized:
        raise ValidationError("Docker name is empty after sanitization")
    
    # Ensure it starts with alphanumeric
    if not sanitized[0].isalnum():
        sanitized = 'algo-' + sanitized
    
    return sanitized[:50]  # Docker names should be reasonable length


def validate_algorithm_description(description: str) -> str:
    """Validate algorithm description."""
    if not description or not isinstance(description, str):
        raise ValidationError("Algorithm description must be a non-empty string")
    
    description = description.strip()
    
    if len(description) < 10:
        raise ValidationError("Algorithm description must be at least 10 characters long")
    
    if len(description) > 1000:
        raise ValidationError("Algorithm description must be less than 1000 characters")
    
    return description


def validate_template_params(params: Dict[str, Any], required_vars: set) -> Dict[str, Any]:
    """Validate template parameters against required variables."""
    validated = {}
    
    for var in required_vars:
        if var in params:
            value = params[var]
            # Convert to string for template formatting
            validated[var] = str(value) if value is not None else ""
        else:
            # Will be filled by template manager defaults
            pass
    
    return validated


def validate_file_path(path: str, must_exist: bool = True) -> Path:
    """Validate file path."""
    if not path or not isinstance(path, str):
        raise ValidationError("File path must be a non-empty string")
    
    path_obj = Path(path)
    
    if must_exist and not path_obj.exists():
        raise ValidationError(f"File does not exist: {path}")
    
    return path_obj


def validate_port(port: int) -> int:
    """Validate port number."""
    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValidationError("Port must be an integer between 1 and 65535")
    
    return port


def validate_host(host: str) -> str:
    """Validate host address."""
    if not host or not isinstance(host, str):
        raise ValidationError("Host must be a non-empty string")
    
    host = host.strip()
    
    # Basic validation - could be enhanced with more sophisticated IP/hostname validation
    if not re.match(r'^[a-zA-Z0-9.-]+$', host):
        raise ValidationError("Host contains invalid characters")
    
    return host


def sanitize_name_for_class(name: str) -> str:
    """Sanitize a name for use as a class name."""
    if not name or not isinstance(name, str):
        return "GenericStrategy"
    
    # Remove non-alphanumeric characters and convert to title case
    words = re.findall(r'[a-zA-Z0-9]+', name)
    if not words:
        return "GenericStrategy"
    
    class_name = ''.join(word.capitalize() for word in words)
    
    # Ensure it starts with a letter
    if not class_name[0].isalpha():
        class_name = 'Strategy' + class_name
    
    return class_name + 'Strategy' if not class_name.endswith('Strategy') else class_name


def sanitize_trading_terms(description: str) -> List[str]:
    """Extract and sanitize trading terms from description."""
    trading_terms = [
        'rsi', 'macd', 'ema', 'sma', 'bollinger', 'momentum', 'scalping',
        'arbitrage', 'grid', 'dca', 'swing', 'day', 'trend', 'reversal',
        'breakout', 'support', 'resistance', 'volume', 'volatility', 'stochastic',
        'fibonacci', 'pivot', 'moving', 'average', 'crossover', 'divergence'
    ]
    
    description_lower = description.lower()
    found_terms = []
    
    for term in trading_terms:
        if term in description_lower:
            found_terms.append(term)
    
    return found_terms[:3]  # Limit to 3 most relevant terms