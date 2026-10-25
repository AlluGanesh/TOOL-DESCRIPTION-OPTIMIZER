"""Persistent disk cache service for deterministic evaluation inference calls."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from backend.app.core.config import CACHE_DIR
from backend.app.core.logging import logger

class CacheService:
    """Manages reading and writing inference results to disk under cache/."""

    def __init__(self, cache_dir: Optional[Union[str, Path]] = None):
        self.cache_dir = Path(cache_dir) if cache_dir else CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def has(self, key: str) -> bool:
        """Checks if a cache entry exists on disk."""
        return self._get_path(key).exists()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieves a cached JSON payload by key. Returns None if absent or corrupted."""
        path = self._get_path(key)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.warning("Failed to read cache file %s: %s", path, exc)
            return None

    def set(self, key: str, value: Any) -> None:
        """Persists a serializable payload to disk under cache/{key}.json."""
        path = self._get_path(key)
        try:
            # Write to temporary file first, then replace for atomic persistence
            tmp_path = path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(value, f, indent=2, ensure_ascii=False)
            tmp_path.replace(path)
        except Exception as exc:
            logger.error("Failed to write cache file %s: %s", path, exc)

    def clear(self) -> int:
        """Removes all cached JSON entries while preserving .gitkeep. Returns count of deleted files."""
        count = 0
        for item in self.cache_dir.glob("*.json"):
            try:
                item.unlink()
                count += 1
            except Exception as exc:
                logger.warning("Failed to delete cache file %s: %s", item, exc)
        return count

# Default global cache service instance
cache_service = CacheService()
