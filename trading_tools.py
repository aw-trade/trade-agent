from datetime import datetime
from langchain.tools import tool
from project_generator import create_rust_project

@tool
def generate_rust_crypto_algo(algo_description: str) -> str:
    """
    Generates a new Rust crypto trading algorithm based on the user's description.
    
    Args:
        algo_description: Description of the trading algorithm including strategy logic,
                         indicators (RSI, moving averages, volume, etc.), entry/exit conditions,
                         and any specific parameters.
    
    Use this tool when the user asks to:
    - Generate a crypto algorithm
    - Create a trading strategy
    - Build a crypto trading bot
    - Make a trading algorithm
    - Develop a crypto strategy
    """
    print(f"\n[TOOL CALL] Generating Rust project with description:\n{algo_description}\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    project_name = f"crypto_algo_{timestamp}"
    
    strategy_params = {
        'strategy_name': f'Custom Crypto Strategy {timestamp}',
        'strategy_description': algo_description,
        'strategy_class_name': f'CustomStrategy{timestamp[-6:]}',
        'imbalance_threshold': 0.6,
        'min_volume_threshold': 10.0,
        'lookback_periods': 5,
        'signal_cooldown_ms': 100,
        'project_name': project_name,
    }
    
    print(f"📋 Using strategy parameters: {strategy_params}")
    
    project_path = create_rust_project(project_name, strategy_params)
    
    if project_path.startswith("❌"):
        return project_path
    
    return f"""✅ Successfully created Rust trading algorithm project!

📁 Project Location: {project_path}
🎯 Strategy Name: {strategy_params['strategy_name']}
📝 Description: {algo_description}

📂 Generated Files:
  ├── src/main.rs         # Main algorithm implementation
  ├── Cargo.toml          # Project dependencies
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
  - Signal Cooldown: {strategy_params['signal_cooldown_ms']}ms

Next: Customize the .env file and run your algorithm!"""