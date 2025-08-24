"""API request and response models."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    """Chat message request model."""
    message: str = Field(..., min_length=1, max_length=5000, description="The chat message")


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="The agent's response")
    success: bool = Field(..., description="Whether the request was successful")
    error: Optional[str] = Field(None, description="Error message if any")


class ChatHistoryItem(BaseModel):
    """Individual chat history item."""
    user_message: str = Field(..., description="User's message")
    agent_response: str = Field(..., description="Agent's response")
    timestamp: str = Field(..., description="Message timestamp")


class ChatHistoryResponse(BaseModel):
    """Chat history response model."""
    history: List[ChatHistoryItem] = Field(..., description="Chat history items")
    success: bool = Field(..., description="Whether the request was successful")


class ProjectCreateRequest(BaseModel):
    """Project creation request model."""
    algorithm_description: str = Field(..., min_length=10, max_length=1000, description="Algorithm description")
    build_docker: bool = Field(False, description="Whether to build Docker image")
    custom_params: Optional[Dict[str, Any]] = Field(None, description="Custom strategy parameters")


class ProjectResponse(BaseModel):
    """Project operation response model."""
    success: bool = Field(..., description="Whether the operation was successful")
    project_name: Optional[str] = Field(None, description="Generated project name")
    project_path: Optional[str] = Field(None, description="Project file path")
    strategy_name: Optional[str] = Field(None, description="Strategy name")
    base_name: Optional[str] = Field(None, description="Base name for Docker images")
    message: str = Field(..., description="Status message")
    error: Optional[str] = Field(None, description="Error message if any")


class ProjectListResponse(BaseModel):
    """Project list response model."""
    projects: List[Dict[str, Any]] = Field(..., description="List of projects")
    count: int = Field(..., description="Number of projects")
    success: bool = Field(..., description="Whether the request was successful")


class DockerBuildRequest(BaseModel):
    """Docker build request model."""
    project_path: str = Field(..., description="Path to the project directory")
    custom_name: Optional[str] = Field(None, description="Custom Docker image name")


class DockerResponse(BaseModel):
    """Docker operation response model."""
    success: bool = Field(..., description="Whether the operation was successful")
    image_name: Optional[str] = Field(None, description="Docker image name")
    build_duration: Optional[float] = Field(None, description="Build duration in seconds")
    size: Optional[str] = Field(None, description="Image size")
    message: str = Field(..., description="Status message")
    error: Optional[str] = Field(None, description="Error message if any")


class KnowledgeBaseSearchRequest(BaseModel):
    """Knowledge base search request model."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    topic_filter: Optional[str] = Field(None, description="Filter by topic")
    n_results: int = Field(5, ge=1, le=20, description="Number of results to return")


class KnowledgeBaseAddRequest(BaseModel):
    """Knowledge base add content request model."""
    content: str = Field(..., min_length=10, max_length=10000, description="Content to add")
    topic: str = Field(..., min_length=1, max_length=100, description="Content topic/category")


class KnowledgeBaseResponse(BaseModel):
    """Knowledge base operation response model."""
    success: bool = Field(..., description="Whether the operation was successful")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="Search results")
    document_id: Optional[str] = Field(None, description="Document ID for added content")
    stats: Optional[Dict[str, Any]] = Field(None, description="Knowledge base statistics")
    message: str = Field(..., description="Status message")
    error: Optional[str] = Field(None, description="Error message if any")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    agent_initialized: bool = Field(..., description="Whether the agent is initialized")
    rag_service_available: bool = Field(..., description="Whether RAG service is available")
    docker_available: bool = Field(..., description="Whether Docker is available")
    timestamp: str = Field(..., description="Health check timestamp")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    error_type: Optional[str] = Field(None, description="Error type/category")
    timestamp: str = Field(..., description="Error timestamp")