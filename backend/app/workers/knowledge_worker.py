import logging
import time

from app.db.session import SessionLocal
from app.services.document import KnowledgeService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_once() -> bool:
    db = SessionLocal()
    try:
        return KnowledgeService.process_next_job(db)
    finally:
        db.close()


def main() -> None:
    logger.info("Knowledge worker started.")
    while True:
        did_work = run_once()
        if not did_work:
            time.sleep(2)


if __name__ == "__main__":
    main()
