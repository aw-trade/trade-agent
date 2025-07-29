from finance_agent import FinanceAgent

class CLI:
    """Command line interface for the Finance Agent."""
    
    def __init__(self, agent: FinanceAgent):
        self.agent = agent
    
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
                    self.agent.display_chat_history()
                    continue
                elif not user_input:
                    print("Please enter a message.")
                    continue

                print("\nAgent: ", end="", flush=True)
                response = self.agent.process_message(user_input)
                print(response)

            except KeyboardInterrupt:
                print("\nExiting chat. Goodbye!")
                break
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                print("Please try again.")