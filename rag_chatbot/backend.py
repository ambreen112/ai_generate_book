"""
FastAPI backend for the RAG Chatbot
Handles API endpoints for document ingestion, question answering, and chat functionality
"""
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
import asyncio
import json
import os
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader, PDFPlumberLoader, Docx2txtLoader, UnstructuredMarkdownLoader
)
import tempfile
import shutil

from database import get_db
from models import Book, Chapter, Chunk
from agent import run_agent_sync
import models

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing database...")
    models.create_tables()  # Create database tables
    # Vector store initialization is handled within the functions when needed
    yield
    # Shutdown


# Initialize FastAPI app
app = FastAPI(
    title="RAG Chatbot API",
    description="API for Retrieval-Augmented Generation chatbot for book content",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class QueryRequest(BaseModel):
    question: str
    selected_text: Optional[str] = ""
    book_id: Optional[int] = None
    max_results: Optional[int] = 5


class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    context_used: str


class BookCreate(BaseModel):
    title: str
    author: str
    description: Optional[str] = ""


class DocumentUploadResponse(BaseModel):
    message: str
    book_id: int
    chunks_added: int


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    selected_text: Optional[str] = ""
    book_id: Optional[int] = None


def get_retriever(book_id: Optional[int] = None):
    """Get a retriever for the specified book or general content"""
    vector_store = get_vector_store()
    # In a real implementation, you'd filter by book_id
    return vector_store


# API Endpoints
@app.get("/")
async def root():
    return {"message": "RAG Chatbot API is running!"}


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Query the RAG system with a question
    """
    try:
        vector_store = get_vector_store()
        agent = get_agent()

        # If user has selected specific text, use that as context
        if request.selected_text:
            retrieved_docs = []
            context = request.selected_text
        else:
            # Perform similarity search to retrieve relevant documents
            retrieved_docs = vector_store.similarity_search(
                request.question,
                k=request.max_results
            )
            context = ""  # Will be formatted by the agent

        # Get response from the agent
        response = run_agent_sync(
            question=request.question,
            selected_text=request.selected_text
        )

        return QueryResponse(
            answer=response["answer"],
            sources=response["sources"],
            context_used=context  # Context is handled internally by the agent
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint that maintains conversation history
    """
    try:
        vector_store = get_vector_store()
        agent = get_agent()

        # Get the last user message as the question
        if not request.messages or request.messages[-1].role != "user":
            raise HTTPException(status_code=400, detail="Last message must be from user")

        question = request.messages[-1].content

        # If user has selected specific text, use that as context
        if request.selected_text:
            retrieved_docs = []
            context = request.selected_text
        else:
            # Perform similarity search to retrieve relevant documents
            retrieved_docs = vector_store.similarity_search(
                question,
                k=5  # Default to 5 results
            )
            context = ""  # Will be formatted by the agent

        # Convert ChatMessage objects to the format expected by the agent
        conversation_history = []
        for msg in request.messages[:-1]:  # Exclude the current question
            conversation_history.append({
                "role": msg.role,
                "content": msg.content
            })

        # Get response from the agent
        response = run_agent_sync(
            question=question,
            selected_text=request.selected_text
        )

        return QueryResponse(
            answer=response["answer"],
            sources=response["sources"],
            context_used=context  # Context is handled internally by the agent
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@app.post("/books/", response_model=DocumentUploadResponse)
async def create_book(book: BookCreate, db=Depends(get_db)):
    """
    Create a new book entry in the database
    """
    try:
        db_book = Book(
            title=book.title,
            author=book.author,
            description=book.description
        )
        db.add(db_book)
        db.commit()
        db.refresh(db_book)

        return DocumentUploadResponse(
            message=f"Book '{book.title}' created successfully",
            book_id=db_book.id,
            chunks_added=0
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating book: {str(e)}")


@app.post("/upload/", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...), book_id: Optional[int] = None, db=Depends(get_db)):
    """
    Upload and process a document (PDF, DOCX, TXT, MD)
    """
    try:
        # Create a temporary file to save the uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name

        try:
            # Load the document based on its type
            if file.filename.lower().endswith('.pdf'):
                loader = PDFPlumberLoader(temp_file_path)
            elif file.filename.lower().endswith('.docx'):
                loader = Docx2txtLoader(temp_file_path)
            elif file.filename.lower().endswith('.txt'):
                loader = TextLoader(temp_file_path, encoding='utf-8')
            elif file.filename.lower().endswith('.md'):
                loader = UnstructuredMarkdownLoader(temp_file_path)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type. Please upload PDF, DOCX, TXT, or MD files.")

            documents = loader.load()

            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            chunks = text_splitter.split_documents(documents)

            # Add to vector store
            vector_store = get_vector_store()
            vector_store.add_documents(chunks)

            # If a book_id is provided, also store in the database
            if book_id:
                # Get the book from the database
                book = db.query(Book).filter(Book.id == book_id).first()
                if not book:
                    raise HTTPException(status_code=404, detail="Book not found")

                # Create a chapter for this document
                chapter = Chapter(
                    book_id=book_id,
                    title=file.filename,
                    content="\n".join([doc.page_content for doc in chunks]),
                    chapter_number=book.chapters.count() + 1
                )
                db.add(chapter)
                db.commit()
                db.refresh(chapter)

                # Create chunks in the database as well
                for i, chunk in enumerate(chunks):
                    chunk_db = Chunk(
                        chapter_id=chapter.id,
                        content=chunk.page_content,
                        chunk_number=i + 1
                    )
                    db.add(chunk_db)

                db.commit()

            return DocumentUploadResponse(
                message=f"Document '{file.filename}' processed successfully",
                book_id=book_id or 0,
                chunks_added=len(chunks)
            )
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@app.get("/books/{book_id}")
async def get_book(book_id: int, db=Depends(get_db)):
    """
    Get book details by ID
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "description": book.description,
        "created_at": book.created_at,
        "updated_at": book.updated_at
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "message": "RAG Chatbot API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)