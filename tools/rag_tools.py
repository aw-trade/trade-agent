from langchain.tools import tool
from typing import Optional

from services.rag_service import rag_service, RAGError

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
    try:
        print(f"\n[RAG TOOL CALL] Searching knowledge base for: {query}\n")
        
        if not rag_service:
            return "❌ RAG service not available. ChromaDB may not be installed."
        
        # Search for relevant documents
        results = rag_service.search_documents(query, n_results=5)
        
        if not results:
            return f"📚 No relevant information found for '{query}' in the knowledge base.\n\nSuggestions:\n- Try different search terms\n- Add relevant content to the knowledge base first\n- Check if the query is related to trading or financial topics"
        
        # Format results
        formatted_response = f"📚 Found {len(results)} relevant results for '{query}':\n\n"
        
        for i, result in enumerate(results, 1):
            relevance = result.get('relevance_score', 0)
            topic = result.get('topic', 'Unknown')
            content_preview = result['content'][:300] + '...' if len(result['content']) > 300 else result['content']
            
            formatted_response += f"{i}. **Topic: {topic}** (Relevance: {relevance:.2f})\n{content_preview}\n\n"
        
        return formatted_response
        
    except RAGError as e:
        return f"❌ RAG search failed: {e}"
    except Exception as e:
        return f"❌ Unexpected error during search: {e}"

@tool 
def add_to_knowledge_base(content: str, topic: str) -> str:
    """
    Add new content to the knowledge base for future reference.
    
    Args:
        content: The content to add to the knowledge base
        topic: The topic/category for this content
    """
    try:
        print(f"\n[RAG TOOL CALL] Adding content to knowledge base under topic: {topic}\n")
        
        if not rag_service:
            return "❌ RAG service not available. ChromaDB may not be installed."
        
        # Add document to the knowledge base
        doc_id = rag_service.add_document(content, topic)
        
        return f"✅ Content successfully added to knowledge base!\n\n📋 Details:\n- Document ID: {doc_id}\n- Topic: {topic}\n- Content Length: {len(content)} characters\n\nThis content will now be searchable in future queries."
        
    except RAGError as e:
        return f"❌ Failed to add content to knowledge base: {e}"
    except Exception as e:
        return f"❌ Unexpected error while adding content: {e}"

@tool
def search_trading_strategies(query: str) -> str:
    """
    Search specifically for trading strategies in the knowledge base.
    
    Args:
        query: The search query for trading strategies
    
    Use this tool when users ask specifically about:
    - Trading strategy patterns
    - Algorithm implementations
    - Strategy parameters and configurations
    """
    try:
        print(f"\n[RAG TOOL CALL] Searching trading strategies for: {query}\n")
        
        if not rag_service:
            return "❌ RAG service not available. ChromaDB may not be installed."
        
        # Search for trading strategies specifically
        results = rag_service.search_trading_strategies(query)
        
        if not results:
            return f"📈 No trading strategies found for '{query}'.\n\nTry:\n- Adding trading strategies to the knowledge base\n- Using more general trading terms\n- Searching for related algorithm patterns"
        
        # Format strategy results
        formatted_response = f"📈 Found {len(results)} trading strategies for '{query}':\n\n"
        
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            strategy_name = metadata.get('strategy_name', 'Unknown Strategy')
            relevance = result.get('relevance_score', 0)
            content_preview = result['content'][:400] + '...' if len(result['content']) > 400 else result['content']
            
            formatted_response += f"{i}. **{strategy_name}** (Relevance: {relevance:.2f})\n{content_preview}\n\n"
        
        return formatted_response
        
    except RAGError as e:
        return f"❌ Trading strategy search failed: {e}"
    except Exception as e:
        return f"❌ Unexpected error during trading strategy search: {e}"

@tool
def get_knowledge_base_stats() -> str:
    """
    Get statistics about the current knowledge base.
    
    Use this tool to understand:
    - How many documents are stored
    - What topics are available
    - Knowledge base health and size
    """
    try:
        if not rag_service:
            return "❌ RAG service not available. ChromaDB may not be installed."
        
        stats = rag_service.get_collection_stats()
        
        response = f"📊 Knowledge Base Statistics:\n\n"
        response += f"📚 Total Documents: {stats['total_documents']}\n"
        response += f"📝 Total Content Length: {stats['total_content_length']:,} characters\n"
        response += f"📏 Average Document Length: {stats['average_content_length']:.1f} characters\n\n"
        
        if stats['topics']:
            response += "📂 Topics Distribution:\n"
            for topic, count in sorted(stats['topics'].items(), key=lambda x: x[1], reverse=True):
                response += f"  • {topic}: {count} documents\n"
        else:
            response += "📂 No documents found in the knowledge base.\n"
        
        response += f"\n🗂️ Collection: {stats['collection_name']}\n"
        response += f"💾 Storage: {stats['persist_directory']}"
        
        return response
        
    except RAGError as e:
        return f"❌ Failed to get knowledge base stats: {e}"
    except Exception as e:
        return f"❌ Unexpected error getting stats: {e}"