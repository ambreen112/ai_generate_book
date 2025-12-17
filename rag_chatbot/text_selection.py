"""
Text selection utilities for the RAG Chatbot
Handles processing of user-selected text for focused Q&A
"""
from typing import Optional, List, Dict, Any
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re


class TextSelectionProcessor:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize the text selection processor
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embeddings = OpenAIEmbeddings()

        # Initialize text splitter for processing selected text
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )

    def process_selected_text(self, selected_text: str, context_window: int = 200) -> List[Document]:
        """
        Process the user-selected text and create documents with surrounding context
        """
        if not selected_text.strip():
            return []

        # Clean up the selected text
        cleaned_text = self._clean_text(selected_text)

        # Create a document with the selected text
        doc = Document(
            page_content=cleaned_text,
            metadata={
                "source": "user_selection",
                "type": "selected_text"
            }
        )

        # If the text is large, split it into chunks
        if len(cleaned_text) > self.chunk_size:
            chunks = self.text_splitter.split_documents([doc])
            return chunks
        else:
            return [doc]

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize the selected text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text

    def enhance_with_context(self, selected_text: str, surrounding_text: Optional[str] = None) -> str:
        """
        Enhance the selected text with surrounding context
        """
        if not surrounding_text:
            return selected_text

        # Find the selected text in the surrounding text and extract a larger context window
        selected_clean = self._clean_text(selected_text)
        surrounding_clean = self._clean_text(surrounding_text)

        # Try to find the selected text in the surrounding text
        start_idx = surrounding_clean.lower().find(selected_clean.lower())
        if start_idx != -1:
            # Calculate context window around the selected text
            context_start = max(0, start_idx - 200)
            context_end = min(len(surrounding_clean), start_idx + len(selected_clean) + 200)
            context = surrounding_clean[context_start:context_end]
            return context
        else:
            # If not found directly, return selected text with beginning of surrounding text
            return f"{selected_clean}...\n\nFor broader context: {surrounding_clean[:500]}..."

    def create_rich_context(self, selected_text: str, related_chunks: List[Document]) -> str:
        """
        Create a rich context combining selected text with related chunks
        """
        parts = []

        # Add the selected text as the primary context
        if selected_text:
            parts.append(f"USER SELECTED TEXT:\n{selected_text}")

        # Add related chunks as supporting context
        for i, chunk in enumerate(related_chunks):
            parts.append(f"RELATED CONTEXT {i+1}:\n{chunk.page_content}")

        return "\n\n" + "\n\n".join(parts) + "\n\n"


# Global instance
_text_selection_processor = None

def get_text_selection_processor() -> TextSelectionProcessor:
    """
    Get or create the text selection processor instance
    """
    global _text_selection_processor
    if _text_selection_processor is None:
        _text_selection_processor = TextSelectionProcessor()
    return _text_selection_processor


def process_user_selection(selected_text: str, context_window: int = 200) -> List[Document]:
    """
    Convenience function to process user-selected text
    """
    processor = get_text_selection_processor()
    return processor.process_selected_text(selected_text, context_window)


def enhance_selection_with_context(selected_text: str, surrounding_text: Optional[str] = None) -> str:
    """
    Convenience function to enhance selected text with context
    """
    processor = get_text_selection_processor()
    return processor.enhance_with_context(selected_text, surrounding_text)


if __name__ == "__main__":
    # Example usage
    processor = TextSelectionProcessor()

    # Example selected text
    selected = "The theory of relativity fundamentally changed our understanding of space and time."
    docs = processor.process_selected_text(selected)

    print("Processed selected text:")
    for doc in docs:
        print(f"- {doc.page_content}")
        print(f"  Metadata: {doc.metadata}")