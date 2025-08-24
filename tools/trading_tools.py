from langchain.tools import tool

from services.project_service import project_service, ProjectCreationError
from services.docker_service import docker_service, DockerError
from config.validation import validate_docker_name, sanitize_trading_terms

def sanitize_name(name: str) -> str:
    """Convert a strategy description into a valid Docker image name."""
    # Use the trading terms extraction from validation module
    trading_terms = sanitize_trading_terms(name)
    
    if trading_terms:
        base_name = '-'.join(trading_terms[:2])  # Use up to 2 terms
    else:
        base_name = 'crypto-algo'
    
    # Validate and return clean Docker name
    return validate_docker_name(base_name)

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
    try:
        print(f"\n[TOOL CALL] Generating Rust project with description:\n{algo_description}\n")
        
        # Create project using the project service
        project_result = project_service.create_rust_project(algo_description)
        
        if not project_result['success']:
            return f"❌ Failed to create project: {project_result.get('error', 'Unknown error')}"
        
        project_path = project_result['project_path']
        base_name = project_result['base_name']
        strategy_name = project_result['strategy_name']
        parameters = project_result['parameters']
        
        # Format success message
        result = f"""✅ Successfully created Rust trading algorithm project!

📁 Project Location: {project_path}
🎯 Strategy Name: {strategy_name}
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
  - Imbalance Threshold: {parameters['imbalance_threshold']}
  - Min Volume Threshold: {parameters['min_volume_threshold']}
  - Lookback Periods: {parameters['lookback_periods']}
  - Signal Cooldown: {parameters['signal_cooldown_ms']}ms"""
        
        # Build Docker image if requested
        if build_docker:
            try:
                print(f"\n🐳 Building Docker image...")
                image_name = f"{base_name}-algo"
                docker_result = docker_service.build_image(project_path, image_name)
                
                if docker_result['success']:
                    result += f"""\n\n🐳 Docker Build Successful!
  
📦 Image Details:
  - Name: {docker_result['image_name']}:latest
  - Size: {docker_result['size']}
  - Build Duration: {docker_result['build_duration']:.1f}s

🚀 Run Commands:
  docker run --rm {docker_result['image_name']}:latest
  docker run --rm -p 3000:3000 {docker_result['image_name']}:latest
  
🔧 Development Mode:
  docker run --rm -it {docker_result['image_name']}:latest /bin/sh"""
                else:
                    result += f"\n\n❌ Docker Build Failed: {docker_result.get('error', 'Unknown error')}"
                    
            except DockerError as e:
                result += f"\n\n❌ Docker Build Error: {e}"
        else:
            result += f"\n\n🐳 Docker Build:\n  cd {project_path}\n  docker build -t {base_name}-algo:latest ."
        
        result += "\n\nNext: Customize the .env file and run your algorithm!"
        return result
        
    except ProjectCreationError as e:
        return f"❌ Project creation failed: {e}"
    except Exception as e:
        return f"❌ Unexpected error: {e}"


@tool
def build_docker_image_only(project_path: str, custom_name: str = "") -> str:
    """
    Build a Docker image for an existing Rust project.
    
    Args:
        project_path: Path to the Rust project directory
        custom_name: Optional custom name for the Docker image
    """
    try:
        # Determine image name
        if custom_name:
            image_name = validate_docker_name(custom_name)
        else:
            from pathlib import Path
            project_dir = Path(project_path)
            image_name = validate_docker_name(project_dir.name)
        
        # Add '-algo' suffix if not present
        if not image_name.endswith('-algo'):
            image_name += '-algo'
        
        # Build using docker service
        docker_result = docker_service.build_image(project_path, image_name)
        
        if docker_result['success']:
            return f"""🐳 Docker Build Successful!
  
📦 Image Details:
  - Name: {docker_result['image_name']}:latest
  - Size: {docker_result['size']}
  - Build Duration: {docker_result['build_duration']:.1f}s

🚀 Run Commands:
  docker run --rm {docker_result['image_name']}:latest
  docker run --rm -p 3000:3000 {docker_result['image_name']}:latest
  
🔧 Development Mode:
  docker run --rm -it {docker_result['image_name']}:latest /bin/sh
  
💡 Management Commands:
  docker ps
  docker logs <container_name>
  docker images {docker_result['image_name']}"""
        else:
            return f"""❌ Docker Build Failed!
  
Error: {docker_result.get('error', 'Unknown error')}

💡 Troubleshooting:
  - Ensure Docker is running
  - Check Dockerfile syntax
  - Verify project path exists: {project_path}
  - Check Docker daemon status"""
    
    except DockerError as e:
        return f"❌ Docker service error: {e}"
    except Exception as e:
        return f"❌ Error building Docker image: {str(e)}"