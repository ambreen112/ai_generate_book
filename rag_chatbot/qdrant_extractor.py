import requests
import xml.etree.ElementTree as ET
import trafilatura
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue
import cohere
import json

# -------------------------------------
# CONFIG
# -------------------------------------
# Your Deployment Link:
SITEMAP_URL = "https://ambreen112.github.io/ai_generate_book/sitemap.xml"
COLLECTION_NAME = "ai_generate_book"

cohere_client = cohere.Client("qLflh2woIvrseyG6kzdrZ6gw3UyNzCEgTjBJn9VJ")
EMBED_MODEL = "embed-english-v3.0"

qdrant_client = QdrantClient(
    url="https://a28ebc35-7712-4b77-b68d-45842c00baa9.us-east4-0.gcp.cloud.qdrant.io:6333",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.zXCfpQVZ7mrxmQuYdSn9UH8Kj8uf-dbhDoP9K1h28uk",
)


# -------------------------------------
# Step 1 — Extract URLs from sitemap
# -------------------------------------
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


# -------------------------------------
# Step 2 — Download page + extract text
# -------------------------------------
def extract_text_from_url(url):
    html = requests.get(url).text
    text = trafilatura.extract(html)

    if not text:
        print("[WARNING] No text extracted from:", url)

    return text


# -------------------------------------
# Step 3 — Chunk the text
# -------------------------------------
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


# -------------------------------------
# Step 4 — Create embedding
# -------------------------------------
def embed(text):
    response = cohere_client.embed(
        model=EMBED_MODEL,
        input_type="search_query",  # Use search_query for queries
        texts=[text],
    )
    return response.embeddings[0]  # Return the first embedding


# -------------------------------------
# Step 5 — Store in Qdrant
# -------------------------------------
def create_collection():
    print("\nCreating Qdrant collection...")
    qdrant_client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
        size=1024,        # Cohere embed-english-v3.0 dimension
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


# -------------------------------------
# MAIN INGESTION PIPELINE
# -------------------------------------
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


# -------------------------------------
# EXTRACTION FUNCTIONS
# -------------------------------------
def extract_chunks_from_qdrant(batch_size=10):
    """
    Extract all chunks from Qdrant collection in batches

    Args:
        batch_size (int): Number of chunks to fetch per batch

    Returns:
        list: All chunks extracted from Qdrant
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


def extract_chunks_by_url(target_url):
    """
    Extract all chunks associated with a specific URL

    Args:
        target_url (str): The URL to filter chunks for

    Returns:
        list: Chunks associated with the specified URL
    """
    print(f"\nExtracting chunks for URL: {target_url}")

    # Search for points with specific URL in payload
    records, _ = qdrant_client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="url",
                    match=MatchValue(value=target_url),
                ),
            ],
        ),
        with_payload=True,
        with_vectors=False
    )

    chunks = []
    for record in records:
        payload = record.payload
        chunk_data = {
            "chunk_id": payload.get("chunk_id"),
            "url": payload.get("url"),
            "text": payload.get("text"),
            "id": record.id
        }
        chunks.append(chunk_data)

    print(f"Found {len(chunks)} chunks for URL: {target_url}")
    return chunks


def print_sample_chunks(num_chunks=5):
    """
    Print a sample of chunks from the Qdrant collection

    Args:
        num_chunks (int): Number of sample chunks to print
    """
    print(f"\nSample of {num_chunks} chunks from Qdrant:")
    print("-" * 50)

    all_chunks = extract_chunks_from_qdrant(batch_size=num_chunks)

    for i, chunk in enumerate(all_chunks[:num_chunks]):
        print(f"Chunk {i+1}:")
        print(f"  ID: {chunk['chunk_id']}")
        print(f"  URL: {chunk['url']}")
        print(f"  Text preview: {chunk['text'][:100]}...")
        print("-" * 30)


def search_chunks(query, top_k=5):
    """
    Search for relevant chunks based on a query using vector similarity

    Args:
        query (str): The search query
        top_k (int): Number of top results to return

    Returns:
        list: Top matching chunks with similarity scores
    """
    print(f"\nSearching for: '{query}'")

    # Create embedding for the query
    query_embedding = embed(query)

    # Perform vector search
    search_results = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding,
        limit=top_k,
        with_payload=True
    )

    results = []
    for result in search_results:
        chunk_data = {
            "chunk_id": result.payload.get("chunk_id"),
            "url": result.payload.get("url"),
            "text": result.payload.get("text"),
            "score": result.score,
            "id": result.id
        }
        results.append(chunk_data)

    print(f"Found {len(results)} relevant chunks")
    return results


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
            sample_chunks = extract_chunks_from_qdrant(batch_size=3)
            print(f"[SUCCESS] Successfully extracted {len(sample_chunks)} sample chunks")

            if sample_chunks:
                print("\nSample chunk:")
                chunk = sample_chunks[0]
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
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run automated test when --test flag is provided
        test_extraction()
    else:
        print("Qdrant Data Extraction Tool")
        print("=" * 30)
        print("Choose an option:")
        print("1. Extract all chunks from Qdrant")
        print("2. Extract chunks for a specific URL")
        print("3. Print sample chunks")
        print("4. Search chunks with a query")
        print("5. Run ingestion pipeline")

        choice = input("Enter your choice (1-5): ").strip()

        if choice == "1":
            all_chunks = extract_chunks_from_qdrant()
            print(f"Retrieved {len(all_chunks)} total chunks")
            # Optionally save to file
            save_option = input("Save chunks to JSON file? (y/n): ").strip().lower()
            if save_option == "y":
                with open('extracted_chunks.json', 'w', encoding='utf-8') as f:
                    json.dump(all_chunks, f, indent=2, ensure_ascii=False)
                print("Chunks saved to 'extracted_chunks.json'")

        elif choice == "2":
            url_to_search = input("Enter the URL to search for: ").strip()
            chunks_for_url = extract_chunks_by_url(url_to_search)
            for i, chunk in enumerate(chunks_for_url):
                print(f"\nChunk {i+1}:")
                print(f"  Chunk ID: {chunk['chunk_id']}")
                print(f"  URL: {chunk['url']}")
                print(f"  Text: {chunk['text'][:500]}...")
                print("-" * 50)

        elif choice == "3":
            num_samples = input("How many sample chunks to display? (default 5): ").strip()
            num_samples = int(num_samples) if num_samples.isdigit() else 5
            print_sample_chunks(num_samples)

        elif choice == "4":
            query = input("Enter your search query: ").strip()
            top_k = input("How many results to return? (default 5): ").strip()
            top_k = int(top_k) if top_k.isdigit() else 5
            results = search_chunks(query, top_k)
            for i, result in enumerate(results):
                print(f"\nResult {i+1} (Score: {result['score']:.3f}):")
                print(f"  URL: {result['url']}")
                print(f"  Text: {result['text'][:300]}...")
                print("-" * 50)

        elif choice == "5":
            confirm = input("This will recreate the collection. Continue? (y/n): ").strip().lower()
            if confirm == "y":
                ingest_book()
            else:
                print("Ingestion cancelled.")

        else:
            print("Invalid choice. Exiting.")