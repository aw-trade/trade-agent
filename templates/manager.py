"""Template loading and management functionality."""

import re
from pathlib import Path
from typing import Dict, Any, Set, Optional

from config.settings import settings
from config.validation import ValidationError


class TemplateLoadError(Exception):
    """Exception raised when template loading fails."""
    pass


class TemplateManager:
    """Manages loading and caching of templates."""
    
    def __init__(self):
        self._template_cache: Dict[str, str] = {}
    
    def load_rust_template(self, template_path: Optional[str] = None) -> str:
        """Load the Rust template from file."""
        if template_path is None:
            template_path = settings.paths['rust_template']
        
        cache_key = f"rust_template:{template_path}"
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]
        
        try:
            path_obj = Path(template_path)
            
            if not path_obj.exists():
                raise TemplateLoadError(f"Rust template not found: {template_path}")
            
            with open(path_obj, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                raise TemplateLoadError(f"Rust template is empty: {template_path}")
            
            self._template_cache[cache_key] = content
            return content
            
        except IOError as e:
            raise TemplateLoadError(f"Failed to read Rust template: {e}")
    
    def load_dockerfile_template(self, template_path: Optional[str] = None) -> str:
        """Load the Dockerfile template from file."""
        if template_path is None:
            template_path = settings.paths['dockerfile_template']
        
        cache_key = f"dockerfile_template:{template_path}"
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]
        
        try:
            path_obj = Path(template_path)
            
            if not path_obj.exists():
                raise TemplateLoadError(f"Dockerfile template not found: {template_path}")
            
            with open(path_obj, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                raise TemplateLoadError(f"Dockerfile template is empty: {template_path}")
            
            self._template_cache[cache_key] = content
            return content
            
        except IOError as e:
            raise TemplateLoadError(f"Failed to read Dockerfile template: {e}")
    
    def extract_template_variables(self, template_str: str) -> Set[str]:
        """Extract all {variable} placeholders from template string."""
        return set(re.findall(r'\{(\w+)\}', template_str))
    
    def clear_cache(self) -> None:
        """Clear the template cache."""
        self._template_cache.clear()
    
    def get_cargo_toml_template(self) -> str:
        """Get the Cargo.toml template."""
        return '''[package]
name = "{project_name}"
version = "0.1.0"
edition = "2021"
description = "{strategy_description}"
authors = ["AI Agent <agent@example.com>"]

[dependencies]
serde = {{ version = "1.0", features = ["derive"] }}
serde_json = "1.0"
crossbeam-channel = "0.5"
ctrlc = "3.4"
tokio = {{ version = "1.0", features = ["full"] }}

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
panic = "abort"
'''
    
    def get_dockerignore_template(self) -> str:
        """Get the .dockerignore template."""
        return """# Git
.git/
.gitignore

# Rust
target/
Cargo.lock

# Development
.env
.env.local
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Documentation
*.md
!README.md
"""
    
    def get_env_example_template(self) -> str:
        """Get the .env.example template."""
        return """# Example environment variables for {strategy_name}
# Copy this file to .env and customize the values

# Strategy Parameters
IMBALANCE_THRESHOLD={imbalance_threshold}
MIN_VOLUME_THRESHOLD={min_volume_threshold}
LOOKBACK_PERIODS={lookback_periods}
SIGNAL_COOLDOWN_MS={signal_cooldown_ms}

# Data Source Configuration
STREAMING_SOURCE_IP=127.0.0.1
STREAMING_SOURCE_PORT=8888

# Docker Configuration (optional)
DOCKER_IMAGE_NAME={base_name}-algo
DOCKER_TAG=latest
"""


# Global template manager instance
template_manager = TemplateManager()