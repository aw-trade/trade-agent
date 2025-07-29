from datetime import datetime
from langchain.tools import tool
from project_generator import create_rust_project
import subprocess
import re

def sanitize_name(name: str) -> str:
    """Convert a strategy description into a valid Docker image name."""
    # Extract key trading terms and convert to lowercase
    trading_terms = ['rsi', 'macd', 'ema', 'sma', 'bollinger', 'momentum', 'scalping', 
                    'arbitrage', 'grid', 'dca', 'swing', 'day', 'trend', 'reversal',
                    'breakout', 'support', 'resistance', 'volume', 'volatility']
    
    # Convert to lowercase and extract alphanumeric words
    words = re.findall(r'\b\w+\b', name.lower())
    
    # Prioritize trading terms, then take other meaningful words
    key_words = []
    for term in trading_terms:
        if term in words:
            key_words.append(term)
    
    # Add other meaningful words (avoid common words)
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'using', 'based', 'strategy', 'algorithm', 'trading', 'crypto'}
    for word in words[:5]:  # Limit to first 5 words to avoid overly long names
        if word not in common_words and word not in key_words and len(word) > 2:
            key_words.append(word)
    
    # If no meaningful words found, use generic terms
    if not key_words:
        key_words = ['crypto', 'algo']
    
    # Join with hyphens and ensure valid Docker name format
    name = '-'.join(key_words[:3])  # Limit to 3 key words
    
    # Ensure it starts with alphanumeric and contains only valid characters
    name = re.sub(r'[^a-z0-9\-]', '', name)
    if not name or not name[0].isalnum():
        name = 'crypto-' + name
    
    return name[:50]  # Docker image names should be reasonable length

@tool
def generate_rust_crypto_algo(algo_description: str, build_docker: bool = False) -> str:
    """
    Generates a new Rust crypto trading algorithm based on the user's description.
    Optionally builds a Docker image.
    
    Args:
        algo_description: Description of the trading algorithm including strategy logic,
                         indicators (RSI, moving averages, volume, etc.), entry/exit conditions,
                         and any specific parameters.
        build_docker: Whether to build a Docker image after creating the project.
    
    Use this tool when the user asks to:
    - Generate a crypto algorithm
    - Create a trading strategy
    - Build a crypto trading bot
    - Make a trading algorithm
    - Develop a crypto strategy
    - Build/create Docker image for algorithm
    """
    print(f"\n[TOOL CALL] Generating Rust project with description:\n{algo_description}\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create meaningful project and image names
    base_name = sanitize_name(algo_description)
    project_name = f"{base_name}_{timestamp}"
    
    strategy_params = {
        'strategy_name': f'{base_name.replace("-", " ").title()} Strategy',
        'strategy_description': algo_description,
        'strategy_class_name': f'{"".join(word.capitalize() for word in base_name.split("-"))}Strategy',
        'imbalance_threshold': 0.6,
        'min_volume_threshold': 10.0,
        'lookback_periods': 5,
        'signal_cooldown_ms': 100,
        'project_name': project_name,
        'base_name': base_name,
    }
    
    print(f"📋 Using strategy parameters: {strategy_params}")
    
    project_path = create_rust_project(project_name, strategy_params)
    
    if project_path.startswith("❌"):
        return project_path
    
    result = f"""✅ Successfully created Rust trading algorithm project!

📁 Project Location: {project_path}
🎯 Strategy Name: {strategy_params['strategy_name']}
📝 Description: {algo_description}

📂 Generated Files:
  ├── src/main.rs         # Main algorithm implementation
  ├── Cargo.toml          # Project dependencies
  ├── Dockerfile          # Docker configuration
  ├── README.md           # Documentation
  └── .env.example        # Environment configuration

🚀 Quick Start:
  cd {project_path}
  cargo build --release
  cargo run

🔧 Configuration:
  - Imbalance Threshold: {strategy_params['imbalance_threshold']}
  - Min Volume Threshold: {strategy_params['min_volume_threshold']}
  - Lookback Periods: {strategy_params['lookback_periods']}
  - Signal Cooldown: {strategy_params['signal_cooldown_ms']}ms"""

    # Build Docker image if requested
    if build_docker:
        print(f"\n🐳 Building Docker image...")
        docker_result = build_docker_image(project_path, base_name, timestamp)
        result += f"\n\n{docker_result}"
    else:
        result += f"\n\n🐳 Docker Build:\n  cd {project_path}\n  docker build -t {base_name}-algo:latest ."

    result += "\n\nNext: Customize the .env file and run your algorithm!"
    return result

def build_docker_image(project_path: str, base_name: str, timestamp: str) -> str:
    """Build Docker image for the generated project."""
    try:
        image_name = f"{base_name}-algo"
        image_tag = f"{image_name}:latest"
        versioned_tag = f"{image_name}:{timestamp}"
        
        print(f"🔨 Building Docker image: {image_tag}")
        
        # Build the Docker image
        build_cmd = [
            "docker", "build", 
            "-t", image_tag,
            "-t", versioned_tag,
            "."
        ]
        
        result = subprocess.run(
            build_cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            # Get image size
            size_cmd = ["docker", "images", image_name, "--format", "table {{.Size}}"]
            size_result = subprocess.run(size_cmd, capture_output=True, text=True)
            size = "Unknown"
            if size_result.returncode == 0:
                lines = size_result.stdout.strip().split('\n')
                if len(lines) > 1:
                    size = lines[1]
            
            return f"""🐳 Docker Build Successful!
  
📦 Image Details:
  - Name: {image_tag}
  - Version: {versioned_tag}
  - Size: {size}

🚀 Run Commands:
  docker run --rm {image_tag}
  docker run --rm -p 3000:3000 {image_tag}
  
🔧 Development Mode:
  docker run --rm -it {image_tag} /bin/sh"""
        
        else:
            error_output = result.stderr or result.stdout
            return f"""❌ Docker Build Failed!
  
Error Output:
{error_output}

💡 Troubleshooting:
  - Ensure Docker is running
  - Check Dockerfile syntax
  - Verify all dependencies are available"""
    
    except subprocess.TimeoutExpired:
        return "❌ Docker build timed out after 5 minutes"
    except FileNotFoundError:
        return "❌ Docker not found. Please install Docker first."
    except Exception as e:
        return f"❌ Docker build error: {str(e)}"

@tool
def build_docker_image_only(project_path: str, custom_name: str = "") -> str:
    """
    Build a Docker image for an existing Rust project.
    
    Args:
        project_path: Path to the Rust project directory
        custom_name: Optional custom name for the Docker image
    """
    try:
        from pathlib import Path
        
        project_dir = Path(project_path)
        if not project_dir.exists():
            return f"❌ Project directory not found: {project_path}"
        
        dockerfile_path = project_dir / "Dockerfile"
        if not dockerfile_path.exists():
            return f"❌ Dockerfile not found in: {project_path}"
        
        # Determine image name
        if custom_name:
            base_name = sanitize_name(custom_name)
        else:
            # Try to extract name from project directory
            base_name = sanitize_name(project_dir.name)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return build_docker_image(str(project_dir), base_name, timestamp)
    
    except Exception as e:
        return f"❌ Error building Docker image: {str(e)}"