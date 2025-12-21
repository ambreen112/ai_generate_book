"""
FastAPI backend for the RAG chatbot with OpenRouter integration.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from agent import run_agent
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RAG Chatbot API",
    description="API for Retrieval-Augmented Generation chatbot using OpenRouter and Qdrant",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QueryRequest(BaseModel):
    question: str
    selected_text: Optional[str] = ""

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]

# API Endpoints
@app.get("/")
async def root():
    return {"message": "RAG Chatbot API is running!"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "message": "RAG Chatbot API is running"}

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Query the RAG system with a question and optional selected text.
    The agent will prioritize the selected text if provided.
    """
    try:
        # Run the agent with the question and selected text
        response = run_agent(
            question=request.question,
            selected_text=request.selected_text
        )

        return QueryResponse(
            answer=response["answer"],
            sources=response["sources"]
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/query")
async def query_get_endpoint(
    question: str = Query(..., description="The question to ask"),
    selected_text: Optional[str] = Query("", description="Optional selected/highlighted text from the book")
):
    """
    Query the RAG system with a question and optional selected text (GET method).
    The agent will prioritize the selected text if provided.
    """
    try:
        # Run the agent with the question and selected text
        response = run_agent(
            question=question,
            selected_text=selected_text
        )

        return QueryResponse(
            answer=response["answer"],
            sources=response["sources"]
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)