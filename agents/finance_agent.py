"""Unified Finance Agent with advanced routing capabilities."""

import sys
import re
import logging
from typing import List, Dict, Optional, TypedDict, Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from config.settings import settings
from tools.trading_tools import generate_rust_crypto_algo, build_docker_image_only
from tools.rag_tools import search_knowledge_base, add_to_knowledge_base, search_trading_strategies, get_knowledge_base_stats
from tools.technical_indicators_tool import (
    get_mfi_analysis, validate_stock_symbol, get_technical_indicators,
    extract_symbols_from_text, build_indicators_context
)
from tools.technical_indicators_client import TechnicalIndicatorsClient

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the LangGraph routing system."""
    messages: List[BaseMessage]
    query_type: Optional[str]
    symbols: List[str]
    technical_data: Optional[str]
    user_message: str
    route_taken: Optional[str]


class FinanceAgentError(Exception):
    """Exception raised when Finance Agent operations fail."""
    pass


class FinanceAgent:
    """Unified Finance Agent with intelligent routing, RAG, code generation, Docker, and technical analysis capabilities."""
    
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
        
        # Initialize technical indicators client
        self.indicators_client = TechnicalIndicatorsClient()
        
        # Initialize routing system
        self.routing_enabled = True
        self.routing_graph = None
        
        # Set up tools
        self.tools = [
            generate_rust_crypto_algo,
            build_docker_image_only,
            search_knowledge_base,
            add_to_knowledge_base,
            search_trading_strategies,
            get_knowledge_base_stats,
            get_mfi_analysis,
            validate_stock_symbol,
            get_technical_indicators,  # Legacy support
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
        
        # Initialize routing graph
        if self.routing_enabled:
            self._build_routing_graph()
    
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

### 3. Technical Analysis
- **get_mfi_analysis**: Detailed MFI (Money Flow Index) analysis with overbought/oversold signals for stocks and crypto
- **validate_stock_symbol**: Validate if a stock or crypto symbol is available for analysis

Use these when users ask about:
- Existing trading strategies or patterns
- Financial concepts and definitions  
- Algorithm explanations and examples
- Market analysis techniques
- Historical trading data or research
- MFI (Money Flow Index) analysis for any stock or cryptocurrency
- Whether stocks/crypto are overbought, oversold, or neutral
- Buy/sell signals based on volume and price momentum
- Symbol validation before analysis

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
        # Use intelligent routing by default if available
        if self.routing_enabled and self.routing_graph:
            return self.process_message_with_routing(user_input)
        
        # Fallback to traditional processing
        try:
            # Log detected request types
            message_lower = user_input.lower()
            if any(kw in message_lower for kw in ['docker', 'container', 'containerize', 'image', 'build docker']):
                print("[INFO] Detected Docker-related request")
            
            if any(kw in message_lower for kw in ['search', 'find', 'knowledge', 'strategy', 'algorithm', 'example']):
                print("[INFO] Detected potential knowledge base query")
            
            if any(kw in message_lower for kw in ['mfi', 'rsi', 'macd', 'technical', 'overbought', 'oversold']):
                print("[INFO] Detected technical analysis request")
                
            symbols = extract_symbols_from_text(user_input)
            if symbols:
                print(f"[INFO] Detected symbols: {', '.join(symbols)}")
            
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
            "agent_initialized": True,
            "routing_enabled": self.routing_enabled
        }
    
    # ===== ROUTING SYSTEM METHODS =====
    
    def _route_query(self, state: AgentState) -> Literal["algorithm_generation", "technical_analysis", "rag_search", "general_agent", "mixed_analysis"]:
        """Route user queries based on content using LLM classification"""
        user_message = state["user_message"]
        
        routing_prompt = f"""
        Classify the following user query into one of these categories:
        
        1. "algorithm_generation" - User asks to create algorithms, generate code, build Docker images, or create trading bots
        2. "technical_analysis" - User asks about technical indicators (MFI, RSI, MACD), stock analysis, or mentions specific symbols
        3. "rag_search" - User asks to search for strategies, find examples, or needs knowledge base information
        4. "mixed_analysis" - User asks about both technical analysis AND algorithm generation or strategy searches
        5. "general_agent" - General trading questions, explanations, or requests that don't fit other categories
        
        User query: "{user_message}"
        
        Respond with only the category name, nothing else.
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=routing_prompt)])
            route = response.content.strip().lower()
            
            # Validate the route
            valid_routes = ["algorithm_generation", "technical_analysis", "rag_search", "mixed_analysis", "general_agent"]
            if route in valid_routes:
                return route
            else:
                # Default fallback based on keywords
                message_lower = user_message.lower()
                
                if any(kw in message_lower for kw in ['generate', 'create', 'build', 'algorithm', 'docker', 'rust']):
                    return "algorithm_generation"
                elif any(kw in message_lower for kw in ['mfi', 'rsi', 'macd', 'technical', 'overbought', 'oversold']):
                    return "technical_analysis"
                elif any(kw in message_lower for kw in ['search', 'find', 'strategy', 'example']):
                    return "rag_search"
                else:
                    return "general_agent"
                
        except Exception as e:
            logger.error(f"Error in query routing: {e}")
            return "general_agent"
    
    def _extract_symbols(self, text: str) -> List[str]:
        """Extract stock symbols from text using both regex and LLM"""
        if not text.strip():
            return []
        
        # First try regex extraction
        regex_symbols = extract_symbols_from_text(text)
        if regex_symbols:
            return regex_symbols
        
        # If no symbols found, try LLM extraction for company names
        extraction_prompt = f"""
        Analyze the following text and extract all stock symbols and company references. 
        
        For each company or stock mentioned, provide the correct stock ticker symbol.
        
        Examples:
        - "Apple" or "AAPL" → AAPL
        - "Microsoft" or "MSFT" → MSFT  
        - "GPU company" or "chip maker" → NVDA
        - "streaming giant" → NFLX
        - "electric car company" → TSLA
        - "e-commerce giant" → AMZN
        - "search engine company" → GOOGL
        - "big tech" → AAPL,MSFT,GOOGL,AMZN,META
        
        Text to analyze: "{text}"
        
        Respond ONLY with a comma-separated list of stock symbols (e.g., AAPL,MSFT,NVDA).
        If no stocks are mentioned, respond with: NONE
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=extraction_prompt)])
            result = response.content.strip()
            
            if result == "NONE" or not result:
                return []
            
            # Parse the response
            symbols = [symbol.strip().upper() for symbol in result.split(',')]
            
            # Filter out invalid symbols (basic validation)
            valid_symbols = []
            for symbol in symbols:
                # Remove any non-alphabetic characters and validate length
                clean_symbol = re.sub(r'[^A-Z]', '', symbol)
                if 1 <= len(clean_symbol) <= 5:
                    valid_symbols.append(clean_symbol)
            
            return list(set(valid_symbols))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error in LLM symbol extraction: {e}")
            return []
    
    def _prepare_state(self, state: AgentState) -> AgentState:
        """Extract symbols and set up initial state"""
        symbols = self._extract_symbols(state["user_message"])
        state["symbols"] = symbols
        return state
    
    def _algorithm_generation_node(self, state: AgentState) -> AgentState:
        """Handle algorithm generation and Docker requests using existing tools"""
        user_message = state["user_message"]
        
        # Add context about available algorithms if symbols were mentioned
        symbols = state["symbols"]
        context = ""
        if symbols:
            context = f"\n\nNote: User mentioned symbols: {', '.join(symbols)}. Consider incorporating these in the algorithm."
        
        # Use the existing agent executor for algorithm generation
        try:
            response = self.agent_executor.invoke({
                "input": user_message + context,
                "chat_history": self.chat_history[-5:],  # Limited history for context
                "system_message": self.system_message
            })
            
            agent_response = response.get("output", "I couldn't generate a response.")
            state["messages"] = [HumanMessage(content=user_message), AIMessage(content=agent_response)]
            state["route_taken"] = "algorithm_generation"
            
        except Exception as e:
            error_msg = f"Error in algorithm generation: {str(e)}"
            state["messages"] = [HumanMessage(content=user_message), AIMessage(content=error_msg)]
            state["route_taken"] = "algorithm_generation"
        
        return state
    
    def _technical_analysis_node(self, state: AgentState) -> AgentState:
        """Handle technical analysis requests"""
        symbols = state["symbols"]
        user_message = state["user_message"]
        
        # Build technical context
        technical_data = build_indicators_context(symbols)
        state["technical_data"] = technical_data
        
        enhanced_message = user_message
        if technical_data:
            enhanced_message += f"\n\nRelevant technical data:{technical_data}"
        
        # Create focused technical analysis prompt
        tech_system_msg = """You are a technical analysis expert. Use the provided technical indicator data to give detailed analysis and trading recommendations. Focus on:
        1. MFI interpretation (overbought >80, oversold <20)
        2. Trading signals and recommendations
        3. Risk management suggestions
        4. Entry/exit points if applicable
        
        Be specific and actionable in your advice."""
        
        messages = [SystemMessage(content=tech_system_msg)]
        messages.append(HumanMessage(content=enhanced_message))
        
        try:
            response = self.llm.invoke(messages)
            state["messages"] = [HumanMessage(content=user_message), AIMessage(content=response.content)]
            state["route_taken"] = "technical_analysis"
        except Exception as e:
            error_msg = f"Error in technical analysis: {str(e)}"
            state["messages"] = [HumanMessage(content=user_message), AIMessage(content=error_msg)]
            state["route_taken"] = "technical_analysis"
        
        return state
    
    def _rag_search_node(self, state: AgentState) -> AgentState:
        """Handle RAG and knowledge base searches"""
        user_message = state["user_message"]
        
        # Use existing agent executor with focus on RAG tools
        try:
            rag_context = "Focus on using search_knowledge_base and search_trading_strategies tools to find relevant information."
            response = self.agent_executor.invoke({
                "input": user_message + f"\n\n{rag_context}",
                "chat_history": self.chat_history[-5:],
                "system_message": self.system_message
            })
            
            agent_response = response.get("output", "I couldn't find relevant information.")
            state["messages"] = [HumanMessage(content=user_message), AIMessage(content=agent_response)]
            state["route_taken"] = "rag_search"
            
        except Exception as e:
            error_msg = f"Error in knowledge search: {str(e)}"
            state["messages"] = [HumanMessage(content=user_message), AIMessage(content=error_msg)]
            state["route_taken"] = "rag_search"
        
        return state
    
    def _mixed_analysis_node(self, state: AgentState) -> AgentState:
        """Handle requests requiring both technical analysis and other capabilities"""
        symbols = state["symbols"]
        user_message = state["user_message"]
        
        # Get technical data first
        technical_data = build_indicators_context(symbols)
        state["technical_data"] = technical_data
        
        # Enhance message with technical context
        enhanced_message = user_message
        if technical_data:
            enhanced_message += f"\n\nTechnical Analysis Context:{technical_data}"
        
        # Use full agent capabilities
        try:
            response = self.agent_executor.invoke({
                "input": enhanced_message,
                "chat_history": self.chat_history[-5:],
                "system_message": self.system_message
            })
            
            agent_response = response.get("output", "I couldn't generate a comprehensive response.")
            state["messages"] = [HumanMessage(content=user_message), AIMessage(content=agent_response)]
            state["route_taken"] = "mixed_analysis"
            
        except Exception as e:
            error_msg = f"Error in mixed analysis: {str(e)}"
            state["messages"] = [HumanMessage(content=user_message), AIMessage(content=error_msg)]
            state["route_taken"] = "mixed_analysis"
        
        return state
    
    def _general_agent_node(self, state: AgentState) -> AgentState:
        """Handle general questions using the full agent"""
        user_message = state["user_message"]
        
        try:
            response = self.agent_executor.invoke({
                "input": user_message,
                "chat_history": self.chat_history[-5:],
                "system_message": self.system_message
            })
            
            agent_response = response.get("output", "I couldn't generate a response.")
            state["messages"] = [HumanMessage(content=user_message), AIMessage(content=agent_response)]
            state["route_taken"] = "general_agent"
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            state["messages"] = [HumanMessage(content=user_message), AIMessage(content=error_msg)]
            state["route_taken"] = "general_agent"
        
        return state
    
    def _build_routing_graph(self) -> None:
        """Build the LangGraph workflow for intelligent routing"""
        try:
            workflow = StateGraph(AgentState)
            
            # Add nodes
            workflow.add_node("prepare", self._prepare_state)
            workflow.add_node("algorithm_generation", self._algorithm_generation_node)
            workflow.add_node("technical_analysis", self._technical_analysis_node)
            workflow.add_node("rag_search", self._rag_search_node)
            workflow.add_node("mixed_analysis", self._mixed_analysis_node)
            workflow.add_node("general_agent", self._general_agent_node)
            
            # Add edges
            workflow.add_edge(START, "prepare")
            workflow.add_conditional_edges(
                "prepare",
                self._route_query,
                {
                    "algorithm_generation": "algorithm_generation",
                    "technical_analysis": "technical_analysis",
                    "rag_search": "rag_search",
                    "mixed_analysis": "mixed_analysis",
                    "general_agent": "general_agent"
                }
            )
            
            # All nodes end the workflow
            workflow.add_edge("algorithm_generation", END)
            workflow.add_edge("technical_analysis", END)
            workflow.add_edge("rag_search", END)
            workflow.add_edge("mixed_analysis", END)
            workflow.add_edge("general_agent", END)
            
            self.routing_graph = workflow.compile()
            logger.info("Routing graph initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to build routing graph: {e}")
            self.routing_enabled = False
    
    def process_message_with_routing(self, user_input: str) -> str:
        """Process a user message using the intelligent routing system"""
        if not self.routing_enabled or not self.routing_graph:
            # Fallback to standard processing
            return self.process_message(user_input)
        
        try:
            # Prepare initial state
            initial_state = AgentState(
                messages=[],
                query_type=None,
                symbols=[],
                technical_data=None,
                user_message=user_input,
                route_taken=None
            )
            
            # Run the workflow
            result = self.routing_graph.invoke(initial_state)
            
            # Extract the response
            if result["messages"] and len(result["messages"]) > 0:
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    response = last_message.content
                    
                    # Log routing information
                    route_taken = result.get("route_taken", "unknown")
                    symbols_found = result.get("symbols", [])
                    
                    logger.info(f"Query routed to: {route_taken}")
                    if symbols_found:
                        logger.info(f"Symbols extracted: {', '.join(symbols_found)}")
                    
                    # Update chat history
                    self.chat_history.append(HumanMessage(content=user_input))
                    self.chat_history.append(AIMessage(content=response))
                    
                    # Trim chat history if too long
                    if len(self.chat_history) > self.max_chat_history:
                        self.chat_history = self.chat_history[-self.max_chat_history:]
                    
                    return response
            
            return "I apologize, but I couldn't generate a response. Please try again."
            
        except Exception as e:
            logger.error(f"Error in routing workflow: {e}")
            # Fallback to standard processing
            return self.process_message(user_input)
    
    def toggle_routing(self, enabled: bool = None) -> bool:
        """Enable or disable intelligent routing"""
        if enabled is None:
            self.routing_enabled = not self.routing_enabled
        else:
            self.routing_enabled = enabled
        
        if self.routing_enabled and not self.routing_graph:
            self._build_routing_graph()
        
        return self.routing_enabled