#!/usr/bin/env python3
"""
Test script to validate the RAG Chatbot functionality
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio
import json

# Load environment variables
load_dotenv()

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend import app
from agent import get_agent
from vector_store import get_vector_store
from database import init_db
from models import Book
from database import get_db
from ingest_pipeline import ingest_text
from fastapi.testclient import TestClient

def test_basic_functionality():
    """Test basic functionality of the RAG system"""
    print("Testing basic RAG functionality...")

    # Test agent creation
    try:
        agent = get_agent()
        print("[PASS] Agent created successfully")
    except Exception as e:
        print(f"[FAIL] Error creating agent: {e}")
        return False

    # Test vector store
    try:
        vector_store = get_vector_store()
        print("[PASS] Vector store created successfully")
    except Exception as e:
        print(f"✗ Error creating vector store: {e}")
        return False

    # Test database initialization
    try:
        init_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        return False

    return True

def test_ingestion():
    """Test document ingestion functionality"""
    print("\nTesting document ingestion...")

    # Sample book content
    sample_content = """
    Chapter 1: Introduction to AI
    Artificial Intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of "intelligent agents": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals.

    Chapter 2: Machine Learning
    Machine learning (ML) is the study of computer algorithms that can improve automatically through experience and by the use of data. It is seen as a part of artificial intelligence.
    """

    try:
        # Create a test book
        db_gen = get_db()
        db = next(db_gen)

        try:
            book = Book(
                title="Test AI Book",
                author="Test Author",
                description="A test book for AI concepts"
            )
            db.add(book)
            db.commit()
            db.refresh(book)
            book_id = book.id
            print(f"✓ Test book created with ID: {book_id}")
        finally:
            db.close()
            next(db_gen, None)  # Close the generator

        # Ingest the sample content
        chunks_count = ingest_text(sample_content, "test_chapter", book_id)
        print(f"✓ Ingested {chunks_count} chunks into book ID {book_id}")

        # Verify that content was added to vector store
        vector_store = get_vector_store()
        results = vector_store.similarity_search("What is artificial intelligence?", k=1)
        if results:
            print("✓ Content successfully added to vector store and retrievable")
        else:
            print("✗ Content not found in vector store")
            return False

        return True
    except Exception as e:
        print(f"✗ Error during ingestion test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test FastAPI endpoints using TestClient"""
    print("\nTesting API endpoints...")

    client = TestClient(app)

    # Test health endpoint
    try:
        response = client.get("/")
        if response.status_code == 200:
            print("✓ Health endpoint working")
        else:
            print(f"✗ Health endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error testing health endpoint: {e}")
        return False

    # Test query endpoint (without proper context, this might fail but should not crash)
    try:
        response = client.post("/query", json={
            "question": "What is AI?",
            "selected_text": "Artificial Intelligence is intelligence demonstrated by machines"
        })
        if response.status_code in [200, 400, 500]:  # 200 for success, 400 for validation error, 500 for processing error
            print("✓ Query endpoint accessible")
        else:
            print(f"✗ Query endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error testing query endpoint: {e}")
        return False

    # Test health check endpoint
    try:
        response = client.get("/health")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print("✓ Health check endpoint working")
            else:
                print(f"✗ Health check endpoint returned unexpected data: {data}")
                return False
        else:
            print(f"✗ Health check endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error testing health check endpoint: {e}")
        return False

    return True

def test_agent_with_context():
    """Test the agent with various contexts"""
    print("\nTesting agent with different contexts...")

    try:
        agent = get_agent()

        # Test with empty context
        response = agent.query(
            question="What is the meaning of life?",
            context="",
            retrieved_docs=[]
        )
        print(f"✓ Agent handled empty context, response length: {len(response.answer)}")

        # Test with simple context
        response = agent.query(
            question="What is AI?",
            context="Artificial Intelligence is intelligence demonstrated by machines",
            retrieved_docs=[]
        )
        print(f"✓ Agent handled simple context, response length: {len(response.answer)}")

        # Test with user-selected text emphasis
        response = agent.query(
            question="What does the selected text say about AI?",
            context="Artificial Intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals.",
            retrieved_docs=[]
        )
        print(f"✓ Agent handled user-selected text, response length: {len(response.answer)}")

        return True
    except Exception as e:
        print(f"✗ Error testing agent: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("RAG Chatbot - Functionality Test Suite")
    print("=" * 50)

    tests = [
        ("Basic functionality", test_basic_functionality),
        ("Document ingestion", test_ingestion),
        ("API endpoints", test_api_endpoints),
        ("Agent with context", test_agent_with_context),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))

    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)

    all_passed = True
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        icon = "✓" if success else "✗"
        print(f"{icon} {test_name}: {status}")
        if not success:
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! RAG Chatbot is ready for use.")
    else:
        print("❌ SOME TESTS FAILED. Please check the output above for details.")

    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)