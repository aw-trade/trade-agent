"""RAG (Retrieval-Augmented Generation) service with ChromaDB integration."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from config.settings import settings


class RAGError(Exception):
    """Exception raised when RAG operations fail."""
    pass


class RAGService:
    """Service for RAG operations using ChromaDB."""
    
    def __init__(self):
        if not CHROMADB_AVAILABLE:
            raise RAGError("ChromaDB not available. Install with: pip install chromadb")
        
        self.config = settings.chromadb_config
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize ChromaDB client and collection."""
        try:
            # Ensure persist directory exists
            persist_dir = Path(self.config['persist_directory'])
            persist_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize client
            self.client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(
                    name=self.config['collection_name']
                )
            except ValueError:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name=self.config['collection_name'],
                    metadata={"description": "Trading strategies and algorithms knowledge base"}
                )
            
        except Exception as e:
            raise RAGError(f"Failed to initialize ChromaDB: {e}")
    
    def add_document(self, content: str, topic: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a document to the knowledge base."""
        try:
            if not self.collection:
                raise RAGError("ChromaDB collection not initialized")
            
            # Generate document ID
            doc_id = self._generate_document_id(content, topic)
            
            # Prepare metadata
            doc_metadata = {
                'topic': topic,
                'added_date': datetime.now().isoformat(),
                'content_length': len(content),
                'content_hash': hashlib.md5(content.encode()).hexdigest()
            }
            
            if metadata:
                doc_metadata.update(metadata)
            
            # Add document to collection
            self.collection.add(
                documents=[content],
                ids=[doc_id],
                metadatas=[doc_metadata]
            )
            
            return doc_id
            
        except Exception as e:
            raise RAGError(f"Failed to add document: {e}")
    
    def search_documents(self, query: str, n_results: int = 5, 
                        topic_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search documents in the knowledge base."""
        try:
            if not self.collection:
                raise RAGError("ChromaDB collection not initialized")
            
            # Prepare query filters
            where_filter = {}
            if topic_filter:
                where_filter['topic'] = topic_filter
            
            # Perform search
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter if where_filter else None
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                    distance = results['distances'][0][i] if results['distances'] and results['distances'][0] else None
                    
                    formatted_results.append({
                        'id': results['ids'][0][i] if results['ids'] and results['ids'][0] else '',
                        'content': doc,
                        'metadata': metadata,
                        'relevance_score': 1 - distance if distance is not None else None,
                        'topic': metadata.get('topic', 'Unknown')
                    })
            
            return formatted_results
            
        except Exception as e:
            raise RAGError(f"Failed to search documents: {e}")
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID."""
        try:
            if not self.collection:
                raise RAGError("ChromaDB collection not initialized")
            
            result = self.collection.get(ids=[doc_id])
            
            if result['documents'] and result['documents'][0]:
                metadata = result['metadatas'][0] if result['metadatas'] else {}
                return {
                    'id': doc_id,
                    'content': result['documents'][0],
                    'metadata': metadata,
                    'topic': metadata.get('topic', 'Unknown')
                }
            
            return None
            
        except Exception as e:
            raise RAGError(f"Failed to get document: {e}")
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the knowledge base."""
        try:
            if not self.collection:
                raise RAGError("ChromaDB collection not initialized")
            
            self.collection.delete(ids=[doc_id])
            return True
            
        except Exception as e:
            raise RAGError(f"Failed to delete document: {e}")
    
    def list_documents(self, topic_filter: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List documents in the knowledge base."""
        try:
            if not self.collection:
                raise RAGError("ChromaDB collection not initialized")
            
            where_filter = {}
            if topic_filter:
                where_filter['topic'] = topic_filter
            
            result = self.collection.get(
                where=where_filter if where_filter else None,
                limit=limit
            )
            
            documents = []
            if result['documents']:
                for i, doc in enumerate(result['documents']):
                    metadata = result['metadatas'][i] if result['metadatas'] else {}
                    documents.append({
                        'id': result['ids'][i] if result['ids'] else '',
                        'content_preview': doc[:200] + '...' if len(doc) > 200 else doc,
                        'content_length': len(doc),
                        'metadata': metadata,
                        'topic': metadata.get('topic', 'Unknown'),
                        'added_date': metadata.get('added_date', 'Unknown')
                    })
            
            return documents
            
        except Exception as e:
            raise RAGError(f"Failed to list documents: {e}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        try:
            if not self.collection:
                raise RAGError("ChromaDB collection not initialized")
            
            # Get total count
            total_docs = self.collection.count()
            
            # Get topics distribution
            all_docs = self.collection.get()
            topics = {}
            total_content_length = 0
            
            if all_docs['metadatas']:
                for metadata in all_docs['metadatas']:
                    topic = metadata.get('topic', 'Unknown')
                    topics[topic] = topics.get(topic, 0) + 1
                    total_content_length += metadata.get('content_length', 0)
            
            return {
                'total_documents': total_docs,
                'topics': topics,
                'total_content_length': total_content_length,
                'average_content_length': total_content_length / total_docs if total_docs > 0 else 0,
                'collection_name': self.config['collection_name'],
                'persist_directory': self.config['persist_directory']
            }
            
        except Exception as e:
            raise RAGError(f"Failed to get collection stats: {e}")
    
    def _generate_document_id(self, content: str, topic: str) -> str:
        """Generate a unique document ID."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        topic_hash = hashlib.md5(topic.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{topic_hash}_{content_hash}_{timestamp}"
    
    def add_trading_strategy(self, strategy_name: str, description: str, 
                           parameters: Dict[str, Any], source: str = "user") -> str:
        """Add a trading strategy to the knowledge base."""
        content = f"""Trading Strategy: {strategy_name}

Description:
{description}

Parameters:
{self._format_parameters(parameters)}

Source: {source}
Added: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        metadata = {
            'strategy_name': strategy_name,
            'source': source,
            'parameters': parameters,
            'type': 'trading_strategy'
        }
        
        return self.add_document(content, 'trading_strategies', metadata)
    
    def search_trading_strategies(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Search for trading strategies specifically."""
        return self.search_documents(query, n_results, topic_filter='trading_strategies')
    
    def add_algorithm_example(self, algorithm_type: str, code: str, 
                            description: str, language: str = "rust") -> str:
        """Add an algorithm example to the knowledge base."""
        content = f"""Algorithm Type: {algorithm_type}
Language: {language}

Description:
{description}

Code:
```{language}
{code}
```

Added: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        metadata = {
            'algorithm_type': algorithm_type,
            'language': language,
            'code_length': len(code),
            'type': 'algorithm_example'
        }
        
        return self.add_document(content, 'algorithm_examples', metadata)
    
    def search_algorithm_examples(self, query: str, language: Optional[str] = None, 
                                n_results: int = 3) -> List[Dict[str, Any]]:
        """Search for algorithm examples."""
        results = self.search_documents(query, n_results * 2, topic_filter='algorithm_examples')
        
        if language:
            # Filter by language
            filtered_results = [r for r in results if r['metadata'].get('language') == language]
            return filtered_results[:n_results]
        
        return results[:n_results]
    
    def _format_parameters(self, parameters: Dict[str, Any]) -> str:
        """Format parameters dictionary for storage."""
        formatted = []
        for key, value in parameters.items():
            formatted.append(f"- {key}: {value}")
        return "\n".join(formatted)


# Global RAG service instance
try:
    rag_service = RAGService()
except RAGError:
    # If ChromaDB is not available, create a dummy service
    rag_service = None