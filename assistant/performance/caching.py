"""
Response Caching and Memoization
Provides intelligent caching and memoization for improved performance.
"""

import os
import json
import hashlib
from typing import Optional, Dict, Any, List, Tuple, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
import pickle


class CacheStrategy(Enum):
    LRU = "lru"
    FIFO = "fifo"
    LFU = "lfu"
    TTL = "ttl"


@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: str
    last_accessed: str
    access_count: int
    ttl: Optional[int]  # Time to live in seconds
    size_bytes: int


class CacheManager:
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.cache_dir = os.path.join(self.base_dir, "data", "cache")
        self.cache_file = os.path.join(self.cache_dir, "cache_entries.json")
        
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.strategy = CacheStrategy.LRU
        
        # Load cache from disk
        self._load_cache()

    def _load_cache(self):
        """Load cache from disk."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    data = pickle.load(f)
                self.cache = data
                # Clean expired entries
                self._clean_expired()
            except Exception:
                pass

    def _save_cache(self):
        """Save cache to disk."""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
        except Exception as e:
            print(f"[CacheManager] Failed to save cache: {e}")

    def _clean_expired(self):
        """Remove expired cache entries."""
        now = datetime.now()
        expired_keys = []
        
        for key, entry in self.cache.items():
            if entry.ttl:
                created = datetime.fromisoformat(entry.created_at)
                if (now - created).total_seconds() > entry.ttl:
                    expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]

    def _evict_if_needed(self):
        """Evict entries if cache is full."""
        if len(self.cache) < self.max_size:
            return
        
        if self.strategy == CacheStrategy.LRU:
            # Evict least recently used
            lru_key = min(self.cache.keys(), 
                         key=lambda k: datetime.fromisoformat(self.cache[k].last_accessed))
            del self.cache[lru_key]
        
        elif self.strategy == CacheStrategy.LFU:
            # Evict least frequently used
            lfu_key = min(self.cache.keys(), key=lambda k: self.cache[k].access_count)
            del self.cache[lfu_key]
        
        elif self.strategy == CacheStrategy.FIFO:
            # Evict oldest
            fifo_key = min(self.cache.keys(),
                         key=lambda k: datetime.fromisoformat(self.cache[k].created_at))
            del self.cache[fifo_key]

    def _generate_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function and arguments."""
        key_parts = [func.__name__]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if entry.ttl:
            created = datetime.fromisoformat(entry.created_at)
            if (datetime.now() - created).total_seconds() > entry.ttl:
                del self.cache[key]
                return None
        
        # Update access info
        entry.last_accessed = datetime.now().isoformat()
        entry.access_count += 1
        
        return entry.value

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache."""
        self._evict_if_needed()
        
        # Calculate size
        size_bytes = len(pickle.dumps(value))
        
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now().isoformat(),
            last_accessed=datetime.now().isoformat(),
            access_count=1,
            ttl=ttl or self.default_ttl,
            size_bytes=size_bytes
        )
        
        self.cache[key] = entry
        self._save_cache()
        
        return True

    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        if key not in self.cache:
            return False
        
        del self.cache[key]
        self._save_cache()
        
        return True

    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self._save_cache()

    def memoize(self, ttl: int = None):
        """Decorator for memoizing function results."""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                key = self._generate_key(func, args, kwargs)
                
                # Try to get from cache
                cached_value = self.get(key)
                if cached_value is not None:
                    return cached_value
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Cache result
                self.set(key, result, ttl)
                
                return result
            return wrapper
        return decorator

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.cache)
        total_size = sum(entry.size_bytes for entry in self.cache.values())
        
        # Calculate hit rate (simplified)
        total_access = sum(entry.access_count for entry in self.cache.values())
        
        return {
            'total_entries': total_entries,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'max_size': self.max_size,
            'strategy': self.strategy.value,
            'total_access': total_access,
            'utilization': round(total_entries / self.max_size * 100, 2)
        }

    def set_strategy(self, strategy: CacheStrategy):
        """Set cache eviction strategy."""
        self.strategy = strategy

    def export_cache(self, export_path: str) -> Tuple[bool, str]:
        """Export cache to file."""
        try:
            export_data = {
                'cache': {k: asdict(v) for k, v in self.cache.items()},
                'statistics': self.get_statistics(),
                'exported_at': datetime.now().isoformat()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True, f"Cache exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"


# Global cache instance
_global_cache = CacheManager()


def cached(ttl: int = None, cache: CacheManager = None):
    """Decorator for caching function results."""
    cache = cache or _global_cache
    return cache.memoize(ttl)


def get_cache() -> CacheManager:
    """Get the global cache instance."""
    return _global_cache
