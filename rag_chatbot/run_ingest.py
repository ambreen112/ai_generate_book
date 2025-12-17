#!/usr/bin/env python3
"""
Script to run the document ingestion pipeline for the RAG Chatbot
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ingest_pipeline import get_ingestor, ingest_file, ingest_directory, ingest_text
from database import init_db
from models import Book
from database import get_db

def create_book(title: str, author: str, description: str = "") -> int:
    """Create a new book entry in the database"""
    db_gen = get_db()
    db = next(db_gen)

    try:
        book = Book(
            title=title,
            author=author,
            description=description
        )
        db.add(book)
        db.commit()
        db.refresh(book)
        print(f"Created book: {title} (ID: {book.id})")
        return book.id
    finally:
        db.close()
        next(db_gen, None)  # Close the generator

def main():
    print("RAG Chatbot - Document Ingestion Pipeline")
    print("=" * 50)

    # Initialize the database
    print("Initializing database...")
    init_db()

    # Get user input for the ingestion method
    print("\nChoose ingestion method:")
    print("1. Single file")
    print("2. Directory")
    print("3. Raw text")

    choice = input("\nEnter your choice (1-3): ").strip()

    if choice == "1":
        file_path = input("Enter the path to the file: ").strip()
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} does not exist")
            return

        book_choice = input("Do you want to associate this with an existing book? (y/n): ").strip().lower()
        book_id = None

        if book_choice == 'y':
            book_id_input = input("Enter book ID (or press Enter to create a new book): ").strip()
            if book_id_input:
                book_id = int(book_id_input)
            else:
                title = input("Enter book title: ").strip()
                author = input("Enter author name: ").strip()
                description = input("Enter book description (optional): ").strip()
                book_id = create_book(title, author, description)

        print(f"\nIngesting file: {file_path}")
        if book_id:
            print(f"Associating with book ID: {book_id}")

        chunks_count = ingest_file(file_path, book_id)
        print(f"\nSuccessfully ingested {chunks_count} chunks from {file_path}")

    elif choice == "2":
        directory_path = input("Enter the path to the directory: ").strip()
        if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
            print(f"Error: Directory {directory_path} does not exist")
            return

        book_choice = input("Do you want to associate these files with an existing book? (y/n): ").strip().lower()
        book_id = None

        if book_choice == 'y':
            book_id_input = input("Enter book ID (or press Enter to create a new book): ").strip()
            if book_id_input:
                book_id = int(book_id_input)
            else:
                title = input("Enter book title: ").strip()
                author = input("Enter author name: ").strip()
                description = input("Enter book description (optional): ").strip()
                book_id = create_book(title, author, description)

        print(f"\nIngesting directory: {directory_path}")
        if book_id:
            print(f"Associating with book ID: {book_id}")

        chunks_count = ingest_directory(directory_path, book_id)
        print(f"\nSuccessfully ingested {chunks_count} chunks from {directory_path}")

    elif choice == "3":
        content = input("Enter the text content: ").strip()
        if not content:
            print("Error: No content provided")
            return

        source = input("Enter source name (optional, defaults to 'manual_input'): ").strip()
        if not source:
            source = "manual_input"

        book_choice = input("Do you want to associate this with an existing book? (y/n): ").strip().lower()
        book_id = None

        if book_choice == 'y':
            book_id_input = input("Enter book ID (or press Enter to create a new book): ").strip()
            if book_id_input:
                book_id = int(book_id_input)
            else:
                title = input("Enter book title: ").strip()
                author = input("Enter author name: ").strip()
                description = input("Enter book description (optional): ").strip()
                book_id = create_book(title, author, description)

        print(f"\nIngesting text content from: {source}")
        if book_id:
            print(f"Associating with book ID: {book_id}")

        chunks_count = ingest_text(content, source, book_id)
        print(f"\nSuccessfully ingested {chunks_count} chunks from text content")

    else:
        print("Invalid choice. Please run the script again and choose 1, 2, or 3.")
        return

    print("\nDocument ingestion completed successfully!")
    print("The content is now available for question answering through the RAG system.")

if __name__ == "__main__":
    main()