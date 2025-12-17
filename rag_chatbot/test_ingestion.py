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

def get_all_urls(sitemap_url):
    xml = requests.get(sitemap_url).text
    root = ET.fromstring(xml)

    urls = []
    for child in root:
        loc_tag = child.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
        if loc_tag is not None:
            urls.append(loc_tag.text)

    print("\nFOUND URLS:")
    for u in urls:
        print(" -", u)

    return urls

def extract_text_from_url(url):
    html = requests.get(url).text
    text = trafilatura.extract(html)

    if not text:
        print("[WARNING] No text extracted from:", url)

    return text

def chunk_text(text, max_chars=1200):
    chunks = []
    while len(text) > max_chars:
        split_pos = text[:max_chars].rfind(". ")
        if split_pos == -1:
            split_pos = max_chars
        chunks.append(text[:split_pos])
        text = text[split_pos:]
    chunks.append(text)
    return chunks

def embed(text):
    response = cohere_client.embed(
        model=EMBED_MODEL,
        input_type="search_query",
        texts=[text],
    )
    return response.embeddings[0]

def create_collection():
    print("\nCreating Qdrant collection...")
    qdrant_client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=1024,
            distance=Distance.COSINE
        )
    )

def save_chunk_to_qdrant(chunk, chunk_id, url):
    vector = embed(chunk)

    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=chunk_id,
                vector=vector,
                payload={
                    "url": url,
                    "text": chunk,
                    "chunk_id": chunk_id
                }
            )
        ]
    )

def ingest_book():
    urls = get_all_urls(SITEMAP_URL)

    create_collection()

    global_id = 1

    for url in urls:
        print("\nProcessing:", url)
        text = extract_text_from_url(url)

        if not text:
            continue

        chunks = chunk_text(text)

        for ch in chunks:
            save_chunk_to_qdrant(ch, global_id, url)
            print(f"Saved chunk {global_id}")
            global_id += 1

    print("\n✔️ Ingestion completed!")
    print("Total chunks stored:", global_id - 1)

def extract_chunks_from_qdrant(batch_size=10):
    """
    Extract all chunks from Qdrant collection in batches
    """
    print(f"\nExtracting data from Qdrant collection: {COLLECTION_NAME}")

    # Get total count of points in the collection
    collection_info = qdrant_client.get_collection(collection_name=COLLECTION_NAME)
    total_points = collection_info.points_count
    print(f"Total points in collection: {total_points}")

    if total_points == 0:
        print("Collection is empty!")
        return []

    all_chunks = []

    # Fetch points in batches
    offset = 0
    while offset < total_points:
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

        print(f"Fetched {len(all_chunks)}/{total_points} chunks...")

        if next_offset is None:
            break
        offset = next_offset

    print(f"\n✔️ Extraction completed! Total chunks retrieved: {len(all_chunks)}")
    return all_chunks

# Run ingestion
if __name__ == "__main__":
    print("Starting ingestion process...")
    ingest_book()

    print("\nVerifying ingestion by extracting some chunks...")
    chunks = extract_chunks_from_qdrant(batch_size=5)
    print(f"Successfully extracted {len(chunks)} chunks for verification")