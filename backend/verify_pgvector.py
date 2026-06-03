import sys
import os
import uuid
import numpy as np

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.base import Base # Ensure all mappers are initialized
from app.db.session import SessionLocal
from app.models.chatbot import Chatbot
from app.models.document import KnowledgeSource, KnowledgeChunk, SourceType, SourceStatus, ChunkStatus
from app.services.vector_store import VectorStoreService

def verify_integration():
    print("--- STARTING SUPABASE PGVECTOR INTEGRATION VERIFICATION ---\n")
    db = SessionLocal()
    try:
        # 1. Fetch active chatbot
        chatbot = db.query(Chatbot).filter(Chatbot.deleted_at == None).first()
        if not chatbot:
            print("[ERROR] No Chatbot found in the database. Please create a chatbot in the UI first.")
            return

        chatbot_id = chatbot.id
        org_id = chatbot.org_id
        print(f"[INFO] Using Chatbot ID: {chatbot_id}, Org ID: {org_id}")

        # 2. Create mock source and chunks
        print("\n[STEP 1] Creating mock KnowledgeSource and KnowledgeChunks...")
        source = KnowledgeSource(
            id=uuid.uuid4(),
            chatbot_id=chatbot_id,
            org_id=org_id,
            source_type=SourceType.TEXT,
            label="Verification Test",
            value="Vector DB Ingestion Test",
            status=SourceStatus.PROCESSING
        )
        db.add(source)
        db.flush()

        chunks = [
            "Supabase Cloud utilizes Postgres, which supports the pgvector extension out-of-the-box.",
            "FastAPI BackgroundTasks processes document embeddings inside the main web server process thread.",
            "VectorStoreService has been rewritten to execute high-performance hybrid searches using RRF."
        ]

        chunk_records = []
        for i, text in enumerate(chunks):
            record = KnowledgeChunk(
                id=uuid.uuid4(),
                source_id=source.id,
                chatbot_id=chatbot_id,
                chunk_text=text,
                chunk_index=i,
                index_status=ChunkStatus.PROCESSING
            )
            db.add(record)
            chunk_records.append(record)
        db.flush()
        print("[SUCCESS] Mock source and chunks flushed to database.")

        # 3. Add Vectors using updated VectorStoreService
        print("\n[STEP 2] Generating and inserting vectors via pgvector...")
        # Create dummy embeddings matching settings.EMBEDDING_DIM (3072 dimensions)
        embeddings = np.random.randn(len(chunks), 3072).tolist()
        chunk_ids = [str(r.id) for r in chunk_records]
        
        VectorStoreService.add_vectors(
            chatbot_id=str(chatbot_id),
            vectors=np.array(embeddings),
            chunk_ids=chunk_ids,
            source_id=str(source.id),
            chunk_texts=chunks,
            db=db
        )
        
        for r in chunk_records:
            r.index_status = ChunkStatus.COMPLETED
        source.status = SourceStatus.INDEXED
        db.commit()
        print("[SUCCESS] Vectors successfully inserted into knowledge_chunks.embedding column.")

        # 4. Verify vector insertion
        print("\n[STEP 3] Verifying embedding column populated...")
        db.refresh(source)
        inserted_chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.source_id == source.id).all()
        for idx, chunk in enumerate(inserted_chunks):
            assert chunk.embedding is not None, f"Chunk {idx} embedding is null!"
            print(f" -> Chunk {idx} embedding size: {len(chunk.embedding)} dimensions.")
        print("[SUCCESS] All chunk embeddings verified in database.")

        # 5. Run hybrid query search
        print("\n[STEP 4] Testing search_hybrid query execution...")
        query = "How to enable pgvector extension in Supabase?"
        results = VectorStoreService.search_hybrid(
            chatbot_id=str(chatbot_id),
            query=query,
            top_k=2,
            db=db
        )
        print(f"[SUCCESS] Search completed! Found {len(results)} matches.")
        for idx, res in enumerate(results):
            print(f" Match {idx+1}: Score={res['score']:.4f} | Text='{res['text']}'")

        # 6. Delete source and verify cascade delete
        print("\n[STEP 5] Deleting KnowledgeSource and verifying cascade delete...")
        db.delete(source)
        db.commit()
        
        # Verify chunks are gone
        remaining_chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.source_id == source.id).count()
        assert remaining_chunks == 0, f"Cascade delete failed, {remaining_chunks} chunks remaining!"
        print("[SUCCESS] Cascade delete verified. All chunks and embeddings deleted from DB.")

        print("\n--- ALL SUPABASE PGVECTOR VERIFICATIONS PASSED ---")

    except Exception as e:
        db.rollback()
        print(f"\n[FAILED] Verification failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_integration()
