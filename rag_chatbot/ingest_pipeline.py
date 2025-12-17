"""
Document ingestion pipeline for the RAG Chatbot
Handles loading, processing, and storing book content in both database and vector store
"""
from typing import List, Optional, Tuple
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader, PDFPlumberLoader, Docx2txtLoader, UnstructuredMarkdownLoader
)
from langchain_community.document_loaders.base import BaseLoader
import os
from pathlib import Path
import tempfile
from database import get_db
from models import Book, Chapter, Chunk
from vector_store import get_vector_store
import models
from sqlalchemy.orm import Session


class DocumentIngestor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, use_gemini: bool = False):
        """
        Initialize the document ingestor
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.use_gemini = use_gemini

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )

    def _get_loader_for_file(self, file_path: str) -> BaseLoader:
        """
        Get appropriate loader based on file extension
        """
        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.pdf':
            return PDFPlumberLoader(file_path)
        elif file_ext in ['.doc', '.docx']:
            return Docx2txtLoader(file_path)
        elif file_ext == '.txt':
            return TextLoader(file_path, encoding='utf-8')
        elif file_ext in ['.md', '.markdown']:
            return UnstructuredMarkdownLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}. "
                           f"Supported types: .pdf, .doc, .docx, .txt, .md, .markdown")

    def load_document(self, file_path: str) -> List[Document]:
        """
        Load a document from the given file path
        """
        loader = self._get_loader_for_file(file_path)
        documents = loader.load()
        return documents

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks
        """
        chunks = self.text_splitter.split_documents(documents)
        return chunks

    def process_file(self, file_path: str, book_id: Optional[int] = None) -> Tuple[int, List[Document]]:
        """
        Process a file: load, split, and store in both database and vector store
        """
        # Load the document
        documents = self.load_document(file_path)

        # Split into chunks
        chunks = self.split_documents(documents)

        # Add to vector store
        vector_store = get_vector_store(use_gemini=self.use_gemini)
        vector_store.add_documents(chunks)

        # If a book_id is provided, also store in the database
        if book_id:
            # Use a database session
            db_gen = get_db()
            db = next(db_gen)

            try:
                # Get the book from the database
                book = db.query(Book).filter(Book.id == book_id).first()
                if not book:
                    raise ValueError(f"Book with id {book_id} not found")

                # Create a chapter for this document
                chapter = Chapter(
                    book_id=book_id,
                    title=Path(file_path).name,
                    content="\n".join([doc.page_content for doc in chunks]),
                    chapter_number=len(book.chapters) + 1
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
            finally:
                db.close()
                # Close the generator
                next(db_gen, None)  # This will trigger the finally block in the generator

        return len(chunks), chunks

    def process_directory(self, directory_path: str, book_id: Optional[int] = None) -> int:
        """
        Process all supported documents in a directory
        """
        supported_extensions = ['.pdf', '.doc', '.docx', '.txt', '.md', '.markdown']
        total_chunks = 0

        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_ext = Path(file).suffix.lower()
                if file_ext in supported_extensions:
                    file_path = os.path.join(root, file)
                    chunks_count, _ = self.process_file(file_path, book_id)
                    total_chunks += chunks_count
                    print(f"Processed {file} - {chunks_count} chunks")

        return total_chunks

    def process_text_content(self, content: str, source: str = "manual_input", book_id: Optional[int] = None) -> Tuple[int, List[Document]]:
        """
        Process raw text content directly
        """
        # Create a document from the text content
        doc = Document(page_content=content, metadata={"source": source})

        # Split into chunks
        chunks = self.split_documents([doc])

        # Add to vector store
        vector_store = get_vector_store()
        vector_store.add_documents(chunks)

        # If a book_id is provided, also store in the database
        if book_id:
            # Use a database session
            db_gen = get_db()
            db = next(db_gen)

            try:
                # Get the book from the database
                book = db.query(Book).filter(Book.id == book_id).first()
                if not book:
                    raise ValueError(f"Book with id {book_id} not found")

                # Create a chapter for this content
                chapter = Chapter(
                    book_id=book_id,
                    title=source,
                    content=content,
                    chapter_number=len(book.chapters) + 1
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
            finally:
                db.close()
                # Close the generator
                next(db_gen, None)  # This will trigger the finally block in the generator

        return len(chunks), chunks


# Global instance
_ingestor = None

def get_ingestor() -> DocumentIngestor:
    """
    Get or create the document ingestor instance
    """
    global _ingestor
    if _ingestor is None:
        _ingestor = DocumentIngestor()
    return _ingestor


# Convenience functions
def ingest_file(file_path: str, book_id: Optional[int] = None) -> int:
    """
    Convenience function to ingest a single file
    """
    ingestor = get_ingestor()
    chunks_count, _ = ingestor.process_file(file_path, book_id)
    return chunks_count


def ingest_directory(directory_path: str, book_id: Optional[int] = None) -> int:
    """
    Convenience function to ingest all files in a directory
    """
    ingestor = get_ingestor()
    return ingestor.process_directory(directory_path, book_id)


def ingest_text(content: str, source: str = "manual_input", book_id: Optional[int] = None) -> int:
    """
    Convenience function to ingest raw text content
    """
    ingestor = get_ingestor()
    chunks_count, _ = ingestor.process_text_content(content, source, book_id)
    return chunks_count


if __name__ == "__main__":
    # Example usage
    print("Document Ingestion Pipeline")
    print("This module provides tools to load, process, and store book content.")
    print("Use get_ingestor() to get an instance, or the convenience functions:")
    print("- ingest_file(file_path, book_id)")
    print("- ingest_directory(directory_path, book_id)")
    print("- ingest_text(content, source, book_id)")