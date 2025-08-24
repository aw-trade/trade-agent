import sys
import argparse

from agents.finance_agent import FinanceAgent, FinanceAgentError
from cli.interface import CLI

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Trade Agent - Finance AI Assistant")
    parser.add_argument(
        "--mode", 
        choices=["cli", "api"], 
        default="cli",
        help="Run mode: 'cli' for command line interface or 'api' for FastAPI server"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="API server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8004,
        help="API server port (default: 8004)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "api":
        try:
            from api.endpoints import run_api_server
            print(f"🚀 Starting Trade Agent API v2.0 server on {args.host}:{args.port}")
            run_api_server(host=args.host, port=args.port)
        except ImportError as e:
            print(f"❌ Error: Missing dependencies for API mode: {e}")
            print("💡 Install with: pip install fastapi uvicorn")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to start API server: {e}")
            sys.exit(1)
    else:
        try:
            print("🤖 Initializing Trade Agent v2.0...")
            agent = FinanceAgent()
            cli = CLI(agent)
            cli.run_chat_cli()
        except FinanceAgentError as e:
            print(f"❌ Agent initialization failed: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print("💡 Check your configuration and try again")
            sys.exit(1)

if __name__ == "__main__":
    main()