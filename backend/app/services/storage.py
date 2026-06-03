import os
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    @staticmethod
    def save_file(storage_path: str, content: bytes) -> None:
        """
        Saves file content to the local filesystem.
        Can be extended to support Supabase Storage / AWS S3 in the future.
        """
        try:
            os.makedirs(os.path.dirname(storage_path), exist_ok=True)
            with open(storage_path, "wb") as f:
                f.write(content)
            logger.info("Successfully saved file to %s", storage_path)
        except Exception as e:
            logger.error("Failed to save file to %s: %s", storage_path, e)
            raise ValueError(f"Could not save file to disk: {e}")

    @staticmethod
    def delete_file(storage_path: str) -> None:
        """
        Deletes a file from the local filesystem.
        Can be extended to support Supabase Storage / AWS S3 in the future.
        """
        if storage_path and os.path.exists(storage_path):
            try:
                os.remove(storage_path)
                logger.info("Successfully deleted file at %s", storage_path)
            except OSError as e:
                logger.warning("Failed to delete file at %s: %s", storage_path, e)
