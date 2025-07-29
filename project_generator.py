from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

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
ctrlc = "3.0"

[profile.release]
opt-level = 3
lto = true
'''

def create_rust_project(project_name: str, strategy_params: Dict[str, Any]) -> str:
    """Creates a complete Rust project directory with all necessary files."""
    
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
            rust_code = template.format(**strategy_params)
            print(f"✅ Template formatted successfully")
        except KeyError as e:
            return f"❌ Template formatting error - missing key: {e}"
        except Exception as e:
            return f"❌ Template formatting error: {str(e)}"
        
        print(f"📝 Writing main.rs...")
        main_rs_path = src_dir / "main.rs"
        with open(main_rs_path, 'w') as f:
            f.write(rust_code)
        print(f"✅ main.rs written to {main_rs_path}")
        
        print(f"📝 Writing Cargo.toml...")
        cargo_toml_content = CARGO_TOML_TEMPLATE.format(
            project_name=project_name,
            strategy_description=strategy_params['strategy_description']
        )
        cargo_toml_path = project_dir / "Cargo.toml"
        with open(cargo_toml_path, 'w') as f:
            f.write(cargo_toml_content)
        print(f"✅ Cargo.toml written to {cargo_toml_path}")
        
        print(f"📝 Writing README.md...")
        readme_content = f"""# {strategy_params['strategy_name']}

## Description
{strategy_params['strategy_description']}

## Configuration
- Imbalance Threshold: {strategy_params['imbalance_threshold']}
- Min Volume Threshold: {strategy_params['min_volume_threshold']}
- Lookback Periods: {strategy_params['lookback_periods']}
- Signal Cooldown: {strategy_params['signal_cooldown_ms']}ms

## Usage

### Build the project:
```bash
cd {project_dir}
cargo build --release
```

### Run the algorithm:
```bash
cargo run
```

### Environment Variables
You can customize the strategy by setting these environment variables:

```bash
export IMBALANCE_THRESHOLD={strategy_params['imbalance_threshold']}
export MIN_VOLUME_THRESHOLD={strategy_params['min_volume_threshold']}
export LOOKBACK_PERIODS={strategy_params['lookback_periods']}
export SIGNAL_COOLDOWN_MS={strategy_params['signal_cooldown_ms']}
export STREAMING_SOURCE_IP=127.0.0.1
export STREAMING_SOURCE_PORT=8888
```

## Generated Files
- `src/main.rs` - Main algorithm implementation
- `Cargo.toml` - Project dependencies and metadata
- `README.md` - This file

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