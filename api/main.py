"""
Main API Entry Point
FastAPI application for interacting with the Enterprise GenAI Orchestrator.
Includes Pydantic models for validation and structured logging.
"""

import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from loguru import logger
from src.agents.autonomous_agent import AutonomousAgent, revenue_tool

# --- Configuration ---

class Settings(BaseSettings):
    azure_openai_endpoint: str = "https://your-resource.openai.azure.com/"
    azure_openai_api_key: str = "your-key"
    azure_openai_api_version: str = "2023-07-01-preview"
    azure_openai_chat_deployment: str = "gpt-4o"
    
    class Config:
        env_file = ".env"

settings = Settings()

# --- Models ---

class QueryRequest(BaseModel):
    prompt: str = Field(..., example="What was Microsoft's revenue in Q4 2023?")
    session_id: Optional[str] = Field(None, example="user-123-session-abc")

class QueryResponse(BaseModel):
    answer: str
    session_id: Optional[str]
    metadata: dict = Field(default_factory=dict)

# --- App Initialization ---

app = FastAPI(
    title="Enterprise GenAI Orchestrator API",
    description="Scalable API for RAG and Agentic Workflows",
    version="1.0.0"
)

# Global agent instance (In production, consider a factory or dependency injection)
agent = AutonomousAgent(
    azure_endpoint=settings.azure_openai_endpoint,
    api_key=settings.azure_openai_api_key,
    api_version=settings.azure_openai_api_version,
    deployment_name=settings.azure_openai_chat_deployment,
    tools=[revenue_tool]
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Enterprise GenAI Orchestrator API...")

@app.post("/v1/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a user query through the autonomous agent orchestrator.
    """
    logger.info(f"Received query: {request.prompt} (Session: {request.session_id})")
    
    try:
        answer = await agent.run(request.prompt)
        
        return QueryResponse(
            answer=answer,
            session_id=request.session_id,
            metadata={"status": "success", "engine": "gpt-4o"}
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error during AI orchestration")

@app.get("/health")
async def health_check():
    """Service health check."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
