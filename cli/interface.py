"""Enhanced CLI interface for the Finance Agent."""

from typing import List, Dict, Any

from agents.finance_agent import FinanceAgent, FinanceAgentError
from services.rag_service import rag_service
from services.docker_service import docker_service
from services.project_service import project_service


class CLI:
    """Enhanced command line interface for the Finance Agent."""
    
    def __init__(self, agent: FinanceAgent):
        self.agent = agent
    
    def run_chat_cli(self):
        """Run the terminal-based chat interface with enhanced features."""
        print('''🚀 Welcome to Trade Agent v2.0 CLI!
        
🤖 Enhanced AI Assistant Features:
  • Advanced Rust algorithm generation with automatic containerization
  • Intelligent knowledge base with semantic search
  • Project management and Docker integration
  • Real-time strategy research and pattern matching
  
💬 Commands:
  • Type your message to chat with the AI
  • 'exit' or 'quit' - Exit the application
  • 'history' - Show chat history
  • 'clear' - Clear chat history
  • 'stats' - Show system statistics
  • 'health' - System health check
  • 'routing' - Show routing system status
  • 'routing toggle' - Enable/disable intelligent routing
  • 'help' - Show this help message
''')
        
        self._show_system_status()
        
        while True:
            try:
                user_input = input("\\n💬 You: ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    print("👋 Goodbye! Happy trading!")
                    break
                elif user_input.lower() == 'history':
                    self.agent.display_chat_history()
                    continue
                elif user_input.lower() == 'clear':
                    self.agent.clear_history()
                    print("✅ Chat history cleared")
                    continue
                elif user_input.lower() == 'stats':
                    self._show_statistics()
                    continue
                elif user_input.lower() == 'health':
                    self._show_health_check()
                    continue
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif user_input.lower() == 'routing':
                    self._show_routing_info()
                    continue
                elif user_input.lower().startswith('routing '):
                    self._handle_routing_command(user_input[8:].strip())
                    continue
                elif not user_input:
                    print("Please enter a message or command.")
                    continue

                print("\\n🤖 Agent: ", end="", flush=True)
                response = self.agent.process_message(user_input)
                print(response)

            except KeyboardInterrupt:
                print("\\n\\n👋 Exiting chat. Goodbye!")
                break
            except Exception as e:
                print(f"\\n❌ An unexpected error occurred: {e}")
                print("Please try again or type 'help' for assistance.")
    
    def _show_system_status(self):
        """Show initial system status."""
        print("\\n📊 System Status:")
        
        # Agent status
        agent_stats = self.agent.get_agent_stats()
        print(f"  🤖 Agent: ✅ Ready ({agent_stats['available_tools']} tools available)")
        
        # RAG service status
        if rag_service:
            try:
                stats = rag_service.get_collection_stats()
                print(f"  📚 Knowledge Base: ✅ Ready ({stats['total_documents']} documents)")
            except Exception:
                print("  📚 Knowledge Base: ⚠️  Available but may have issues")
        else:
            print("  📚 Knowledge Base: ❌ Not available (ChromaDB not installed)")
        
        # Docker status
        if docker_service.is_docker_available():
            print("  🐳 Docker: ✅ Available")
        else:
            print("  🐳 Docker: ❌ Not available")
        
        # Project service
        try:
            project_stats = project_service.list_projects()
            print(f"  📁 Projects: ✅ Ready ({project_stats['count']} existing projects)")
        except Exception:
            print("  📁 Projects: ⚠️  Service available but may have issues")
    
    def _show_statistics(self):
        """Show detailed system statistics."""
        print("\\n📊 Detailed System Statistics:\\n")
        
        # Agent statistics
        agent_stats = self.agent.get_agent_stats()
        print("🤖 Agent Statistics:")
        print(f"  • Model: {agent_stats['llm_model']}")
        print(f"  • Chat History: {agent_stats['chat_history_length']}/{agent_stats['max_chat_history']} messages")
        print(f"  • Available Tools: {agent_stats['available_tools']}")
        print(f"  • Tool Names: {', '.join(agent_stats['tool_names'])}")
        print(f"  • Intelligent Routing: {'✅ Enabled' if agent_stats.get('routing_enabled', False) else '❌ Disabled'}")
        
        # RAG statistics
        if rag_service:
            try:
                rag_stats = rag_service.get_collection_stats()
                print("\\n📚 Knowledge Base Statistics:")
                print(f"  • Total Documents: {rag_stats['total_documents']}")
                print(f"  • Total Content: {rag_stats['total_content_length']:,} characters")
                print(f"  • Average Length: {rag_stats['average_content_length']:.1f} chars/doc")
                if rag_stats['topics']:
                    print("  • Topics:")
                    for topic, count in sorted(rag_stats['topics'].items(), key=lambda x: x[1], reverse=True):
                        print(f"    - {topic}: {count} documents")
            except Exception as e:
                print(f"\\n📚 Knowledge Base: ❌ Error getting stats: {e}")
        else:
            print("\\n📚 Knowledge Base: ❌ Not available")
        
        # Project statistics
        try:
            project_stats = project_service.list_projects()
            print("\\n📁 Project Statistics:")
            print(f"  • Total Projects: {project_stats['count']}")
            if project_stats['projects']:
                print("  • Recent Projects:")
                for project in project_stats['projects'][:5]:  # Show first 5
                    print(f"    - {project['name']} (created: {project['created'][:10]})")
        except Exception as e:
            print(f"\\n📁 Projects: ❌ Error getting stats: {e}")
        
        # Docker statistics
        if docker_service.is_docker_available():
            try:
                images = docker_service.list_images()
                algo_images = [img for img in images if 'algo' in img['repository'].lower()]
                print("\\n🐳 Docker Statistics:")
                print(f"  • Docker Status: ✅ Available")
                print(f"  • Trading Algorithm Images: {len(algo_images)}")
                if algo_images:
                    print("  • Recent Images:")
                    for img in algo_images[:3]:  # Show first 3
                        print(f"    - {img['repository']}:{img['tag']} ({img['size']})")
            except Exception as e:
                print(f"\\n🐳 Docker: ⚠️  Available but error getting stats: {e}")
        else:
            print("\\n🐳 Docker: ❌ Not available")
    
    def _show_health_check(self):
        """Show comprehensive health check."""
        print("\\n🏥 System Health Check:\\n")
        
        health_status = "✅ HEALTHY"
        issues = []
        
        # Check agent
        try:
            self.agent.get_agent_stats()
            print("🤖 Agent: ✅ Healthy")
        except Exception as e:
            print(f"🤖 Agent: ❌ Error - {e}")
            issues.append("Agent has issues")
            health_status = "⚠️  DEGRADED"
        
        # Check RAG service
        if rag_service:
            try:
                rag_service.get_collection_stats()
                print("📚 Knowledge Base: ✅ Healthy")
            except Exception as e:
                print(f"📚 Knowledge Base: ❌ Error - {e}")
                issues.append("Knowledge base connection issues")
                health_status = "⚠️  DEGRADED"
        else:
            print("📚 Knowledge Base: ⚠️  Not installed (ChromaDB missing)")
            issues.append("ChromaDB not available")
        
        # Check Docker
        if docker_service.is_docker_available():
            print("🐳 Docker: ✅ Healthy")
        else:
            print("🐳 Docker: ⚠️  Not available")
            issues.append("Docker not available")
        
        # Check project service
        try:
            project_service.list_projects()
            print("📁 Project Service: ✅ Healthy")
        except Exception as e:
            print(f"📁 Project Service: ❌ Error - {e}")
            issues.append("Project service issues")
            health_status = "❌ UNHEALTHY"
        
        print(f"\\n🏥 Overall Status: {health_status}")
        if issues:
            print("\\n⚠️  Issues Found:")
            for issue in issues:
                print(f"  • {issue}")
            print("\\n💡 Recommendations:")
            if "ChromaDB not available" in issues:
                print("  • Install ChromaDB: pip install chromadb")
            if "Docker not available" in issues:
                print("  • Install Docker and ensure it's running")
    
    def _show_help(self):
        """Show comprehensive help information."""
        print('''\\n📖 Trade Agent v2.0 Help\\n

💬 Chat Commands:
  • Just type your message to interact with the AI
  • 'exit' or 'quit' - Exit the application
  • 'history' - Show conversation history
  • 'clear' - Clear conversation history
  • 'stats' - Show detailed system statistics
  • 'health' - Perform system health check
  • 'help' - Show this help message

🤖 What the AI can help you with:

📈 Algorithm Generation:
  • "Generate a RSI momentum strategy"
  • "Create a grid trading algorithm with Docker"
  • "Build a mean reversion bot for crypto"

🐳 Docker Operations:
  • "Build Docker image for my project"
  • "Containerize the trading algorithm"
  • "Show Docker deployment commands"

📚 Knowledge Base:
  • "Search for arbitrage strategies"
  • "Find examples of moving average crossovers"
  • "Add this strategy pattern to knowledge base"
  • "Show knowledge base statistics"

📁 Project Management:
  • "List my generated projects"
  • "Show project details for [project-name]"
  • "Create a new algorithm with custom parameters"

📊 Technical Analysis:
  • "Analyze MFI for AAPL"
  • "Is TSLA overbought or oversold?"
  • "Screen AAPL,MSFT,GOOGL for buy signals"
  • "Technical analysis of Bitcoin"

💡 Tips:
  • Be specific about your trading strategy requirements
  • Mention if you want Docker containerization
  • Ask about existing patterns before creating new ones
  • The AI uses intelligent routing to optimize responses
  • Technical analysis works with stocks and crypto symbols

🔗 Example Workflows:
  1. Search knowledge base → Generate algorithm → Build Docker image
  2. Technical analysis → Create strategy → Add to knowledge base
  3. Research existing patterns → Customize parameters → Deploy
  4. Screen symbols → Generate targeted algorithms → Containerize

🧠 Intelligent Routing:
  • The agent automatically detects query types and routes optimally
  • Use 'routing' command to see current status
  • Use 'routing toggle' to enable/disable smart routing
''')
    
    def _show_routing_info(self):
        """Show routing system information."""
        print("\n🧠 Intelligent Routing System Status:\n")
        
        agent_stats = self.agent.get_agent_stats()
        routing_enabled = agent_stats.get('routing_enabled', False)
        
        print(f"🔀 Status: {'✅ Enabled' if routing_enabled else '❌ Disabled'}")
        
        if routing_enabled:
            print("\n📋 Available Routes:")
            print("  • algorithm_generation - Code generation and Docker operations")
            print("  • technical_analysis - MFI analysis and stock/crypto signals")
            print("  • rag_search - Knowledge base and strategy searches")  
            print("  • mixed_analysis - Combined technical + algorithm/search requests")
            print("  • general_agent - General trading questions and explanations")
            
            print("\n🎯 How Routing Works:")
            print("  • Queries are automatically classified using AI")
            print("  • Each route uses optimized tools and context")
            print("  • Technical analysis gets real-time market data")
            print("  • Algorithm requests get specialized code generation")
            print("  • Mixed requests combine multiple capabilities")
            
            print("\n💡 Benefits:")
            print("  • Faster, more focused responses")
            print("  • Automatic symbol extraction and analysis")
            print("  • Context-aware tool selection")
            print("  • Optimized for different query types")
        else:
            print("\n⚠️  Routing is disabled - using fallback mode")
            print("  • All queries processed with standard agent")
            print("  • Use 'routing toggle' to enable intelligent routing")
    
    def _handle_routing_command(self, command: str):
        """Handle routing-related commands."""
        if command.lower() == 'toggle':
            current_status = self.agent.toggle_routing()
            status_text = "enabled" if current_status else "disabled"
            print(f"✅ Intelligent routing {status_text}")
        elif command.lower() == 'enable':
            self.agent.toggle_routing(True)
            print("✅ Intelligent routing enabled")
        elif command.lower() == 'disable':
            self.agent.toggle_routing(False)
            print("❌ Intelligent routing disabled")
        else:
            print("❌ Unknown routing command. Available: toggle, enable, disable")