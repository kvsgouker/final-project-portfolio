"""
Project Name: Star Power
File: merge_imdb_cache.py

Allows cache to be restarted when incomplete (vital for long download runs)


Author: Kyle Salgado-Gouker
"""

import json
import os
from access.paths import RATINGS_DATA_DIRECTORY
from processing.cleaner import get_series_imdb_id
from utils.film_log import FilmLog

CACHE_FILE = os.path.join(RATINGS_DATA_DIRECTORY, "imdb_cache.json")


class IMDbCache:
    _instance = None  # singleton storage

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load()
        return cls._instance

    def __init__(self):
        if IMDbCache._instance is not None:
            raise Exception("Use IMDbCache.get_instance() instead of creating manually.")
        self.cache = {}
        self.counter = 0

    def _load(self):
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                self.cache = json.load(f)
            FilmLog.get_shared_logger().log(FilmLog.CACHE_LOGGING, f"IMDb cache loaded with {len(self.cache)} entries.")
        else:
            FilmLog.get_shared_logger().log(FilmLog.CACHE_LOGGING, "No existing cache found. Starting fresh.")

    def save(self):
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f, indent=4)
        FilmLog.get_shared_logger().log(FilmLog.CACHE_LOGGING, f"IMDb cache saved with {len(self.cache)} entries.")

    def get(self, title):
        title_key = title.lower().strip()
        return self.cache.get(title_key)

    def set(self, title, imdb_id, title_type="TV Series"):
        title_key = title.lower().strip()
        self.cache[title_key] = {
            "IMDb Series ID": imdb_id,
            "Title Type": title_type
        }
        self.counter += 1
        if self.counter % 10 == 0:
            FilmLog.get_shared_logger().log(FilmLog.CACHE_LOGGING, f"Cache updated with 10 more entries, total updates: {self.counter}")

    def get_or_fetch(self, title):
        entry = self.get(title)
        if entry:
            return entry
        imdb_id = get_series_imdb_id(title)
        self.set(title, imdb_id)
        return self.get(title)

    def verify(self):
        non_dicts = [k for k, v in self.cache.items() if not isinstance(v, dict)]
        if non_dicts:
            FilmLog.get_shared_logger().log(FilmLog.CACHE_LOGGING, f"{len(non_dicts)} invalid entries found.")
        else:
            FilmLog.get_shared_logger().log(FilmLog.CACHE_LOGGING, "All cache entries are valid dictionaries.")

    def keys(self):
        return list(self.cache.keys())

    def values(self):
        return list(self.cache.values())

    def size(self):
        return len(self.cache)

    def has(self, title):
        """Check if a normalized title is in the cache."""
        return title.lower().strip() in self.cache

    def delete(self, title):
        """Remove a title from the cache, if it exists."""
        title_key = title.lower().strip()
        if title_key in self.cache:
            del self.cache[title_key]
            FilmLog.get_shared_logger().log(FilmLog.CACHE_LOGGING, f"Removed cache entry for title: {title}")
        else:
            FilmLog.get_shared_logger().log(FilmLog.CACHE_LOGGING, f"No cache entry found for: {title}")

    def __contains__(self, title):
        """Allow `in cache` syntax.
           For Example:
                if title in cache, return True
        """
        return self.has(title)

    def __getitem__(self, title):
        """Allow bracket access like a dict."""
        return self.cache[title.lower().strip()]

    def __setitem__(self, title, imdb_info):
        """Allow bracket assignment like a dict."""
        self.set(title, imdb_info.get("IMDb Series ID", None), imdb_info.get("Title Type", "TV Series"))

    def clear(self):
        """Clear the entire cache."""
        self.cache.clear()
        FilmLog.get_shared_logger().log(FilmLog.CACHE_LOGGING, "Cache cleared.")
