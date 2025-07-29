import os
import sys
from typing import List
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseMessage, HumanMessage, AIMessage

from trading_tools import generate_rust_crypto_algo
from rag_tools import search_knowledge_base, add_to_knowledge_base

load_dotenv()

class FinanceAgent:
    """LangChain-based Finance Agent with RAG and code generation capabilities."""
    
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
            search_knowledge_base,
            add_to_knowledge_base,
        ]
        
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