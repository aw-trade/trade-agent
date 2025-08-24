"""Project creation and management service."""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from config.settings import settings
from config.validation import (
    validate_strategy_params, validate_algorithm_description,
    validate_project_name, sanitize_trading_terms, sanitize_name_for_class,
    ValidationError
)
from templates.manager import template_manager
from templates.formatter import template_formatter
from templates.validators import template_validator, TemplateValidationError


class ProjectCreationError(Exception):
    """Exception raised when project creation fails."""
    pass


class ProjectService:
    """Service for creating and managing trading algorithm projects."""
    
    def __init__(self):
        self.generated_algorithms_path = Path(settings.paths['generated_algorithms'])
    
    def create_rust_project(self, algorithm_description: str, custom_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a complete Rust trading algorithm project."""
        try:
            # Validate input
            description = validate_algorithm_description(algorithm_description)
            
            # Generate project parameters
            project_params = self._generate_project_params(description, custom_params)
            
            # Validate project parameters
            validated_params = validate_strategy_params(project_params)
            project_params.update(validated_params)
            
            # Create project directory structure
            project_path = self._create_project_directory(project_params['project_name'])
            
            # Generate all project files
            self._generate_project_files(project_path, project_params)
            
            return {
                'success': True,
                'project_path': str(project_path.absolute()),
                'project_name': project_params['project_name'],
                'strategy_name': project_params['strategy_name'],
                'base_name': project_params['base_name'],
                'description': description,
                'parameters': project_params
            }
            
        except ValidationError as e:
            raise ProjectCreationError(f"Validation failed: {e}")
        except TemplateValidationError as e:
            raise ProjectCreationError(f"Template validation failed: {e}")
        except Exception as e:
            raise ProjectCreationError(f"Project creation failed: {e}")
    
    def _generate_project_params(self, description: str, custom_params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate project parameters from description and custom inputs."""
        # Extract trading terms for naming
        trading_terms = sanitize_trading_terms(description)
        base_name = '-'.join(trading_terms[:2]) if trading_terms else 'generic-algo'
        
        # Generate timestamp for unique naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = f"{base_name}_{timestamp}"
        
        # Base parameters
        params = {
            'strategy_description': description,
            'base_name': base_name,
            'project_name': project_name,
            'strategy_name': ' '.join(term.capitalize() for term in trading_terms) + ' Strategy' if trading_terms else 'Generic Trading Strategy',
            'strategy_class_name': sanitize_name_for_class(' '.join(trading_terms) if trading_terms else 'Generic'),
            **settings.strategy_params
        }
        
        # Override with custom parameters if provided
        if custom_params:
            params.update(custom_params)
        
        return params
    
    def _create_project_directory(self, project_name: str) -> Path:
        """Create the project directory structure."""
        project_path = self.generated_algorithms_path / project_name
        src_path = project_path / "src"
        
        try:
            # Create directories
            project_path.mkdir(parents=True, exist_ok=True)
            src_path.mkdir(exist_ok=True)
            
            return project_path
            
        except OSError as e:
            raise ProjectCreationError(f"Failed to create project directory: {e}")
    
    def _generate_project_files(self, project_path: Path, params: Dict[str, Any]) -> None:
        """Generate all project files."""
        files_to_create = [
            ('src/main.rs', self._generate_main_rs, params),
            ('Cargo.toml', self._generate_cargo_toml, params),
            ('Dockerfile', self._generate_dockerfile, params),
            ('.dockerignore', self._generate_dockerignore, params),
            ('README.md', self._generate_readme, params),
            ('.env.example', self._generate_env_example, params)
        ]
        
        for file_path, generator_func, file_params in files_to_create:
            full_path = project_path / file_path
            content = generator_func(file_params)
            
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except IOError as e:
                raise ProjectCreationError(f"Failed to write {file_path}: {e}")
    
    def _generate_main_rs(self, params: Dict[str, Any]) -> str:
        """Generate main.rs content."""
        try:
            template = template_manager.load_rust_template()
            
            # Validate template
            is_valid, issues = template_validator.validate_rust_template(template)
            if not is_valid:
                raise TemplateValidationError(f"Rust template validation failed: {'; '.join(issues)}")
            
            # Format template
            content = template_formatter.safe_format(template, params)
            
            # Validate generated code
            is_valid, issues = template_validator.validate_generated_rust_code(content)
            if not is_valid:
                raise TemplateValidationError(f"Generated Rust code validation failed: {'; '.join(issues)}")
            
            return content
            
        except Exception as e:
            raise ProjectCreationError(f"Failed to generate main.rs: {e}")
    
    def _generate_cargo_toml(self, params: Dict[str, Any]) -> str:
        """Generate Cargo.toml content."""
        try:
            template = template_manager.get_cargo_toml_template()
            
            # Validate template
            is_valid, issues = template_validator.validate_cargo_template(template)
            if not is_valid:
                raise TemplateValidationError(f"Cargo template validation failed: {'; '.join(issues)}")
            
            return template_formatter.safe_format(template, params)
            
        except Exception as e:
            raise ProjectCreationError(f"Failed to generate Cargo.toml: {e}")
    
    def _generate_dockerfile(self, params: Dict[str, Any]) -> str:
        """Generate Dockerfile content."""
        try:
            template = template_manager.load_dockerfile_template()
            
            # Validate template
            is_valid, issues = template_validator.validate_dockerfile_template(template)
            if not is_valid:
                # Log warnings but don't fail for Dockerfile validation
                print(f"Dockerfile template warnings: {'; '.join(issues)}")
            
            return template_formatter.safe_format(template, params)
            
        except Exception as e:
            raise ProjectCreationError(f"Failed to generate Dockerfile: {e}")
    
    def _generate_dockerignore(self, params: Dict[str, Any]) -> str:
        """Generate .dockerignore content."""
        return template_manager.get_dockerignore_template()
    
    def _generate_readme(self, params: Dict[str, Any]) -> str:
        """Generate README.md content."""
        return f"""# {params['strategy_name']}

## Description
{params['strategy_description']}

## Configuration
- Imbalance Threshold: {params['imbalance_threshold']}
- Min Volume Threshold: {params['min_volume_threshold']}
- Lookback Periods: {params['lookback_periods']}
- Signal Cooldown: {params['signal_cooldown_ms']}ms

## Quick Start

### Local Development
```bash
# Build and run locally
cargo build --release
cargo run
```

### Docker Deployment
```bash
# Build Docker image
docker build -t {params['base_name']}-algo:latest .

# Run container
docker run --rm {params['base_name']}-algo:latest

# Run with port mapping (if applicable)
docker run --rm -p 3000:3000 {params['base_name']}-algo:latest

# Run in development mode with shell access
docker run --rm -it {params['base_name']}-algo:latest /bin/sh
```

### Environment Variables
Customize the strategy with these environment variables:

```bash
export IMBALANCE_THRESHOLD={params['imbalance_threshold']}
export MIN_VOLUME_THRESHOLD={params['min_volume_threshold']}
export LOOKBACK_PERIODS={params['lookback_periods']}
export SIGNAL_COOLDOWN_MS={params['signal_cooldown_ms']}
export STREAMING_SOURCE_IP=127.0.0.1
export STREAMING_SOURCE_PORT=8888
```

## Generated Files
- `src/main.rs` - Main algorithm implementation
- `Cargo.toml` - Project dependencies and metadata
- `Dockerfile` - Multi-stage Docker build configuration
- `.dockerignore` - Docker build context exclusions
- `README.md` - This documentation
- `.env.example` - Environment configuration template

## Performance Notes
- The Docker image uses Alpine Linux for minimal size
- Multi-stage build optimizes final image size
- Runs as non-root user for security
- Includes health check for container monitoring

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    
    def _generate_env_example(self, params: Dict[str, Any]) -> str:
        """Generate .env.example content."""
        template = template_manager.get_env_example_template()
        return template_formatter.safe_format(template, params)
    
    def list_projects(self) -> Dict[str, Any]:
        """List all generated projects."""
        try:
            if not self.generated_algorithms_path.exists():
                return {'projects': [], 'count': 0}
            
            projects = []
            for project_dir in self.generated_algorithms_path.iterdir():
                if project_dir.is_dir():
                    projects.append({
                        'name': project_dir.name,
                        'path': str(project_dir.absolute()),
                        'created': datetime.fromtimestamp(project_dir.stat().st_ctime).isoformat(),
                        'has_cargo': (project_dir / 'Cargo.toml').exists(),
                        'has_dockerfile': (project_dir / 'Dockerfile').exists(),
                        'has_readme': (project_dir / 'README.md').exists()
                    })
            
            # Sort by creation time, newest first
            projects.sort(key=lambda x: x['created'], reverse=True)
            
            return {
                'projects': projects,
                'count': len(projects)
            }
            
        except Exception as e:
            raise ProjectCreationError(f"Failed to list projects: {e}")
    
    def get_project_info(self, project_name: str) -> Dict[str, Any]:
        """Get information about a specific project."""
        try:
            project_path = self.generated_algorithms_path / project_name
            
            if not project_path.exists():
                raise ProjectCreationError(f"Project not found: {project_name}")
            
            info = {
                'name': project_name,
                'path': str(project_path.absolute()),
                'exists': True,
                'files': {}
            }
            
            # Check for important files
            important_files = ['src/main.rs', 'Cargo.toml', 'Dockerfile', 'README.md', '.env.example']
            for file_name in important_files:
                file_path = project_path / file_name
                info['files'][file_name] = {
                    'exists': file_path.exists(),
                    'size': file_path.stat().st_size if file_path.exists() else 0,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat() if file_path.exists() else None
                }
            
            return info
            
        except Exception as e:
            raise ProjectCreationError(f"Failed to get project info: {e}")


# Global project service instance
project_service = ProjectService()