# RAG Chatbot for Docusaurus Book

This project integrates a Retrieval-Augmented Generation (RAG) chatbot into a Docusaurus book site, allowing users to ask questions about the book content with support for selected/highlighted text priority.

## Features

- **Floating Chat Widget**: A chat interface that appears on every page of your Docusaurus site
- **Text Selection Priority**: Automatically captures selected text and prioritizes it in responses
- **OpenRouter Integration**: Uses OpenRouter for both embeddings and chat completion
- **Qdrant Vector Storage**: Efficient vector storage and retrieval
- **Production-Ready**: Clean, modern code with proper error handling

## Prerequisites

1. **OpenRouter API Key**: Get a free API key from [OpenRouter](https://openrouter.ai/keys)
2. **Qdrant Cloud**: Get a free tier account at [Qdrant](https://qdrant.tech/)
3. **Python 3.8+**
4. **Node.js 16+** (for Docusaurus)

## Setup Instructions

### 1. Backend Setup (rag_chatbot)

1. Navigate to the rag_chatbot directory:
   ```bash
   cd rag_chatbot
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` with your credentials:
   ```bash
   # Get your OpenRouter API key from https://openrouter.ai/keys
   OPENROUTER_API_KEY=your_openrouter_api_key_here

   # Get your Qdrant credentials from Qdrant Cloud
   QDRANT_URL=your_qdrant_cluster_url_here
   QDRANT_API_KEY=your_qdrant_api_key_here
   QDRANT_COLLECTION_NAME=book_content
   ```

5. Run the ingestion script to index your book content:
   ```bash
   python ingest.py
   ```
   This will recursively load all `.md` files from `../book-site/docs`, chunk them, embed them using OpenRouter's `text-embedding-3-small` model (1536 dimensions), and store them in Qdrant.

6. Start the FastAPI backend:
   ```bash
   python main.py
   ```
   The backend will run on `http://localhost:8000`

### 2. Frontend Setup (book-site)

1. Navigate to the book-site directory:
   ```bash
   cd book-site
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Docusaurus development server:
   ```bash
   npm run start
   ```
   The site will run on `http://localhost:3000`

## How It Works

1. **Ingestion**: The `inggest.py` script reads all `.md` files from the Docusaurus docs directory, chunks them, and stores them in Qdrant with 1536-dimensional embeddings using OpenRouter's `text-embedding-3-small` model.

2. **Retrieval**: The `vector_store.py` provides a `retrieve` function that searches Qdrant for relevant content based on the user's query and selected text.

3. **Agent**: The `agent.py` uses OpenRouter's `gpt-4o-mini` model with strict instructions to always call the retrieve function first and prioritize selected text.

4. **Frontend**: The `RAGChatWidget.tsx` component captures selected text on mouseup events and sends queries to the backend API.

## API Endpoints

- `GET /` - Health check
- `GET /health` - Health check
- `POST /query` - Query the RAG system (JSON: `{"question": "text", "selected_text": "optional text"}`)
- `GET /query` - Query via query parameters

## Vector Dimensions

- **Embedding Model**: OpenRouter `openai/text-embedding-3-small`
- **Dimensions**: 1536
- **Distance Metric**: Cosine similarity

## Rate Limiting

The system includes exponential backoff retry logic for handling rate limits from OpenRouter and Qdrant.

## Customization

- Modify the system prompt in `agent.py` to change the assistant's behavior
- Adjust chunk size and overlap in `ingest.py`
- Customize the chat widget UI in `RAGChatWidget.tsx` and `RAGChatWidget.css`

## Production Deployment

1. **Backend**: Deploy the FastAPI app to a cloud provider (AWS, GCP, Azure, etc.)
2. **Frontend**: Build and deploy the Docusaurus site
3. **Environment**: Update the API endpoint in `RAGChatWidget.tsx` to point to your deployed backend
   - In `RAGChatWidget.tsx`, change the fetch URL from `'http://localhost:8000/query'` to your production backend URL

## Development Notes

- The frontend component is set to call the backend at `http://localhost:8000/query`
- When running locally, ensure the FastAPI backend is running before starting the Docusaurus frontend
- For production, update the API endpoint in the component to match your deployed backend URL
- The chat widget automatically adapts to Docusaurus light/dark mode using CSS theme detection

## Troubleshooting

- **API Key Issues**: Ensure your OpenRouter and Qdrant credentials are correct
- **Vector Dimensions**: The system expects 1536-dimensional vectors from the text-embedding-3-small model
- **CORS**: The backend allows all origins - restrict in production
- **Rate Limits**: The system has built-in retry logic for handling rate limits

## Notes

- The `text-embedding-3-small` model from OpenAI provides 1536-dimensional embeddings
- Selected text is given higher priority in the retrieval process
- The chat widget automatically captures selected text when users release their mouse button
- The system is designed to never hallucinate - it only uses retrieved context