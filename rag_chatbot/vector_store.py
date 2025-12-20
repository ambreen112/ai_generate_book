"""
Qdrant vector store with retrieve function tool for the RAG agent.
"""
import os
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import PointStruct, Distance
from openai import OpenAI
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenRouter client for embeddings
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# Initialize Qdrant client
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=30
)

def get_embedding(text: str) -> List[float]:
    """
    Get embedding for a given text using OpenRouter's text-embedding-3-small model (1536 dimensions).

    Args:
        text (str): Text to embed

    Returns:
        List[float]: Embedding vector (1536 dimensions)
    """
    try:
        response = openrouter_client.embeddings.create(
            model="openai/text-embedding-3-small",  # 1536 dimensions
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error getting OpenRouter embedding: {e}")
        raise

def retrieve(query: str, selected_text: str = "") -> str:
    """
    Retrieve relevant documents from the vector store based on the query and selected text.
    Prioritizes selected text if provided.

    Args:
        query (str): Main query to search for
        selected_text (str): Optional selected/highlighted text from the book (higher priority)

    Returns:
        str: Formatted context with source filenames
    """
    # This function can be called by the agent as a tool
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "book_content")
    if not collection_name:
        return "Error: QDRANT_COLLECTION_NAME not set."

    all_results = []

    # Priority 1: Selected text (higher limit)
    if selected_text.strip():
        try:
            sel_emb = get_embedding(selected_text)
            # Search in Qdrant for similar content to the selected text
            sel_hits = qdrant_client.search(
                collection_name=collection_name,
                query_vector=sel_emb,
                limit=8,  # Higher limit for selected text priority
                with_payload=True
            )
            for hit in sel_hits:
                all_results.append({
                    "text": hit.payload.get("text", ""),
                    "filename": hit.payload.get("filename", "unknown"),
                    "score": hit.score,
                    "priority": "selected"
                })
        except Exception as e:
            # Try the newer query_points method if search fails
            try:
                sel_hits = qdrant_client.query_points(
                    collection_name=collection_name,
                    query=sel_emb,
                    limit=8,  # Higher limit for selected text priority
                    with_payload=True
                ).points
                for hit in sel_hits:
                    all_results.append({
                        "text": hit.payload.get("text", ""),
                        "filename": hit.payload.get("filename", "unknown"),
                        "score": getattr(hit, 'score', getattr(hit, 'distance', 0)),  # Handle both old and new API
                        "priority": "selected"
                    })
            except Exception as e2:
                logger.warning(f"Error processing selected text embedding: {e}, {e2}")

    # Priority 2: Main query
    try:
        query_emb = get_embedding(query)
        # Search in Qdrant for similar content to the query
        query_hits = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_emb,
            limit=10,
            with_payload=True
        )
    except Exception as e:
        # Try the newer query_points method if search fails
        try:
            query_hits = qdrant_client.query_points(
                collection_name=collection_name,
                query=query_emb,
                limit=10,
                with_payload=True
            ).points
        except Exception as e2:
            logger.error(f"Error processing query embedding: {e}, {e2}")
            return "Error: Unable to process the query. API quota may be exceeded or service unavailable."

    for hit in query_hits:
        text = hit.payload.get("text", "")
        filename = hit.payload.get("filename", "unknown")
        # Avoid duplicates
        if not any(r["text"] == text for r in all_results):
            all_results.append({
                "text": text,
                "filename": filename,
                "score": getattr(hit, 'score', getattr(hit, 'distance', 0)),  # Handle both old and new API
                "priority": "query"
            })

    if not all_results:
        return "No relevant content found in the book."

    # Sort: selected text first, then by score
    all_results.sort(key=lambda x: (x["priority"] != "selected", -x["score"]))

    formatted = []
    sources = set()
    for r in all_results:
        formatted.append(f"[Source: {r['filename']}]\n{r['text']}\n")
        sources.add(r['filename'])

    context = "\n\n".join(formatted)
    sources_str = ", ".join(sorted(sources))

    return f"{context}\n\nSources: {sources_str}"