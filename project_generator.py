from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import re

class TemplateManager:
    """Generic template manager that auto-extracts variables and provides safe formatting."""
    
    def __init__(self):
        self.default_values = {
            'strategy_name': 'Generic Trading Strategy',
            'strategy_description': 'AI-generated cryptocurrency trading algorithm',
            'strategy_class_name': 'GenericStrategy',
            'imbalance_threshold': 0.6,
            'min_volume_threshold': 10.0,
            'lookback_periods': 5,
            'signal_cooldown_ms': 100,
            'project_name': 'generic-algo',
            'base_name': 'generic',
        }
    
    def extract_template_variables(self, template_str: str) -> set:
        """Extract all {variable} placeholders from template string."""
        return set(re.findall(r'\{(\w+)\}', template_str))
    
    def generate_missing_values(self, required_vars: set, provided_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate default values for missing template variables."""
        missing_vars = required_vars - set(provided_params.keys())
        generated = {}
        
        for var in missing_vars:
            if var in self.default_values:
                generated[var] = self.default_values[var]
            else:
                # Generate intelligent defaults based on variable name
                if 'threshold' in var.lower():
                    generated[var] = 0.5
                elif 'period' in var.lower() or 'lookback' in var.lower():
                    generated[var] = 5
                elif 'cooldown' in var.lower() or 'ms' in var.lower():
                    generated[var] = 100
                elif 'name' in var.lower():
                    generated[var] = f"Generated_{var.title()}"
                elif 'description' in var.lower():
                    generated[var] = f"Auto-generated {var.replace('_', ' ')}"
                else:
                    generated[var] = f"default_{var}"
        
        return generated
    
    def safe_format(self, template_str: str, params: Dict[str, Any]) -> str:
        """Safely format template with auto-generated defaults for missing variables."""
        try:
            # Extract required variables from template
            required_vars = self.extract_template_variables(template_str)
            
            # Generate missing values
            missing_values = self.generate_missing_values(required_vars, params)
            
            # Combine provided params with generated defaults
            all_params = {**missing_values, **params}  # params override defaults
            
            # Process string values to handle multiline content in comments
            processed_params = {}
            for key, value in all_params.items():
                if isinstance(value, str) and '\n' in value and 'description' in key.lower():
                    # Convert multiline descriptions to single line comments
                    lines = [line.strip() for line in value.split('\n') if line.strip()]
                    processed_params[key] = ' '.join(lines)
                else:
                    processed_params[key] = value
            
            # Format the template
            return template_str.format(**processed_params)
            
        except KeyError as e:
            raise ValueError(f"Template formatting failed - missing variable: {e}")
        except Exception as e:
            raise ValueError(f"Template formatting error: {str(e)}")

# Global template manager instance
template_manager = TemplateManager()

CARGO_TOML_TEMPLATE = '''[package]
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



def create_rust_project(project_name: str, strategy_params: Dict[str, Any]) -> str:
    """Creates a complete Rust project directory with all necessary files including Dockerfile."""
    
    project_dir = Path(f"generated_algorithms/{project_name}")
    src_dir = project_dir / "src"
    
    try:
        print(f"🔧 Creating project directory: {project_dir}")
        project_dir.mkdir(parents=True, exist_ok=True)
        src_dir.mkdir(exist_ok=True)
        print(f"✅ Directories created successfully")
        
        print(f"📖 Loading Rust template...")
        template = load_rust_template()
        if template is None:
            return "❌ Failed to load Rust template."
        
        print(f"🔧 Formatting template with parameters...")
        print(f"📋 Strategy params: {strategy_params}")
        
        try:
            rust_code = template_manager.safe_format(template, strategy_params)
            print(f"✅ Template formatted successfully")
        except ValueError as e:
            return f"❌ Template formatting error: {str(e)}"
        except Exception as e:
            return f"❌ Template formatting error: {str(e)}"
        
        print(f"📝 Writing main.rs...")
        main_rs_path = src_dir / "main.rs"
        with open(main_rs_path, 'w') as f:
            f.write(rust_code)
        print(f"✅ main.rs written to {main_rs_path}")
        
        print(f"📝 Writing Cargo.toml...")
        cargo_params = {**strategy_params, 'project_name': project_name}
        cargo_toml_content = template_manager.safe_format(CARGO_TOML_TEMPLATE, cargo_params)
        cargo_toml_path = project_dir / "Cargo.toml"
        with open(cargo_toml_path, 'w') as f:
            f.write(cargo_toml_content)
        print(f"✅ Cargo.toml written to {cargo_toml_path}")
        
        print(f"📝 Writing Dockerfile...")
        dockerfile_template = load_dockerfile_template()
        if dockerfile_template is None:
            return "❌ Failed to load Dockerfile template."
        
        try:
            dockerfile_content = template_manager.safe_format(dockerfile_template, strategy_params)
            dockerfile_path = project_dir / "Dockerfile"
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            print(f"✅ Dockerfile written to {dockerfile_path}")
        except ValueError as e:
            return f"❌ Dockerfile template formatting error: {str(e)}"
        except Exception as e:
            return f"❌ Dockerfile template formatting error: {str(e)}"
        
        print(f"📝 Writing .dockerignore...")
        dockerignore_content = """# Git
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
        dockerignore_path = project_dir / ".dockerignore"
        with open(dockerignore_path, 'w') as f:
            f.write(dockerignore_content)
        print(f"✅ .dockerignore written to {dockerignore_path}")
        
        print(f"📝 Writing README.md...")
        readme_content = f"""# {strategy_params['strategy_name']}

## Description
{strategy_params['strategy_description']}

## Configuration
- Imbalance Threshold: {strategy_params['imbalance_threshold']}
- Min Volume Threshold: {strategy_params['min_volume_threshold']}
- Lookback Periods: {strategy_params['lookback_periods']}
- Signal Cooldown: {strategy_params['signal_cooldown_ms']}ms

## Quick Start

### Local Development
```bash
# Build and run locally
cd {project_dir}
cargo build --release
cargo run
```

### Docker Deployment
```bash
# Build Docker image
docker build -t {strategy_params.get('base_name', 'crypto')}-algo:latest .

# Run container
docker run --rm {strategy_params.get('base_name', 'crypto')}-algo:latest

# Run with port mapping (if applicable)
docker run --rm -p 3000:3000 {strategy_params.get('base_name', 'crypto')}-algo:latest

# Run in development mode with shell access
docker run --rm -it {strategy_params.get('base_name', 'crypto')}-algo:latest /bin/sh
```

### Environment Variables
Customize the strategy with these environment variables:

```bash
export IMBALANCE_THRESHOLD={strategy_params['imbalance_threshold']}
export MIN_VOLUME_THRESHOLD={strategy_params['min_volume_threshold']}
export LOOKBACK_PERIODS={strategy_params['lookback_periods']}
export SIGNAL_COOLDOWN_MS={strategy_params['signal_cooldown_ms']}
export STREAMING_SOURCE_IP=127.0.0.1
export STREAMING_SOURCE_PORT=8888
```

## Docker Commands

### Build Commands
```bash
# Build image with latest tag
docker build -t {strategy_params.get('base_name', 'crypto')}-algo:latest .

# Build with custom tag
docker build -t {strategy_params.get('base_name', 'crypto')}-algo:v1.0.0 .

# Build with build args (if needed)
docker build --build-arg RUST_VERSION=1.75 -t {strategy_params.get('base_name', 'crypto')}-algo:latest .
```

### Run Commands
```bash
# Basic run
docker run --rm {strategy_params.get('base_name', 'crypto')}-algo:latest

# Run with environment variables
docker run --rm -e IMBALANCE_THRESHOLD=0.7 {strategy_params.get('base_name', 'crypto')}-algo:latest

# Run with volume mount for logs
docker run --rm -v $(pwd)/logs:/app/logs {strategy_params.get('base_name', 'crypto')}-algo:latest

# Run detached
docker run -d --name {strategy_params.get('base_name', 'crypto')}-strategy {strategy_params.get('base_name', 'crypto')}-algo:latest
```

### Management Commands
```bash
# View running containers
docker ps

# View logs
docker logs {strategy_params.get('base_name', 'crypto')}-strategy

# Stop container
docker stop {strategy_params.get('base_name', 'crypto')}-strategy

# Remove container
docker rm {strategy_params.get('base_name', 'crypto')}-strategy

# View image info
docker images {strategy_params.get('base_name', 'crypto')}-algo
```

## Generated Files
- `src/main.rs` - Main algorithm implementation
- `Cargo.toml` - Project dependencies and metadata
- `Dockerfile` - Multi-stage Docker build configuration
- `.dockerignore` - Docker build context exclusions
- `README.md` - This documentation

## Performance Notes
- The Docker image uses Alpine Linux for minimal size
- Multi-stage build optimizes final image size
- Runs as non-root user for security
- Includes health check for container monitoring

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        readme_path = project_dir / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        print(f"✅ README.md written to {readme_path}")
        
        print(f"📝 Writing .env.example...")
        env_example_content = f"""# Example environment variables for {strategy_params['strategy_name']}
# Copy this file to .env and customize the values

# Strategy Parameters
IMBALANCE_THRESHOLD={strategy_params['imbalance_threshold']}
MIN_VOLUME_THRESHOLD={strategy_params['min_volume_threshold']}
LOOKBACK_PERIODS={strategy_params['lookback_periods']}
SIGNAL_COOLDOWN_MS={strategy_params['signal_cooldown_ms']}

# Data Source Configuration
STREAMING_SOURCE_IP=127.0.0.1
STREAMING_SOURCE_PORT=8888

# Docker Configuration (optional)
DOCKER_IMAGE_NAME={strategy_params.get('base_name', 'crypto')}-algo
DOCKER_TAG=latest
"""
        
        env_example_path = project_dir / ".env.example"
        with open(env_example_path, 'w') as f:
            f.write(env_example_content)
        print(f"✅ .env.example written to {env_example_path}")
        
        print(f"🎉 Project creation completed successfully!")
        return str(project_dir.absolute())
        
    except Exception as e:
        error_msg = f"❌ Error creating project: {str(e)}"
        print(error_msg)
        return error_msg

def load_dockerfile_template(template_file: str = "dockerfile_template.dockerfile") -> Optional[str]:
    """Load the Dockerfile template from file."""
    try:
        print(f"🔍 Looking for Dockerfile template: {template_file}")
        template_path = Path(template_file)
        
        if not template_path.exists():
            print(f"❌ Dockerfile template '{template_file}' not found!")
            print(f"📂 Current working directory: {Path.cwd()}")
            print(f"📋 Files in current directory:")
            for file in Path.cwd().iterdir():
                if file.name.lower().startswith('dockerfile'):
                    print(f"   - {file.name} (Dockerfile related)")
                else:
                    print(f"   - {file.name}")
            return None
            
        print(f"✅ Dockerfile template found, reading contents...")
        with open(template_path, 'r') as f:
            content = f.read()
        
        print(f"✅ Dockerfile template loaded successfully ({len(content)} characters)")
        return content
        
    except FileNotFoundError:
        print(f"❌ Dockerfile template '{template_file}' not found!")
        print("Make sure dockerfile_template.dockerfile is in the same directory as the project files")
        return None
    except Exception as e:
        print(f"❌ Error reading Dockerfile template: {str(e)}")
        return None

def load_rust_template(template_file: str = "rust_template.rs") -> Optional[str]:
    """Load the Rust template from file."""
    try:
        print(f"🔍 Looking for template file: {template_file}")
        template_path = Path(template_file)
        
        if not template_path.exists():
            print(f"❌ Template file '{template_file}' not found!")
            print(f"📂 Current working directory: {Path.cwd()}")
            print(f"📋 Files in current directory:")
            for file in Path.cwd().iterdir():
                print(f"   - {file.name}")
            return None
            
        print(f"✅ Template file found, reading contents...")
        with open(template_path, 'r') as f:
            content = f.read()
        
        print(f"✅ Template loaded successfully ({len(content)} characters)")
        return content
        
    except FileNotFoundError:
        print(f"❌ Template file '{template_file}' not found!")
        print("Make sure rust_template.rs is in the same directory as agent.py")
        return None
    except Exception as e:
        print(f"❌ Error reading template file: {str(e)}")
        return None