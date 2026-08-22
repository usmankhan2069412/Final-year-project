import os
import logging
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    @staticmethod
    def get_storage_path(filename: str) -> str:
        """
        Computes and validates the target storage path for a file.
        Can be adapted for cloud/S3 storage keys.
        """
        upload_root = os.path.abspath(settings.UPLOAD_DIR)
        os.makedirs(upload_root, exist_ok=True)
        storage_path = os.path.abspath(os.path.join(upload_root, Path(filename).name))
        if not storage_path.startswith(upload_root):
            raise ValueError("Invalid storage path")
        return storage_path

    @classmethod
    def save_file(cls, storage_path: str, content: bytes) -> None:
        """
        Saves file content to the target storage path.
        """
        try:
            os.makedirs(os.path.dirname(storage_path), exist_ok=True)
            with open(storage_path, "wb") as f:
                f.write(content)
            logger.info("Successfully saved file to %s", storage_path)
        except Exception as e:
            logger.error("Failed to save file to %s: %s", storage_path, e)
            raise ValueError(f"Could not save file to disk: {e}")

    @classmethod
    def save_file_content(cls, filename: str, content: bytes) -> str:
        """
        Encapsulates storage path resolution and file saving in a single call.
        Returns the resolved storage path.
        """
        storage_path = cls.get_storage_path(filename)
        cls.save_file(storage_path, content)
        return storage_path

    @staticmethod
    def delete_file(storage_path: str) -> None:
        """
        Deletes a file from storage.
        """
        if storage_path and os.path.exists(storage_path):
            try:
                os.remove(storage_path)
                logger.info("Successfully deleted file at %s", storage_path)
            except OSError as e:
                logger.warning("Failed to delete file at %s: %s", storage_path, e)
