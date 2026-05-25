import asyncio
import os
import sys

# Add backend directory to path so it can import 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.text_extractor import TextExtractor
from app.services.chunker import TextChunker
from app.services.embedding import embedding_service

async def test_pipeline():
    print("\n--- STARTING SECOND STAGE (INGESTION) TEST ---\n")

    # STEP 1: Text Extraction
    print("--- STEP 1: Text Extraction ---")
    test_url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
    print(f"Extracting text from website: {test_url}")
    try:
        text = await TextExtractor.extract_url(test_url)
        print(f"[SUCCESS] Extraction successful! Total characters extracted: {len(text)}")
        
        # safely encode the preview string to ignore unprintable unicode chars in windows console
        preview_str = text[:250].encode('ascii', 'ignore').decode('ascii')
        print(f"Preview:\n{preview_str}...\n")
    except Exception as e:
        print(f"[FAILED] Extraction failed: {e}")
        return

    # STEP 2: Text Chunking
    print("--- STEP 2: Text Chunking ---")
    try:
        chunks = TextChunker.split_text(text)
        print(f"[SUCCESS] Chunking successful! Text divided into {len(chunks)} chunks.")
        if chunks:
            print(f"Chunk 1 Length: {len(chunks[0])} characters")
            print(f"Chunk 2 Length: {len(chunks[1])} characters (Notice the overlap with Chunk 1)")
            
            preview_chunk = chunks[0][:150].encode('ascii', 'ignore').decode('ascii')
            print(f"Preview of Chunk 1:\n{preview_chunk}...\n")
    except Exception as e:
        print(f"[FAILED] Chunking failed: {e}")
        return

    # STEP 3: Vector Embedding
    print("--- STEP 3: Vector Embedding ---")
    print("Loading embedding model... (This might take a few seconds on the first run)")
    try:
        # We'll just encode the first 3 chunks to save time during the test
        test_chunks = chunks[:3]
        embeddings = embedding_service.encode(test_chunks)
        print(f"[SUCCESS] Embedding successful! Generated vectors for {len(embeddings)} chunks.")
        print(f"Vector Dimensions: {embeddings[0].shape[0]} (This is the size of the array for each chunk)")
        print(f"Preview of Vector 1 (first 5 values):\n{embeddings[0][:5]}...\n")
    except Exception as e:
        print(f"[FAILED] Embedding failed: {e}")
        return

    print("--- ALL STEPS WORKING PERFECTLY! ---")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
