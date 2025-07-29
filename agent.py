import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_core.messages import ToolMessage

# RAG imports (add your existing RAG imports here)
# from langchain_chroma import Chroma
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.schema import Document
# Add any other RAG-related imports you were using

# --- Cargo.toml Template ---
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

# --- Project Creation Functions ---
def create_rust_project(project_name: str, strategy_params: Dict[str, Any]) -> str:
    """Creates a complete Rust project directory with all necessary files."""
    
    # Create project directory
    project_dir = Path(f"generated_algorithms/{project_name}")
    src_dir = project_dir / "src"
    
    try:
        print(f"🔧 Creating project directory: {project_dir}")
        # Create directories
        project_dir.mkdir(parents=True, exist_ok=True)
        src_dir.mkdir(exist_ok=True)
        print(f"✅ Directories created successfully")
        
        # Load and format the Rust template
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
        
        # Write main.rs
        print(f"📝 Writing main.rs...")
        main_rs_path = src_dir / "main.rs"
        with open(main_rs_path, 'w') as f:
            f.write(rust_code)
        print(f"✅ main.rs written to {main_rs_path}")
        
        # Write Cargo.toml
        print(f"📝 Writing Cargo.toml...")
        cargo_toml_content = CARGO_TOML_TEMPLATE.format(
            project_name=project_name,
            strategy_description=strategy_params['strategy_description']
        )
        cargo_toml_path = project_dir / "Cargo.toml"
        with open(cargo_toml_path, 'w') as f:
            f.write(cargo_toml_content)
        print(f"✅ Cargo.toml written to {cargo_toml_path}")
        
        # Write README.md
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
        
        # Write .env.example
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

# --- RAG Tools (add your existing RAG functionality here) ---

# Example RAG tool - replace with your actual RAG implementation
@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the knowledge base for relevant information about trading strategies,
    algorithms, or financial concepts.
    
    Args:
        query: The search query to find relevant information
    
    Use this tool when the user asks about:
    - Existing trading strategies
    - Financial concepts or definitions
    - Algorithm explanations
    - Market analysis techniques
    """
    # TODO: Replace this with your actual RAG implementation
    # This is a placeholder - you need to add your ChromaDB/vector store logic here
    
    print(f"\n[RAG TOOL CALL] Searching knowledge base for: {query}\n")
    
    # Example placeholder response
    return f"""Based on the knowledge base search for "{query}":

📚 Found relevant information about trading strategies and algorithms.
This is a placeholder response - please implement your actual RAG logic here.

