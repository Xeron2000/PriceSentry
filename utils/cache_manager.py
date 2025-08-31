"""
Cache management utilities for PriceSentry system.
Provides intelligent caching with LRU strategy, TTL support, and performance monitoring.
"""

import hashlib
import json
import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class CacheStrategy(Enum):
    """Cache eviction strategies."""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    TTL = "ttl"  # Time To Live


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    value: Any
    timestamp: float = field(default_factory=time.time)
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    ttl: Optional[float] = None

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl

    def update_access(self):
        """Update access metadata."""
        self.access_count += 1
        self.last_access = time.time()


class CacheManager:
    """Intelligent cache management system."""

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[float] = None,
        strategy: CacheStrategy = CacheStrategy.LRU,
    ):
        """
        Initialize cache manager.

        Args:
            max_size: Maximum number of entries in cache
            default_ttl: Default time-to-live in seconds
            strategy: Cache eviction strategy
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.strategy = strategy
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.access_order: list = []  # Track access order for LRU
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)

        # Performance metrics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expirations = 0

        # Cache statistics
        self.creation_time = time.time()
        self.total_access_time = 0.0
        self.access_count = 0

        self.logger.info(
            f"CacheManager initialized with strategy={strategy}, max_size={max_size}"
        )

    def _generate_key(self, key: Union[str, tuple, dict]) -> str:
        """Generate consistent cache key from various input types."""
        if isinstance(key, str):
            return key
        elif isinstance(key, (tuple, list)):
            return hashlib.md5(str(key).encode()).hexdigest()
        elif isinstance(key, dict):
            return hashlib.md5(json.dumps(key, sort_keys=True).encode()).hexdigest()
        else:
            return hashlib.md5(str(key).encode()).hexdigest()

    def _evict_if_needed(self):
        """Evict entries if cache is full."""
        if len(self.cache) >= self.max_size:
            self.evictions += 1

            if self.strategy == CacheStrategy.LRU:
                # Remove least recently used (first in access_order)
                if self.access_order:
                    lru_key = self.access_order.pop(0)
                    if lru_key in self.cache:
                        del self.cache[lru_key]
            elif self.strategy == CacheStrategy.LFU:
                # Remove least frequently used
                lfu_key = min(
                    self.cache.keys(), key=lambda k: self.cache[k].access_count
                )
                del self.cache[lfu_key]
                if lfu_key in self.access_order:
                    self.access_order.remove(lfu_key)
            elif self.strategy == CacheStrategy.FIFO:
                # Remove first in (first in access_order)
                if self.access_order:
                    fifo_key = self.access_order.pop(0)
                    if fifo_key in self.cache:
                        del self.cache[fifo_key]
            elif self.strategy == CacheStrategy.TTL:
                # Remove expired entries first, then LRU
                expired_keys = [
                    k for k, entry in self.cache.items() if entry.is_expired()
                ]
                if expired_keys:
                    expired_key = expired_keys[0]
                    del self.cache[expired_key]
                    if expired_key in self.access_order:
                        self.access_order.remove(expired_key)
                    self.expirations += 1
                else:
                    # Remove least recently used
                    if self.access_order:
                        lru_key = self.access_order.pop(0)
                        if lru_key in self.cache:
                            del self.cache[lru_key]

    def _cleanup_expired(self):
        """Clean up expired entries."""
        expired_keys = []
        for key, entry in self.cache.items():
            if entry.is_expired():
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
            self.expirations += 1

        if expired_keys:
            self.logger.debug(f"Cleaned up {len(expired_keys)} expired entries")

    def get(self, key: Union[str, tuple, dict], default: Any = None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        start_time = time.time()
        cache_key = self._generate_key(key)

        with self.lock:
            # Clean up expired entries periodically
            if self.access_count % 100 == 0:
                self._cleanup_expired()

            if cache_key in self.cache:
                entry = self.cache[cache_key]

                if entry.is_expired():
                    del self.cache[cache_key]
                    if cache_key in self.access_order:
                        self.access_order.remove(cache_key)
                    self.expirations += 1
                    self.misses += 1
                else:
                    # Update access metadata
                    entry.update_access()

                    # Move to end for LRU
                    if self.strategy == CacheStrategy.LRU:
                        self.cache.move_to_end(cache_key)
                        # Update access order
                        if cache_key in self.access_order:
                            self.access_order.remove(cache_key)
                        self.access_order.append(cache_key)

                    self.hits += 1
                    self.access_count += 1
                    self.total_access_time += time.time() - start_time
                    return entry.value

            self.misses += 1
            self.access_count += 1
            self.total_access_time += time.time() - start_time
            return default

    def set(
        self, key: Union[str, tuple, dict], value: Any, ttl: Optional[float] = None
    ):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (overrides default)
        """
        cache_key = self._generate_key(key)
        entry_ttl = ttl if ttl is not None else self.default_ttl

        with self.lock:
            # Evict if needed
            self._evict_if_needed()

            # Create new entry
            entry = CacheEntry(value=value, ttl=entry_ttl)

            self.cache[cache_key] = entry

            # Add to access order (for new entries)
            if cache_key not in self.access_order:
                self.access_order.append(cache_key)

            self.logger.debug(f"Cached entry with key: {cache_key}")

    def delete(self, key: Union[str, tuple, dict]) -> bool:
        """
        Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if entry was deleted, False if not found
        """
        cache_key = self._generate_key(key)

        with self.lock:
            if cache_key in self.cache:
                del self.cache[cache_key]
                # Remove from access order
                if cache_key in self.access_order:
                    self.access_order.remove(cache_key)
                self.logger.debug(f"Deleted cache entry with key: {cache_key}")
                return True
            return False

    def clear(self):
        """Clear all entries from cache."""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
            self.logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            avg_access_time = (
                (self.total_access_time / self.access_count)
                if self.access_count > 0
                else 0
            )

            # Calculate memory usage (approximate)
            estimated_memory = sum(
                len(str(entry.value)) + len(str(key))
                for key, entry in self.cache.items()
            )

            return {
                "size": len(self.cache),
                "total_entries": len(self.cache),
                "max_size": self.max_size,
                "strategy": self.strategy.value,
                "hit_count": self.hits,
                "miss_count": self.misses,
                "eviction_count": self.evictions,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": f"{hit_rate:.2f}%",
                "evictions": self.evictions,
                "expirations": self.expirations,
                "avg_access_time_ms": f"{avg_access_time * 1000:.3f}",
                "estimated_memory_bytes": estimated_memory,
                "uptime_seconds": time.time() - self.creation_time,
                "default_ttl": self.default_ttl,
            }

    def get_keys(self) -> List[str]:
        """Get all cache keys."""
        with self.lock:
            return list(self.cache.keys())

    def get_values(self) -> List[Any]:
        """Get all cache values."""
        with self.lock:
            return [entry.value for entry in self.cache.values()]

    def contains(self, key: Union[str, tuple, dict]) -> bool:
        """Check if key exists in cache."""
        cache_key = self._generate_key(key)
        with self.lock:
            return cache_key in self.cache and not self.cache[cache_key].is_expired()

    def size(self) -> int:
        """Get current cache size."""
        with self.lock:
            return len(self.cache)

    def is_empty(self) -> bool:
        """Check if cache is empty."""
        with self.lock:
            return len(self.cache) == 0

    def __contains__(self, key: Union[str, tuple, dict]) -> bool:
        """Support 'in' operator."""
        return self.contains(key)

    def keys(self) -> List[str]:
        """Get all cache keys."""
        return self.get_keys()

    def values(self) -> List[Any]:
        """Get all cache values."""
        return self.get_values()

    def items(self) -> List[tuple]:
        """Get all cache items as (key, value) tuples."""
        with self.lock:
            return [(key, entry.value) for key, entry in self.cache.items()]

    def cleanup_expired(self) -> int:
        """Clean up expired entries and return count of removed entries."""
        with self.lock:
            initial_count = len(self.cache)
            self._cleanup_expired()
            return initial_count - len(self.cache)

    def resize(self, new_max_size: int):
        """
        Resize cache.

        Args:
            new_max_size: New maximum size
        """
        with self.lock:
            self.max_size = new_max_size
            # Evict entries if needed
            while len(self.cache) > self.max_size:
                self._evict_if_needed()
            self.logger.info(f"Cache resized to {new_max_size}")

    def set_strategy(self, new_strategy: CacheStrategy):
        """
        Change cache strategy.

        Args:
            new_strategy: New cache strategy
        """
        with self.lock:
            self.strategy = new_strategy
            self.logger.info(f"Cache strategy changed to {new_strategy.value}")

    def get_expired_entries(self) -> List[str]:
        """Get list of expired entry keys."""
        with self.lock:
            return [key for key, entry in self.cache.items() if entry.is_expired()]

    def cleanup_expired_entries(self) -> int:
        """Clean up all expired entries and return count."""
        with self.lock:
            expired_keys = self.get_expired_entries()
            for key in expired_keys:
                del self.cache[key]
                self.expirations += 1
            return len(expired_keys)


