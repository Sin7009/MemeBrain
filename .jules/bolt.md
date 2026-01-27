## 2024-12-13 - [Caching Mutable Objects vs Raw Data]
**Learning:** When optimizing with `lru_cache`, be extremely careful when caching objects that can be modified (like `PIL.Image`).
**Action:** Always cache the immutable raw data (bytes) and reconstruct the object, OR ensure the cached object is deep-copied before use.

## 2024-12-13 - [lru_cache on Instance Methods]
**Learning:** `lru_cache` on instance methods includes `self` in the cache key. This breaks caching if instances are short-lived, and causes memory leaks if they are long-lived (cache holds reference to `self`).
**Action:** Always use `@staticmethod` for cached helper methods or use a class-level cache to avoid `self` issues.

## 2024-12-13 - [Pillow Text Rendering]
**Learning:** `draw.text()` calls in Python are relatively slow compared to the underlying C implementation.
**Action:** Use Pillow's native `stroke_width` and `stroke_fill` parameters instead of manually drawing shadows in a Python loop. This is ~1.85x faster and cleaner.

## 2024-12-13 - [Async Wrapper for Blocking Sync Calls]
**Learning:** Legacy synchronous code (requests, Pillow) inside async handlers blocks the entire event loop, causing severe latency under concurrent load.
**Action:** Use `await asyncio.to_thread(func, *args)` to offload these blocking calls to a thread pool. This simple change provided a ~3x speedup in concurrent request handling.