To implement RAG:
1. Initialize your vector store (ChromaDB, etc.)
2. Search for relevant documents
3. Return the most relevant information
"""

# Add more RAG tools as needed
@tool 
def add_to_knowledge_base(content: str, topic: str) -> str:
    """
    Add new content to the knowledge base for future reference.
    
    Args:
        content: The content to add to the knowledge base
        topic: The topic/category for this content
    """
    print(f"\n[RAG TOOL CALL] Adding content to knowledge base under topic: {topic}\n")
    
    # TODO: Implement your document ingestion logic here
    return f"✅ Content added to knowledge base under topic: {topic}"

# --- Code Generation Tool ---
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
    
    # Create timestamp for unique naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create a clean project name (no spaces, lowercase)
    project_name = f"crypto_algo_{timestamp}"
    
    # Strategy parameters with all required template variables
    strategy_params = {
        'strategy_name': f'Custom Crypto Strategy {timestamp}',
        'strategy_description': algo_description,
        'strategy_class_name': f'CustomStrategy{timestamp[-6:]}',  # Use last 6 chars of timestamp
        'imbalance_threshold': 0.6,
        'min_volume_threshold': 10.0,
        'lookback_periods': 5,
        'signal_cooldown_ms': 100,
        'project_name': project_name,  # Add this for Cargo.toml
    }
    
    print(f"📋 Using strategy parameters: {strategy_params}")
    
    # Create the Rust project
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

class FinanceAgent:
    """LangChain-based Finance Agent with RAG and code generation capabilities."""
    
    def __init__(self):
        # Get API key from environment variable
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("Error: GOOGLE_API_KEY not found in .env file or environment variables.")
            sys.exit(1)
        
        # Initialize the LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.1
        )
        
        # Define tools - BOTH RAG and code generation
        self.tools = [
            generate_rust_crypto_algo,  # Code generation tool
            search_knowledge_base,      # RAG search tool
            add_to_knowledge_base,      # RAG ingestion tool
            # Add any other RAG tools you had before
        ]
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a finance and crypto trading expert AI assistant with access to both a knowledge base and code generation capabilities.

You have access to these tools:

1. **Code Generation**: Use generate_rust_crypto_algo when users ask to:
   - Generate a crypto algorithm
   - Create a trading strategy  
   - Build a crypto trading bot
   - Make a trading algorithm
   - Develop a crypto strategy

2. **Knowledge Base Search**: Use search_knowledge_base when users ask about:
   - Existing trading strategies
   - Financial concepts or definitions
   - Algorithm explanations
   - Market analysis techniques

3. **Knowledge Base Management**: Use add_to_knowledge_base to store new information

You can use multiple tools in a single conversation. For example:
- First search the knowledge base for relevant strategies
- Then generate code based on that information
- Or add new insights to the knowledge base after generating code

Always be helpful with general finance questions and use the appropriate tools based on the user's needs."""),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Create agent
        self.agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5  # Increased to allow for multiple tool calls
        )
        
        # Chat history
        self.chat_history: List[BaseMessage] = []
        
        # TODO: Initialize your RAG system here
        # self.initialize_rag_system()
    
    def initialize_rag_system(self):
        """Initialize the RAG system with your existing ChromaDB setup."""
        # TODO: Add your existing RAG initialization code here
        # Example:
        # self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        # self.vectorstore = Chroma(...)
        # etc.
        pass
    
    def display_chat_history(self):
        """Prints the current chat history."""
        print("\n--- Chat History ---")
        for message in self.chat_history:
            if isinstance(message, HumanMessage):
                print(f"You: {message.content}")
            elif isinstance(message, AIMessage):
                print(f"Agent: {message.content}")
        print("--------------------\n")
    
    def process_message(self, user_input: str) -> str:
        """Process a user message and return the agent's response."""
        try:
            # Invoke the agent
            response = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": self.chat_history
            })
            
            # Extract the output
            agent_response = response.get("output", "I couldn't generate a response.")
            
            # Update chat history
            self.chat_history.append(HumanMessage(content=user_input))
            self.chat_history.append(AIMessage(content=agent_response))
            
            # Keep history manageable (last 20 messages)
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]
            
            return agent_response
            
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return error_msg
    
    def run_chat_cli(self):
        """Runs the terminal-based chat interface."""
        print("Welcome to the LangChain Finance Agent CLI with RAG and Code Generation!")
        print("Type 'exit' to quit, 'history' to see chat history.")
        print("\n🤖 I can help you with:")
        print("  • Search knowledge base for trading strategies and concepts")
        print("  • Generate Rust crypto trading algorithms")
        print("  • Add new information to the knowledge base")
        print("  • General finance and crypto questions")
        print("\n💡 Try these commands:")
        print("  • 'search for momentum trading strategies'")
        print("  • 'generate a crypto algorithm for scalping'")
        print("  • 'what is RSI and how is it used in trading?'")
        print("  • 'create a trading strategy using moving averages'")

        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() == 'exit':
                    print("Goodbye!")
                    break
                elif user_input.lower() == 'history':
                    self.display_chat_history()
                    continue
                elif not user_input:
                    print("Please enter a message.")
                    continue

                # Process the message
                print("\nAgent: ", end="", flush=True)
                response = self.process_message(user_input)
                print(response)

            except KeyboardInterrupt:
                print("\nExiting chat. Goodbye!")
                break
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                print("Please try again.")

def main():
    """Main entry point."""
    try:
        agent = FinanceAgent()
        agent.run_chat_cli()
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()