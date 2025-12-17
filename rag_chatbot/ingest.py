"""
Ingest all .md files from the book-site/docs directory into Qdrant vector store
using OpenRouter embeddings.
"""
import os
import asyncio
import time
import random
from pathlib import Path
from typing import List
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.models import PointStruct
from openai import AsyncOpenAI
import logging
from dotenv import load_dotenv
import aiofiles

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenRouter client for embeddings
openrouter_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# Rate limiting parameters
MAX_RETRIES = 5
BASE_DELAY = 1  # seconds
MAX_DELAY = 60  # seconds

async def exponential_backoff_retry(func, *args, **kwargs):
    """
    Execute a function with exponential backoff retry logic for rate limits.
    """
    for attempt in range(MAX_RETRIES):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower() or "rate limit" in str(e).lower():
                if attempt == MAX_RETRIES - 1:  # Last attempt
                    raise e

                # Calculate delay with exponential backoff and jitter
                delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
                jitter = random.uniform(0, delay * 0.1)  # Add 10% jitter
                actual_delay = delay + jitter

                logger.warning(f"Rate limit hit (attempt {attempt + 1}/{MAX_RETRIES}), waiting {actual_delay:.2f}s: {e}")
                await asyncio.sleep(actual_delay)
            else:
                # If it's not a rate limit error, raise immediately
                raise e

async def get_embedding(text: str) -> List[float]:
    """
    Get embedding for a given text using OpenRouter's text-embedding-3-small model (1536 dimensions).

    Args:
        text (str): Text to embed

    Returns:
        List[float]: Embedding vector (1536 dimensions)
    """
    async def _get_openrouter_embedding():
        response = await openrouter_client.embeddings.create(
            model="openai/text-embedding-3-small",  # 1536 dimensions
            input=text
        )
        return response.data[0].embedding

    try:
        return await exponential_backoff_retry(_get_openrouter_embedding)
    except Exception as e:
        logger.error(f"Error getting OpenRouter embedding after {MAX_RETRIES} retries: {e}")
        raise

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Chunk text into smaller pieces with overlap to preserve context.

    Args:
        text (str): Text to chunk
        chunk_size (int): Size of each chunk
        overlap (int): Overlap between chunks

    Returns:
        List[str]: List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # If this isn't the last chunk, try to break at a sentence boundary
        if end < len(text):
            # Look for sentence endings near the end of the chunk
            sentence_end = max(chunk.rfind('.'), chunk.rfind('!'), chunk.rfind('?'))
            if sentence_end > chunk_size // 2:  # Only break if the sentence end is reasonably close to the end
                chunk = text[start:start + sentence_end + 1]
                end = start + sentence_end + 1

        chunks.append(chunk)
        start = end - overlap if end < len(text) else end

    # Remove empty chunks
    return [chunk for chunk in chunks if chunk.strip()]

async def process_md_file(file_path: Path) -> List[PointStruct]:
    """
    Process an MD file and create Qdrant points from its content.

    Args:
        file_path (Path): Path to the MD file

    Returns:
        List[PointStruct]: List of Qdrant points
    """
    logger.info(f"Processing file: {file_path}")

    # Read the MD file
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
        content = await file.read()

    # Chunk the content
    chunks = chunk_text(content)

    # Create points for each chunk
    points = []
    for i, chunk in enumerate(chunks):
        if chunk.strip():  # Skip empty chunks
            embedding = await get_embedding(chunk)
            point = PointStruct(
                id=len(points),  # Use sequential integer ID
                vector=embedding,
                payload={
                    "text": chunk,
                    "filename": file_path.name,
                    "filepath": str(file_path),
                    "chunk_index": i
                }
            )
            points.append(point)

    logger.info(f"Created {len(points)} points from {file_path}")
    return points

async def ingest_docs(docs_folder: str = "../book-site/docs"):
    """
    Ingest all MD files from the specified folder into Qdrant.
    Uses OpenRouter embeddings (text-embedding-3-small) with 1536 dimensions.

    Args:
        docs_folder (str): Path to the folder containing MD files
    """
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "book_content")

    if not collection_name:
        raise ValueError("QDRANT_COLLECTION_NAME environment variable is not set")

    docs_path = Path(docs_folder)
    if not docs_path.exists():
        logger.error(f"Docs folder does not exist: {docs_folder}")
        return

    # Get all MD files recursively from subfolders
    md_files = list(docs_path.rglob("*.md"))
    logger.info(f"Found {len(md_files)} MD files to process (recursive)")

    if not md_files:
        logger.warning("No MD files found in the specified folder and subfolders")
        return

    # Process each file and collect points
    all_points = []
    for md_file in md_files:
        try:
            points = await process_md_file(md_file)
            all_points.extend(points)
        except Exception as e:
            logger.error(f"Error processing file {md_file}: {e}")

    # Initialize Qdrant client
    qdrant_client = AsyncQdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        timeout=30
    )

    # Create collection if it doesn't exist
    try:
        # Try to get the collection to see if it exists
        await qdrant_client.get_collection(collection_name)
        logger.info(f"Collection '{collection_name}' already exists")
    except:
        # Collection doesn't exist, create it with 1536 dimensions for OpenRouter embeddings
        logger.info(f"Creating collection '{collection_name}'")
        await qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)  # OpenRouter text-embedding-3-small: 1536 dimensions
        )
        logger.info(f"Collection '{collection_name}' created successfully with 1536-dimensional vectors")

    # Upsert all points to Qdrant
    if all_points:
        logger.info(f"Upserting {len(all_points)} points to Qdrant collection '{collection_name}'")
        try:
            await qdrant_client.upsert(
                collection_name=collection_name,
                points=all_points,
                wait=True  # Wait for the operation to complete
            )
            logger.info(f"Successfully upserted {len(all_points)} points to Qdrant")
        except Exception as e:
            logger.error(f"Error upserting points to Qdrant: {e}")
            raise
    else:
        logger.warning("No points to upsert - no valid content found in MD files")

async def main():
    """
    Main function to run the ingestion process.
    """
    docs_folder = os.getenv("DOCS_FOLDER", "../book-site/docs")
    await ingest_docs(docs_folder)

if __name__ == "__main__":
    asyncio.run(main())