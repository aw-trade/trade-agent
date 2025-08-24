"""Refactored Finance Agent using the new service architecture."""

import sys
from typing import List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseMessage, HumanMessage, AIMessage

from config.settings import settings
from tools.trading_tools import generate_rust_crypto_algo, build_docker_image_only
from tools.rag_tools import search_knowledge_base, add_to_knowledge_base, search_trading_strategies, get_knowledge_base_stats


class FinanceAgentError(Exception):
    """Exception raised when Finance Agent operations fail."""
    pass


class FinanceAgent:
    """LangChain-based Finance Agent with RAG, code generation, and Docker capabilities."""
    
    def __init__(self):
        # Validate settings
        try:
            settings.validate_required_settings()
        except Exception as e:
            print(f"Error: Configuration validation failed: {e}")
            sys.exit(1)
        
        # Initialize LLM
        langchain_config = settings.langchain_config
        self.llm = ChatGoogleGenerativeAI(
            model=langchain_config['model'],
            google_api_key=settings.google_api_key,
            temperature=langchain_config['temperature']
        )
        
        # Set up tools
        self.tools = [
            generate_rust_crypto_algo,
            build_docker_image_only,
            search_knowledge_base,
            add_to_knowledge_base,
            search_trading_strategies,
            get_knowledge_base_stats,
        ]
        
        # Create prompt template and store system message
        self.system_message = self._get_system_message()
        self.prompt = self._create_prompt_template()
        
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
            verbose=langchain_config['verbose'],
            handle_parsing_errors=True,
            max_iterations=langchain_config['max_iterations']
        )
        
        # Initialize chat history
        api_config = settings.api_config
        self.max_chat_history = api_config['max_chat_history']
        self.chat_history: List[BaseMessage] = []
    
    def _get_system_message(self) -> str:
        """Get the system message for the agent."""
        return """You are a finance and crypto trading expert AI assistant with access to advanced code generation, Docker containerization, and knowledge base capabilities.

## Available Tools:

### 1. Code Generation & Docker
- **generate_rust_crypto_algo**: Create complete Rust trading algorithms with optional Docker containerization
- **build_docker_image_only**: Build Docker images for existing projects

Use these when users ask to:
- Generate crypto algorithms or trading strategies
- Create trading bots or automated systems
- Build or containerize algorithms
- Develop trading systems with specific indicators (RSI, MACD, etc.)

### 2. Knowledge Base & RAG
- **search_knowledge_base**: General search across all knowledge base content
- **search_trading_strategies**: Focused search for trading strategies and patterns
- **add_to_knowledge_base**: Store new information for future reference
- **get_knowledge_base_stats**: View knowledge base statistics and health

Use these when users ask about:
- Existing trading strategies or patterns
- Financial concepts and definitions  
- Algorithm explanations and examples
- Market analysis techniques
- Historical trading data or research

## Advanced Features:

### Docker Integration
- **Automated Naming**: Images get meaningful names based on strategy (e.g., "rsi-momentum-algo")
- **Multi-stage Builds**: Optimized images using Rust musl targets for minimal size
- **Security**: Non-root users, health checks, proper resource limits
- **Development Ready**: Interactive modes, volume mounts, environment customization

### Knowledge Management
- **Semantic Search**: Find relevant strategies using natural language queries
- **Topic Organization**: Content organized by categories (strategies, indicators, concepts)
- **Version Tracking**: Document history and metadata for research continuity
- **Strategy Library**: Build a personal library of trading patterns and algorithms

### Project Management
- **Structured Generation**: Consistent project layouts with documentation
- **Configuration Management**: Environment-based parameter customization
- **Template System**: Reusable patterns for different algorithm types
- **Validation**: Automatic code and configuration validation

## Interaction Guidelines:

1. **Be Proactive**: Suggest Docker containerization for new algorithms
2. **Leverage Knowledge**: Search existing patterns before creating new ones
3. **Provide Context**: Explain trading concepts and strategy rationale
4. **Offer Examples**: Use knowledge base to show similar implementations
5. **Consider Workflow**: Think about development, testing, and deployment steps

## Example Workflows:

- **Strategy Development**: Search existing patterns → Generate custom algorithm → Containerize → Document
- **Research Mode**: Search knowledge base → Add findings → Cross-reference with generated code
- **Production Ready**: Generate algorithm → Build Docker image → Provide deployment commands

Always ask about Docker containerization preferences and suggest knowledge base searches for related strategies. Focus on practical, deployable solutions with clear documentation."""
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Create the system prompt template for the agent."""
        return ChatPromptTemplate.from_messages([
            ("system", "{system_message}"),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
    
    def process_message(self, user_input: str) -> str:
        """Process a user message and return the agent's response."""
        try:
            # Log Docker-related requests
            docker_keywords = ['docker', 'container', 'containerize', 'image', 'build docker']
            if any(keyword in user_input.lower() for keyword in docker_keywords):
                print("[INFO] Detected Docker-related request")
            
            # Log RAG-related requests
            rag_keywords = ['search', 'find', 'knowledge', 'strategy', 'algorithm', 'example']
            if any(keyword in user_input.lower() for keyword in rag_keywords):
                print("[INFO] Detected potential knowledge base query")
            
            # Process with agent
            response = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": self.chat_history,
                "system_message": self.system_message
            })
            
            agent_response = response.get("output", "I couldn't generate a response.")
            
            # Update chat history
            self.chat_history.append(HumanMessage(content=user_input))
            self.chat_history.append(AIMessage(content=agent_response))
            
            # Trim chat history if too long
            if len(self.chat_history) > self.max_chat_history:
                self.chat_history = self.chat_history[-self.max_chat_history:]
            
            return agent_response
            
        except Exception as e:
            error_msg = f"An error occurred while processing your message: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return error_msg
    
    def display_chat_history(self) -> None:
        """Print the current chat history."""
        print("\\n--- Chat History ---")
        for message in self.chat_history:
            if isinstance(message, HumanMessage):
                print(f"You: {message.content}")
            elif isinstance(message, AIMessage):
                print(f"Agent: {message.content}")
        print("--------------------\\n")
    
    def clear_history(self) -> None:
        """Clear the chat history."""
        self.chat_history = []
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.tools]
    
    def get_agent_stats(self) -> dict:
        """Get statistics about the agent."""
        return {
            "chat_history_length": len(self.chat_history),
            "max_chat_history": self.max_chat_history,
            "available_tools": len(self.tools),
            "tool_names": self.get_available_tools(),
            "llm_model": settings.langchain_config['model'],
            "agent_initialized": True
        }