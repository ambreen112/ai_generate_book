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


def embed(text):
    """Create embedding for text using Cohere"""
    response = cohere_client.embed(
        model=EMBED_MODEL,
        input_type="search_query",  # Use search_query for queries
        texts=[text],
    )
    return response.embeddings[0]  # Return the first embedding


def search_chunks(query, top_k=5):
    """
    Search for relevant chunks based on a query using vector similarity

    Args:
        query (str): The search query
        top_k (int): Number of top results to return

    Returns:
        list: Top matching chunks with similarity scores
    """
    # Create embedding for the query
    query_embedding = embed(query)

    # Perform vector search - using the query_points method which accepts vectors
    search_results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,  # Pass the embedding vector directly
        limit=top_k,
        with_payload=True
    )

    results = []
    # Access the points from the response
    for result in search_results.points:
        chunk_data = {
            "chunk_id": result.payload.get("chunk_id"),
            "url": result.payload.get("url"),
            "text": result.payload.get("text"),
            "score": result.score,
            "id": result.id
        }
        results.append(chunk_data)

    return results


def generate_answer(query, context_chunks):
    """
    Generate an answer based on the query and relevant context chunks

    Args:
        query (str): The user's question
        context_chunks (list): List of relevant context chunks

    Returns:
        str: Generated answer
    """
    # Combine all relevant context chunks
    context_text = ""
    for chunk in context_chunks:
        context_text += chunk['text'] + "\n\n"

    # Create a message for the chat model
    message = f"""
    Answer the following question based on the provided context.
    If the answer is not available in the context, please say so.

    Context:
    {context_text}

    Question: {query}

    Answer:"""

    # Use Cohere's chat API to generate the answer
    response = cohere_client.chat(
        message=message,
        max_tokens=500,
        temperature=0.3
    )

    return response.text.strip()


def chatbot_response(user_query):
    """
    Main function to process user query and return a response

    Args:
        user_query (str): The user's question

    Returns:
        str: The chatbot's response
    """
    print(f"Searching for relevant information for query: '{user_query}'")

    # Search for relevant chunks in Qdrant
    relevant_chunks = search_chunks(user_query, top_k=5)

    if not relevant_chunks:
        return "I couldn't find any relevant information in the knowledge base to answer your question."

    print(f"Found {len(relevant_chunks)} relevant chunks")

    # Generate an answer using the relevant chunks
    answer = generate_answer(user_query, relevant_chunks)

    # Add source information
    sources = set([chunk['url'] for chunk in relevant_chunks])
    source_text = f"\n\nSources: {', '.join(list(sources)[:3])}"  # Limit to first 3 sources

    return answer + source_text


def run_chatbot():
    """
    Run the interactive chatbot
    """
    print("🤖 Qdrant-powered Chatbot")
    print("=" * 40)
    print("Ask me anything about your book content!")
    print("Type 'quit' to exit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Chatbot: Goodbye! 👋")
            break

        if not user_input:
            continue

        try:
            response = chatbot_response(user_input)
            print(f"Chatbot: {response}\n")
        except Exception as e:
            print(f"Chatbot: Sorry, I encountered an error: {str(e)}\n")


def test_chatbot():
    """
    Test the chatbot functionality with sample queries
    """
    print("Testing chatbot functionality...")

    sample_queries = [
        "What is this book about?",
        "Tell me about the blog features",
        "What is Docusaurus?"
    ]

    for query in sample_queries:
        print(f"\nQuery: {query}")
        response = chatbot_response(query)
        print(f"Response: {response[:200]}...")  # Truncate for display
        print("-" * 50)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_chatbot()
    else:
        run_chatbot()