"""API endpoints with improved error handling and structure."""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Optional

from .models import (
    ChatMessage, ChatResponse, ChatHistoryResponse, HealthResponse, ErrorResponse,
    ProjectCreateRequest, ProjectResponse, ProjectListResponse,
    DockerBuildRequest, DockerResponse,
    KnowledgeBaseSearchRequest, KnowledgeBaseAddRequest, KnowledgeBaseResponse
)
from config.settings import settings
from services.project_service import project_service, ProjectCreationError
from services.docker_service import docker_service, DockerError
from services.rag_service import rag_service, RAGError


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Trade Agent API",
        version="2.0.0",
        description="AI-powered trading algorithm generation and management API"
    )
    
    # Configure CORS
    api_config = settings.api_config
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_config['cors_origins'],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Global agent instance
    agent = None
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup."""
        nonlocal agent
        try:
            # Validate settings
            settings.validate_required_settings()
            
            # Initialize agent
            from agents.finance_agent import FinanceAgent
            agent = FinanceAgent()
            print("✅ Finance Agent initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize services: {e}")
            # Don't raise - let the app start but show errors in health check
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Comprehensive health check endpoint."""
        return HealthResponse(
            status="healthy" if agent else "degraded",
            service="Trade Agent API v2.0",
            agent_initialized=agent is not None,
            rag_service_available=rag_service is not None,
            docker_available=docker_service.is_docker_available(),
            timestamp=datetime.now().isoformat()
        )
    
    # Chat endpoints
    @app.post("/chat", response_model=ChatResponse)
    async def chat_endpoint(chat_message: ChatMessage):
        """Send a message to the finance agent and get response."""
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Finance agent not initialized"
            )
        
        try:
            response = agent.process_message(chat_message.message)
            return ChatResponse(response=response, success=True)
        except Exception as e:
            return ChatResponse(
                response="I encountered an error processing your message. Please try again.",
                success=False,
                error=str(e)
            )
    
    @app.get("/chat/history", response_model=ChatHistoryResponse)
    async def get_chat_history():
        """Get the current chat history."""
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Finance agent not initialized"
            )
        
        try:
            history_items = []
            chat_history = agent.chat_history
            
            for i in range(0, len(chat_history), 2):
                if i + 1 < len(chat_history):
                    user_msg = chat_history[i]
                    agent_msg = chat_history[i + 1]
                    history_items.append({
                        "user_message": user_msg.content,
                        "agent_response": agent_msg.content,
                        "timestamp": datetime.now().isoformat()
                    })
            
            return ChatHistoryResponse(history=history_items, success=True)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve chat history: {str(e)}"
            )
    
    @app.delete("/chat/history")
    async def clear_chat_history():
        """Clear the chat history."""
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Finance agent not initialized"
            )
        
        try:
            agent.chat_history = []
            return {"success": True, "message": "Chat history cleared"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to clear chat history: {str(e)}"
            )
    
    # Project management endpoints
    @app.post("/projects", response_model=ProjectResponse)
    async def create_project(request: ProjectCreateRequest):
        """Create a new trading algorithm project."""
        try:
            result = project_service.create_rust_project(
                request.algorithm_description,
                request.custom_params
            )
            
            if result['success']:
                response_data = ProjectResponse(
                    success=True,
                    project_name=result['project_name'],
                    project_path=result['project_path'],
                    strategy_name=result['strategy_name'],
                    base_name=result['base_name'],
                    message="Project created successfully"
                )
                
                # Build Docker image if requested
                if request.build_docker:
                    try:
                        docker_result = docker_service.build_image(
                            result['project_path'],
                            f"{result['base_name']}-algo"
                        )
                        if docker_result['success']:
                            response_data.message += f" and Docker image built successfully"
                        else:
                            response_data.message += f" but Docker build failed: {docker_result.get('error', 'Unknown error')}"
                    except DockerError as e:
                        response_data.message += f" but Docker build failed: {e}"
                
                return response_data
            else:
                return ProjectResponse(
                    success=False,
                    message="Project creation failed",
                    error=result.get('error', 'Unknown error')
                )
                
        except ProjectCreationError as e:
            return ProjectResponse(
                success=False,
                message="Project creation failed",
                error=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error: {str(e)}"
            )
    
    @app.get("/projects", response_model=ProjectListResponse)
    async def list_projects():  # type: ignore
        """List all generated projects."""
        try:
            result = project_service.list_projects()
            return ProjectListResponse(
                projects=result['projects'],
                count=result['count'],
                success=True
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list projects: {str(e)}"
            )
    
    @app.get("/projects/{project_name}")
    async def get_project_info(project_name: str):  # type: ignore
        """Get information about a specific project."""
        try:
            result = project_service.get_project_info(project_name)
            return {"success": True, "project": result}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {str(e)}"
            )
    
    # Docker endpoints
    @app.post("/docker/build", response_model=DockerResponse)
    async def build_docker_image(request: DockerBuildRequest):  # type: ignore
        """Build a Docker image for an existing project."""
        try:
            # Determine image name
            if request.custom_name:
                image_name = request.custom_name
            else:
                from pathlib import Path
                project_dir = Path(request.project_path)
                image_name = f"{project_dir.name}-algo"
            
            result = docker_service.build_image(request.project_path, image_name)
            
            if result['success']:
                return DockerResponse(
                    success=True,
                    image_name=result['image_name'],
                    build_duration=result['build_duration'],
                    size=result['size'],
                    message="Docker image built successfully"
                )
            else:
                return DockerResponse(
                    success=False,
                    message="Docker build failed",
                    error=result.get('error', 'Unknown error')
                )
                
        except DockerError as e:
            return DockerResponse(
                success=False,
                message="Docker build failed",
                error=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error: {str(e)}"
            )
    
    @app.get("/docker/images")
    async def list_docker_images():  # type: ignore
        """List Docker images."""
        try:
            images = docker_service.list_images()
            return {"success": True, "images": images}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list Docker images: {str(e)}"
            )
    
    # Knowledge base endpoints
    @app.post("/knowledge/search", response_model=KnowledgeBaseResponse)
    async def search_knowledge_base(request: KnowledgeBaseSearchRequest):  # type: ignore
        """Search the knowledge base."""
        try:
            if not rag_service:
                return KnowledgeBaseResponse(
                    success=False,
                    message="RAG service not available",
                    error="ChromaDB may not be installed"
                )
            
            results = rag_service.search_documents(
                request.query,
                request.n_results,
                request.topic_filter
            )
            
            return KnowledgeBaseResponse(
                success=True,
                results=results,
                message=f"Found {len(results)} results"
            )
            
        except RAGError as e:
            return KnowledgeBaseResponse(
                success=False,
                message="Knowledge base search failed",
                error=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error: {str(e)}"
            )
    
    @app.post("/knowledge/add", response_model=KnowledgeBaseResponse)
    async def add_to_knowledge_base(request: KnowledgeBaseAddRequest):  # type: ignore
        """Add content to the knowledge base."""
        try:
            if not rag_service:
                return KnowledgeBaseResponse(
                    success=False,
                    message="RAG service not available",
                    error="ChromaDB may not be installed"
                )
            
            doc_id = rag_service.add_document(request.content, request.topic)
            
            return KnowledgeBaseResponse(
                success=True,
                document_id=doc_id,
                message="Content added successfully"
            )
            
        except RAGError as e:
            return KnowledgeBaseResponse(
                success=False,
                message="Failed to add content",
                error=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error: {str(e)}"
            )
    
    @app.get("/knowledge/stats", response_model=KnowledgeBaseResponse)
    async def get_knowledge_base_stats():  # type: ignore
        """Get knowledge base statistics."""
        try:
            if not rag_service:
                return KnowledgeBaseResponse(
                    success=False,
                    message="RAG service not available",
                    error="ChromaDB may not be installed"
                )
            
            stats = rag_service.get_collection_stats()
            
            return KnowledgeBaseResponse(
                success=True,
                stats=stats,
                message="Knowledge base statistics retrieved"
            )
            
        except RAGError as e:
            return KnowledgeBaseResponse(
                success=False,
                message="Failed to get statistics",
                error=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error: {str(e)}"
            )
    
    return app


def run_api_server(host: str = None, port: int = None):
    """Run the FastAPI server."""
    import uvicorn
    
    api_config = settings.api_config
    host = host or api_config['host']
    port = port or api_config['port']
    
    app = create_app()
    uvicorn.run(app, host=host, port=port)