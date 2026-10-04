"""
Utility script to re-index all orphaned or un-embedded knowledge sources.
Usage:
    cd backend
    python reindex_knowledge_base.py [--force-all]
"""
import sys
import argparse
import logging
from sqlalchemy import select, func, or_, text
import app.db.base  # noqa: F401 - Register all SQLAlchemy models
from app.db.session import SessionLocal
from app.models.document import KnowledgeSource, KnowledgeChunk, ChunkStatus, SourceStatus
from app.services.document import KnowledgeService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reindex")

def reindex(force_all: bool = False):
    db = SessionLocal()
    try:
        if force_all:
            sources = db.query(KnowledgeSource).filter(KnowledgeSource.status != SourceStatus.FAILED).all()
            logger.info("Found %d total sources to force re-index.", len(sources))
        else:
            # Find sources that have chunks with QUEUED status or NULL embeddings
            subq = (
                select(KnowledgeChunk.source_id)
                .filter(or_(KnowledgeChunk.index_status == ChunkStatus.QUEUED, KnowledgeChunk.embedding.is_(None)))
                .distinct()
            )
            sources = db.query(KnowledgeSource).filter(KnowledgeSource.id.in_(subq)).all()
            logger.info("Found %d sources requiring re-indexing.", len(sources))

        if not sources:
            logger.info("Knowledge base is fully up-to-date. No re-indexing needed.")
            return

        for idx, src in enumerate(sources, 1):
            logger.info("[%d/%d] Re-indexing source %s (type=%s, chatbot=%s)...", idx, len(sources), src.id, src.source_type, src.chatbot_id)
            try:
                db.execute(text("SELECT set_config('app.current_org_id', :org_id, true)"), {"org_id": str(src.org_id)})
                KnowledgeService.process_source(db, src)
                db.commit()
                logger.info("✓ Successfully re-indexed source %s", src.id)
            except Exception as e:
                db.rollback()
                logger.error("✗ Failed to re-index source %s: %s", src.id, e, exc_info=True)

    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Re-index knowledge chunks")
    parser.add_argument("--force-all", action="store_true", help="Re-index all sources, not just orphaned ones")
    args = parser.parse_args()
    reindex(force_all=args.force_all)
