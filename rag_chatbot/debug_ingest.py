import asyncio
import logging
from pathlib import Path
from ingest import process_mdx_file, get_embedding

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_ingest():
    docs_path = Path("../book-site/docs")
    md_files = list(docs_path.rglob("*.md"))

    print(f"Found {len(md_files)} MD files:")
    for i, md_file in enumerate(md_files[:3]):  # Just test the first 3 files
        print(f"  {i+1}. {md_file}")

        # Try to read the file
        try:
            with open(md_file, 'r', encoding='utf-8') as file:
                content = file.read()
                print(f"     Content length: {len(content)} characters")

                if len(content) > 100:
                    print(f"     First 100 chars: {content[:100]}...")

                # Test embedding
                print("     Testing embedding...")
                embedding = await get_embedding(content[:500])  # Just first 500 chars
                print(f"     Embedding length: {len(embedding)}")

                # Test chunking
                from ingest import chunk_text
                chunks = chunk_text(content)
                print(f"     Number of chunks: {len(chunks)}")

                # Process first chunk if exists
                if chunks:
                    first_chunk_embedding = await get_embedding(chunks[0])
                    print(f"     First chunk embedding length: {len(first_chunk_embedding)}")

        except Exception as e:
            print(f"     Error reading file: {e}")

        print()

if __name__ == "__main__":
    asyncio.run(debug_ingest())