import os
import sys
from typing import List
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseMessage, HumanMessage, AIMessage

from trading_tools import generate_rust_crypto_algo, build_docker_image_only
from rag_tools import search_knowledge_base, add_to_knowledge_base

load_dotenv()

class FinanceAgent:
    """LangChain-based Finance Agent with RAG, code generation, and Docker capabilities."""
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("Error: GOOGLE_API_KEY not found in .env file or environment variables.")
            sys.exit(1)
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.1
        )
        
        self.tools = [
            generate_rust_crypto_algo,
            build_docker_image_only,
            search_knowledge_base,
            add_to_knowledge_base,
        ]
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a finance and crypto trading expert AI assistant with access to code generation, Docker containerization, and knowledge base capabilities.

You have access to these tools:

1. **Code Generation & Docker**: Use generate_rust_crypto_algo when users ask to:
   - Generate a crypto algorithm
   - Create a trading strategy  
   - Build a crypto trading bot
   - Make a trading algorithm
   - Develop a crypto strategy
   - Create and containerize algorithms
   
   This tool can optionally build Docker images. Ask if they want Docker containerization.

2. **Docker Build Only**: Use build_docker_image_only when users want to:
   - Build Docker image for existing project
   - Containerize existing Rust code
   - Create Docker container from project path

3. **Knowledge Base Search**: Use search_knowledge_base when users ask about:
   - Existing trading strategies
   - Financial concepts or definitions
   - Algorithm explanations
   - Market analysis techniques
   - Docker best practices for trading apps

4. **Knowledge Base Management**: Use add_to_knowledge_base to store new information

## Docker Integration Features:
- **Meaningful Names**: Images get names based on strategy (e.g., "rsi-momentum-algo", "grid-trading-algo")
- **Multi-stage Builds**: Optimized images using Rust musl for minimal size
- **Security**: Non-root user, health checks, proper labels
- **Development**: Ready-to-use commands for building and running

You can combine tools effectively:
- Search for strategy patterns, then generate code with Docker
- Generate algorithms and automatically containerize them
- Build Docker images for existing projects with custom names

Always ask if users want Docker containerization when generating new algorithms. Provide meaningful Docker commands and examples."""),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        self.agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
        
        self.chat_history: List[BaseMessage] = []
    
    def initialize_rag_system(self):
        """Initialize the RAG system with your existing ChromaDB setup."""
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
            # Check if the user is asking about Docker-related functionality
            docker_keywords = ['docker', 'container', 'containerize', 'image', 'build docker']
            if any(keyword in user_input.lower() for keyword in docker_keywords):
                print("[INFO] Detected Docker-related request")
            
            response = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": self.chat_history
            })
            
            agent_response = response.get("output", "I couldn't generate a response.")
            
            self.chat_history.append(HumanMessage(content=user_input))
            self.chat_history.append(AIMessage(content=agent_response))
            
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]
            
            return agent_response
            
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return error_msg