from __future__ import annotations

import hashlib
import hmac
import pickle
import typing as t

import redis

from modx.cache import (
    CACHE_MISS,
    CacheMiss,
    EMPTY,
    Empty,
    KVCache,
    V,
)
from modx.config import ModXConfig
from modx.helpers.mixin import ContextMixin, LoggingTagMixin
from modx.logger import Logger


class RedisCache(KVCache[V], ContextMixin):
    __logging_tag__ = 'modx.cache.redis'

    def __init__(
        self,
        config: ModXConfig,
        logger: Logger,
    ) -> None:
        LoggingTagMixin.__init__(self, logger)
        self.config = config.cache
        if not self.config.redis:
            raise ValueError("Redis configuration is missing in ModXConfig.")

        self.logger.info("Initializing Redis cache connection")

        self.client = redis.Redis(
            host=self.config.redis.host,
            port=self.config.redis.port,
            db=self.config.redis.db,
            password=self.config.redis.password,
            decode_responses=False,  # Store data as bytes
            socket_timeout=self.config.redis.socket_timeout,
            socket_connect_timeout=self.config.redis.socket_connect_timeout,
            retry_on_timeout=self.config.redis.retry_on_timeout,
            max_connections=self.config.redis.max_connections,
            health_check_interval=self.config.redis.health_check_interval,
            ssl=self.config.redis.ssl,
            ssl_cert_reqs=self.config.redis.ssl_cert_reqs,
        )

        self.logger.info(
            f"Redis cache initialized with host={self.config.redis.host}, "
            f"port={self.config.redis.port}, db={self.config.redis.db}",
            redis_host=self.config.redis.host,
            redis_port=self.config.redis.port,
            redis_db=self.config.redis.db
        )

    def add_prefix(self, key: str) -> str:
        """Add cache prefix to key."""
        return f"{self.config.pref}{key}"

    def serl(self, value: V) -> bytes:
        """Serialize value with optional HMAC signing."""
        try:
            data = pickle.dumps(value)

            if (
                self.config.redis.secure_serialization and
                self.config.redis.secret_key
            ):
                # Create HMAC signature
                signature = hmac.new(
                    self.config.redis.secret_key.encode('utf-8'),
                    data,
                    hashlib.sha256
                ).digest()

                # Prepend signature to data
                data = signature + data
                self.logger.debug("Value serialized with HMAC signature")
            else:
                self.logger.debug("Value serialized without signature")

            return data
        except Exception as e:
            self.logger.error(f"Failed to serialize value: {e}")
            raise ValueError(f"Serialization failed: {e}")

    def deserl(self, data: bytes) -> V:
        """Deserialize value with optional HMAC verification."""
        try:
            if (
                self.config.redis.secure_serialization and
                self.config.redis.secret_key
            ):
                # Extract signature and data
                if len(data) < 32:  # SHA256 digest is 32 bytes
                    self.logger.warning(
                        "Data too short for signed serialization"
                    )
                    raise ValueError("Invalid signed data")

                signature = data[:32]
                payload = data[32:]

                # Verify signature
                expected_signature = hmac.new(
                    self.config.redis.secret_key.encode('utf-8'),
                    payload,
                    hashlib.sha256
                ).digest()

                if not hmac.compare_digest(signature, expected_signature):
                    self.logger.warning("HMAC signature verification failed")
                    raise ValueError("Invalid signature")

                self.logger.debug("HMAC signature verified successfully")
                return pickle.loads(payload)
            else:
                self.logger.debug(
                    "Deserializing value without signature verification"
                )
                return pickle.loads(data)
        except Exception as e:
            self.logger.error(f"Failed to deserialize value: {e}")
            raise ValueError(f"Deserialization failed: {e}")

    def set_negative(self, key: str, /) -> None:
        """Store cache miss marker to prevent cache penetration."""
        prefixed_key = self.add_prefix(key)
        try:
            marker_data = self.serl(CACHE_MISS)
            self.client.setex(
                prefixed_key,
                self.config.negative_ttl,
                marker_data
            )
            self.logger.debug(f"Set negative cache for key: {key}")
        except redis.RedisError as e:
            self.logger.warning(
                f"Failed to set negative cache for key {key}: {e}"
            )

    def __getitem__(self, key: str) -> V | Empty:
        prefixed_key = self.add_prefix(key)
        try:
            data = self.client.get(prefixed_key)  # type: bytes | None
            if data is not None:
                try:
                    value = self.deserl(data)
                    if isinstance(value, CacheMiss):
                        self.logger.debug(
                            f"Found negative cache for key: {key}"
                        )
                        return EMPTY
                    self.logger.debug(f"Cache hit for key: {key}")
                    return value
                except ValueError:
                    self.logger.warning(
                        f"Failed to deserialize cached value for key: {key}"
                    )
                    # Delete corrupted data
                    try:
                        self.client.delete(prefixed_key)
                    except redis.RedisError:
                        pass  # Ignore deletion errors
                    return EMPTY
            else:
                self.logger.debug(f"Cache miss for key: {key}")
                return EMPTY
        except redis.RedisError as e:
            self.logger.error(f"Redis error when getting key {key}: {e}")
            return EMPTY

    def __setitem__(self, key: str, value: V) -> None:
        prefixed_key = self.add_prefix(key)
        try:
            data = self.serl(value)
            result = self.client.setex(
                prefixed_key,
                self.config.default_ttl,
                data
            )
            if result:
                self.logger.debug(f"Successfully cached key: {key}")
            else:
                self.logger.warning(f"Failed to cache key: {key}")
        except (redis.RedisError, ValueError) as e:
            self.logger.error(f"Failed to set cache for key {key}: {e}")

    def __delitem__(self, key: str) -> None:
        prefixed_key = self.add_prefix(key)
        try:
            result = self.client.delete(prefixed_key)
            if result == 0:
                self.logger.debug(f"Key not found for deletion: {key}")
                raise KeyError(key)
            else:
                self.logger.debug(f"Successfully deleted key: {key}")
        except redis.RedisError as e:
            self.logger.error(f"Redis error when deleting key {key}: {e}")
            raise KeyError(key)

    def __iter__(self) -> t.Iterator[str]:
        pattern = f"{self.config.pref}*"
        try:
            count = 0
            for key in self.client.scan_iter(match=pattern):
                if isinstance(key, bytes):
                    key_str = key.decode('utf-8')
                else:
                    key_str = key

                if key_str.startswith(self.config.pref):
                    yield key_str[len(self.config.pref):]
                    count += 1

            self.logger.debug(f"Iterated over {count} cache keys")
        except redis.RedisError as e:
            self.logger.error(f"Redis error during iteration: {e}")
            return

    def __len__(self) -> int:
        pattern = f"{self.config.pref}*"
        try:
            count = sum(1 for _ in self.client.scan_iter(match=pattern))
            self.logger.debug(f"Cache contains {count} keys")
            return count
        except redis.RedisError as e:
            self.logger.error(f"Redis error when counting keys: {e}")
            return 0

    def __contains__(self, key: object, /) -> bool:
        if not isinstance(key, str):
            return False
        prefixed_key = self.add_prefix(key)
        try:
            exists = self.client.exists(prefixed_key) > 0
            self.logger.debug(f"Key existence check for {key}: {exists}")
            return exists
        except redis.RedisError as e:
            self.logger.error(
                f"Redis error when checking key existence {key}: {e}"
            )
            return False

    def get(self, key: str, default: V | None = None, /) -> V | None:
        """Get value from cache, return default if not found."""
        result = self[key]
        if isinstance(result, Empty):
            return default
        return result

    def setdefault(self, key: str, default: V | None = None, /) -> V | None:
        """Get value or set and return default if key doesn't exist."""
        # First check if key exists (including negative cache)
        prefixed_key = self.add_prefix(key)
        try:
            data = self.client.get(prefixed_key)  # type: bytes | None
            if data is not None:
                try:
                    value = self.deserl(data)
                    if isinstance(value, CacheMiss):
                        # Key is in negative cache, return default without
                        # setting
                        self.logger.debug(f"Key {key} in negative cache")
                        return default
                    # Key exists with real value
                    self.logger.debug(
                        f"Key {key} exists, returning cached value"
                    )
                    return value
                except ValueError:
                    # Corrupted data, delete and continue
                    try:
                        self.client.delete(prefixed_key)
                    except redis.RedisError:
                        pass

            # Key doesn't exist, set default if provided
            if default is not None:
                self[key] = default
                self.logger.debug(f"Set default value for key: {key}")
                return default
            else:
                # No default provided, set negative cache
                self.set_negative(key)
                return None

        except redis.RedisError as e:
            self.logger.error(f"Redis error in setdefault for key {key}: {e}")
            return default

    def clear(self) -> None:
        """Clear all cache entries with the configured prefix."""
        pattern = f"{self.config.pref}*"
        try:
            keys = list(self.client.scan_iter(match=pattern))
            if keys:
                deleted_count = self.client.delete(*keys)
                self.logger.info(f"Cleared {deleted_count} cache entries")
            else:
                self.logger.info("No cache entries to clear")
        except redis.RedisError as e:
            self.logger.error(f"Failed to clear cache: {e}")

    def pop(self, key: str, default: V | None = None, /) -> V | None:
        """Remove and return value, or return default if not found."""
        prefixed_key = self.add_prefix(key)
        try:
            data = self.client.get(prefixed_key)  # type: bytes | None
            if data is not None:
                deleted = self.client.delete(prefixed_key)
                if deleted:
                    try:
                        value = self.deserl(data)
                        if isinstance(value, CacheMiss):
                            return default
                        self.logger.debug(f"Successfully popped key: {key}")
                        return value
                    except ValueError:
                        self.logger.warning(
                            f"Failed to deserialize popped value for key: {key}"
                        )
                        return default
            self.logger.debug(f"Key not found for pop operation: {key}")
            return default
        except redis.RedisError as e:
            self.logger.error(f"Redis error when popping key {key}: {e}")
            return default

    def popitem(self) -> t.Tuple[str, V]:
        """Remove and return an arbitrary (key, value) pair."""
        pattern = f"{self.config.pref}*"
        try:
            # Get a random key with prefix
            for key in self.client.scan_iter(match=pattern, count=1):
                if isinstance(key, bytes):
                    key_str = key.decode('utf-8')
                else:
                    key_str = key

                if key_str.startswith(self.config.pref):
                    original_key = key_str[len(self.config.pref):]
                    value = self.pop(original_key)
                    if value is not None:
                        self.logger.debug(
                            f"Successfully popped item: {original_key}"
                        )
                        return original_key, value

            self.logger.debug("No items to pop")
            raise KeyError("popitem(): cache is empty")
        except redis.RedisError as e:
            self.logger.error(f"Redis error during popitem: {e}")
            raise KeyError(f"popitem() failed due to Redis error: {e}")

    def set(self, key: str, value: V, /) -> None:
        """Set a key-value pair (alias for __setitem__)."""
        self[key] = value

    def setx(
        self,
        key: str,
        value: V, /,
        ttl: int | None = None
    ) -> None:
        """Set a key-value pair with optional TTL."""
        prefixed_key = self.add_prefix(key)
        try:
            data = self.serl(value)
            if ttl is not None:
                result = self.client.setex(prefixed_key, ttl, data)
                self.logger.debug(f"Set key {key} with TTL {ttl}")
            else:
                result = self.client.set(prefixed_key, data)
                self.logger.debug(f"Set key {key} without TTL")

            if not result:
                self.logger.warning(f"Failed to set key: {key}")
        except (redis.RedisError, ValueError) as e:
            self.logger.error(f"Failed to setx for key {key}: {e}")

    def ttl(self, key: str, /) -> int | None:
        """Get TTL for a key."""
        prefixed_key = self.add_prefix(key)
        try:
            result = self.client.ttl(prefixed_key)
            if result == -1:  # Key exists but has no associated expire
                self.logger.debug(f"Key {key} exists without expiration")
                return None
            elif result == -2:  # Key does not exist
                self.logger.debug(f"Key {key} does not exist")
                return None
            else:
                self.logger.debug(f"Key {key} TTL: {result}")
                return result
        except redis.RedisError as e:
            self.logger.error(
                f"Redis error when getting TTL for key {key}: {e}"
            )
            return None

    def expire(self, key: str, /, ttl: int | None = None) -> None:
        """Set or remove expiration for a key."""
        prefixed_key = self.add_prefix(key)
        try:
            if ttl is not None:
                result = self.client.expire(prefixed_key, ttl)
                if result:
                    self.logger.debug(
                        f"Set expiration for key {key}: {ttl} seconds"
                    )
                else:
                    self.logger.warning(
                        f"Failed to set expiration for key {key} (key may not "
                        f"exist)"
                    )
            else:
                result = self.client.persist(prefixed_key)
                if result:
                    self.logger.debug(f"Removed expiration for key: {key}")
                else:
                    self.logger.warning(
                        f"Failed to remove expiration for key {key} (key may "
                        f"not exist)"
                    )
        except redis.RedisError as e:
            self.logger.error(
                f"Redis error when setting expiration for key {key}: {e}"
            )

    def incr(self, key: str, /, amount: int = 1) -> int:
        """Increment a key's value."""
        prefixed_key = self.add_prefix(key)
        try:
            result = self.client.incr(prefixed_key, amount)
            self.logger.debug(
                f"Incremented key {key} by {amount}, result: {result}"
            )
            return result
        except redis.RedisError as e:
            self.logger.error(f"Redis error when incrementing key {key}: {e}")
            return 0

    def decr(self, key: str, /, amount: int = 1) -> int:
        """Decrement a key's value."""
        prefixed_key = self.add_prefix(key)
        try:
            result = self.client.decr(prefixed_key, amount)
            self.logger.debug(
                f"Decremented key {key} by {amount}, result: {result}"
            )
            return result
        except redis.RedisError as e:
            self.logger.error(f"Redis error when decrementing key {key}: {e}")
            return 0

    def keys(self) -> t.List[str]:
        """Return all cache keys (without prefix)."""
        return list(self)

    def values(self) -> t.List[V]:
        """Return all cache values."""
        values = []
        for key in self:
            value = self.get(key)
            if value is not None:
                values.append(value)
        return values

    def items(self) -> t.List[t.Tuple[str, V]]:
        """Return all cache items as (key, value) pairs."""
        items = []
        for key in self:
            value = self.get(key)
            if value is not None:
                items.append((key, value))
        return items

    def init(self) -> None:
        """Initialize cache connection."""
        try:
            self.client.ping()
            self.logger.info("Redis cache connection established successfully")
        except redis.ConnectionError as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    def close(self) -> None:
        """Close cache connection."""
        try:
            self.client.connection_pool.disconnect()
            self.logger.info("Redis cache connection closed")
        except redis.RedisError as e:
            self.logger.warning(f"Error while closing Redis connection: {e}")
