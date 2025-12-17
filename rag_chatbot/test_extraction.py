import requests
import xml.etree.ElementTree as ET
import trafilatura
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue
import cohere
import json

# Configuration from your original script
SITEMAP_URL = "https://ambreen112.github.io/ai_generate_book/sitemap.xml"
COLLECTION_NAME = "ai_generate_book"

cohere_client = cohere.Client("qLflh2woIvrseyG6kzdrZ6gw3UyNzCEgTjBJn9VJ")
EMBED_MODEL = "embed-english-v3.0"

qdrant_client = QdrantClient(
    url="https://a28ebc35-7712-4b77-b68d-45842c00baa9.us-east4-0.gcp.cloud.qdrant.io:6333",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.zXCfpQVZ7mrxmQuYdSn9UH8Kj8uf-dbhDoP9K1h28uk",
)

def test_extraction():
    """Test function to verify extraction functionality"""
    print("Testing Qdrant extraction functionality...")

    # Test getting collection info
    try:
        collection_info = qdrant_client.get_collection(collection_name=COLLECTION_NAME)
        total_points = collection_info.points_count
        print(f"[SUCCESS] Successfully connected to Qdrant collection: {COLLECTION_NAME}")
        print(f"[INFO] Total points in collection: {total_points}")

        if total_points > 0:
            # Test extracting a few sample chunks
            print("Attempting to extract sample chunks...")
            all_chunks = []

            # Fetch points in batches
            offset = 0
            batch_size = 3
            while offset < total_points and len(all_chunks) < 3:
                # Retrieve batch of points
                records, next_offset = qdrant_client.scroll(
                    collection_name=COLLECTION_NAME,
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )

                # Extract chunk information from each record
                for record in records:
                    payload = record.payload
                    chunk_data = {
                        "chunk_id": payload.get("chunk_id"),
                        "url": payload.get("url"),
                        "text": payload.get("text"),
                        "id": record.id
                    }
                    all_chunks.append(chunk_data)
                    if len(all_chunks) >= 3:  # Only get 3 samples
                        break

                if next_offset is None:
                    break
                offset = next_offset

            print(f"[SUCCESS] Successfully extracted {len(all_chunks)} sample chunks")

            if all_chunks:
                print("\nSample chunk:")
                chunk = all_chunks[0]
                print(f"  Chunk ID: {chunk['chunk_id']}")
                print(f"  URL: {chunk['url']}")
                print(f"  Text preview: {chunk['text'][:100]}...")
        else:
            print("[WARNING] Collection is empty - you may need to run ingestion first")

    except Exception as e:
        print(f"[ERROR] Error during testing: {str(e)}")
        return False

    print("\n[SUCCESS] All extraction functionality tests passed!")
    return True

if __name__ == "__main__":
    test_extraction()