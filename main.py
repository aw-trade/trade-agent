import sys
from finance_agent import FinanceAgent
from cli import CLI

def main():
    """Main entry point."""
    try:
        agent = FinanceAgent()
        cli = CLI(agent)
        cli.run_chat_cli()
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()