class PriceCacheManager(CacheManager):
    """Specialized cache manager for price data."""

    def __init__(self, max_size: int = 1000, default_ttl: float = 300.0):
        """
        Initialize price cache manager.

        Args:
            max_size: Maximum number of price entries
            default_ttl: Default TTL for price data (5 minutes)
        """
        super().__init__(max_size, default_ttl, CacheStrategy.LRU)
        self.price_precision = 8  # Decimal places for price precision

    def get_price(
        self, symbol: str, default: Optional[float] = None
    ) -> Optional[float]:
        """
        Get price from cache.

        Args:
            symbol: Trading pair symbol
            default: Default price if not found

        Returns:
            Cached price or default
        """
        price = self.get(symbol, default)
        if price is not None:
            return round(float(price), self.price_precision)
        return None

    def set_price(self, symbol: str, price: float, ttl: Optional[float] = None):
        """
        Set price in cache.

        Args:
            symbol: Trading pair symbol
            price: Price value
            ttl: Time-to-live in seconds
        """
        rounded_price = round(float(price), self.price_precision)
        self.set(symbol, rounded_price, ttl)

    def get_prices(
        self, symbols: List[str], default: Optional[float] = None
    ) -> Dict[str, Optional[float]]:
        """
        Get multiple prices from cache.

        Args:
            symbols: List of trading pair symbols
            default: Default price if not found

        Returns:
            Dictionary of symbol -> price mappings
        """
        result = {}
        for symbol in symbols:
            result[symbol] = self.get_price(symbol, default=default)
        return result

    def set_prices(self, prices: Dict[str, float], ttl: Optional[float] = None):
        """
        Set multiple prices in cache.

        Args:
            prices: Dictionary of symbol -> price mappings
            ttl: Time-to-live in seconds
        """
        for symbol, price in prices.items():
            self.set_price(symbol, price, ttl)

    def get_price_history(self, symbol: str, limit: int = 10) -> List[float]:
        """
        Get price history for a symbol (if stored).

        Args:
            symbol: Trading pair symbol
            limit: Maximum number of historical prices

        Returns:
            List of historical prices
        """
        history_key = f"{symbol}_history"
        history = self.get(history_key, [])
        return history[-limit:] if history else []

    def add_to_price_history(self, symbol: str, price: float, max_history: int = 100):
        """
        Add price to history cache.

        Args:
            symbol: Trading pair symbol
            price: Price value
            max_history: Maximum number of historical prices to keep
        """
        history_key = f"{symbol}_history"
        history = self.get(history_key, [])

        rounded_price = round(float(price), self.price_precision)
        history.append(rounded_price)

        # Limit history size
        if len(history) > max_history:
            history = history[-max_history:]

        self.set(history_key, history, ttl=3600)  # 1 hour TTL for history

    def delete_price(self, symbol: str) -> bool:
        """
        Delete price from cache.

        Args:
            symbol: Trading pair symbol

        Returns:
            True if price was deleted, False if not found
        """
        return self.delete(symbol)

    def clear_prices(self):
        """Clear all price data from cache."""
        self.clear()

    def cleanup_expired_prices(self) -> int:
        """
        Clean up expired price data.

        Returns:
            Number of expired prices removed
        """
        return self.cleanup_expired()


# Global cache instances
default_cache = CacheManager(max_size=1000, default_ttl=300.0)
price_cache = PriceCacheManager(max_size=1000, default_ttl=300.0)
