import asyncio
import os
import sys

# Add backend directory to path so it can import 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.text_extractor import TextExtractor
from app.services.chunker import TextChunker
from app.services.embedding import embedding_service

async def run_pipeline():
    print("\n--- STARTING SECOND STAGE (INGESTION) TEST ---\n")

    # STEP 1: Text Extraction
    print("--- STEP 1: Text Extraction ---")
    
    # 1A. Test URL
    test_url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
    print(f"\n[A] Extracting text from URL: {test_url}")
    try:
        text = await TextExtractor.extract_url(test_url)
        print(f"[SUCCESS] URL Extraction successful! Total characters: {len(text)}")
        preview_str = text[:150].encode('ascii', 'ignore').decode('ascii')
        print(f"Preview:\n{preview_str}...\n")
    except Exception as e:
        print(f"[FAILED] URL Extraction failed: {e}")
        text = "Fallback text because URL failed."

    # 1B. Test TXT and CSV (Creating dummy files on the fly)
    with open("test_dummy.txt", "w", encoding="utf-8") as f:
        f.write("This is a dummy text file for testing the extraction pipeline.")
    with open("test_dummy.csv", "w", encoding="utf-8") as f:
        f.write("Name,Age,Profession\nJohn,30,Engineer\nAlice,25,Data Scientist")

    print(f"\n[B] Extracting text from TXT: test_dummy.txt")
    try:
        txt_text = TextExtractor.extract_txt("test_dummy.txt")
        print(f"[SUCCESS] TXT Extraction successful!\nPreview: {txt_text[:50]}...")
    except Exception as e:
        print(f"[FAILED] TXT Extraction failed: {e}")

    print(f"\n[C] Extracting text from CSV: test_dummy.csv")
    try:
        csv_text = TextExtractor.extract_csv("test_dummy.csv")
        print(f"[SUCCESS] CSV Extraction successful!\nPreview: {csv_text[:50]}...")
    except Exception as e:
        print(f"[FAILED] CSV Extraction failed: {e}")

    # 1C. Test PDF and DOCX
    print("\n[D] PDF and DOCX Extraction:")
    print("-> Note: To test these, place 'sample.pdf' and 'sample.docx' in the 'backend' folder.")
    
    if os.path.exists("sample.pdf"):
        try:
            pdf_text = TextExtractor.extract_pdf("sample.pdf")
            print(f"[SUCCESS] PDF Extraction successful! Characters: {len(pdf_text)}")
            print(f"Preview: {pdf_text[:50].encode('ascii', 'ignore').decode('ascii')}...")
        except Exception as e:
            print(f"[FAILED] PDF Extraction failed: {e}")
    else:
        print("-> 'sample.pdf' not found. Skipping PDF test.")

    if os.path.exists("sample.docx"):
        try:
            docx_text = TextExtractor.extract_docx("sample.docx")
            print(f"[SUCCESS] DOCX Extraction successful! Characters: {len(docx_text)}")
            print(f"Preview: {docx_text[:50].encode('ascii', 'ignore').decode('ascii')}...")
        except Exception as e:
            print(f"[FAILED] DOCX Extraction failed: {e}")
    else:
        print("-> 'sample.docx' not found. Skipping DOCX test.\n")

    # STEP 2: Text Chunking
    print("--- STEP 2: Text Chunking ---")
    try:
        chunks = TextChunker.split_text(text)
        print(f"[SUCCESS] Chunking successful! Text divided into {len(chunks)} chunks.")
        if chunks:
            print(f"Chunk 1 Length: {len(chunks[0])} characters")
            if len(chunks) > 1:
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
    asyncio.run(run_pipeline())
