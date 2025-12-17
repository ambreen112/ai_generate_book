# RAG Chatbot - Document Ingestion Guide

This guide explains how to use the document ingestion functionality of the RAG Chatbot.

## Prerequisites

Before running the ingestion script, make sure you have:

1. Valid API keys in your `.env` file:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `QDRANT_URL`: Your Qdrant Cloud URL
   - `QDRANT_API_KEY`: Your Qdrant API key

2. Required dependencies installed (run from the rag_chatbot directory):
   ```bash
   pip install -r requirements.txt
   ```

## Setting up API Keys

1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your actual API keys:
   ```env
   OPENAI_API_KEY=your_actual_openai_api_key_here
   QDRANT_URL=your_qdrant_url_here
   QDRANT_API_KEY=your_qdrant_api_key_here
   ```

## Using the Ingestion Scripts

### Method 1: Simple Directory Ingestion (`ingest.py`)

For quick ingestion of markdown files from a directory:

```bash
python ingest.py [optional_directory_path]
```

If no directory is specified, it defaults to `../book-site/docs`.

Example:
```bash
python ingest.py ../my_documents
```

This script supports:
- Markdown (.md, .markdown) files

### Method 2: Interactive Ingestion (`run_ingest.py`)

For more flexible ingestion with multiple file types and database integration:

```bash
python run_ingest.py
```

This interactive script allows you to:
- Ingest single files
- Ingest entire directories
- Add raw text content
- Associate documents with books in the database
- Support for multiple file types: .pdf, .doc, .docx, .txt, .md, .markdown

## Supported File Types

- **Directory ingestion (`ingest.py`)**: .md, .markdown
- **Interactive ingestion (`run_ingest.py`)**: .pdf, .doc, .docx, .txt, .md, .markdown

## Troubleshooting

### Common Issues:

1. **API Key Error**: If you see an error about incorrect API key, make sure your `.env` file has valid keys.

2. **Directory Not Found**: Ensure the directory you're trying to ingest from exists and contains supported file types.

3. **Qdrant Connection Error**: Check that your Qdrant URL and API key are correct and that you have internet connectivity.

## How It Works

1. **Loading**: Documents are loaded from the specified source using appropriate loaders
2. **Splitting**: Documents are split into chunks of 1000 characters with 200-character overlap
3. **Embedding**: Text chunks are converted to vector embeddings using OpenAI
4. **Storage**: Embeddings are stored in Qdrant vector database for similarity search
5. **Indexing**: Documents are indexed for fast retrieval during question answering

The ingestion process maintains both vector embeddings for semantic search and database records for metadata management.