## 2024-12-13 - [Caching Mutable Objects vs Raw Data]
**Learning:** When optimizing with `lru_cache`, be extremely careful when caching objects that can be modified (like `PIL.Image`).
**Action:** Always cache the immutable raw data (bytes) and reconstruct the object, OR ensure the cached object is deep-copied before use.

## 2024-12-13 - [lru_cache on Instance Methods]
**Learning:** `lru_cache` on instance methods includes `self` in the cache key. This breaks caching if instances are short-lived, and causes memory leaks if they are long-lived (cache holds reference to `self`).
**Action:** Always use `@staticmethod` for cached helper methods or use a class-level cache to avoid `self` issues.

## 2024-12-13 - [Pillow Text Rendering]
**Learning:** `draw.text()` calls in Python are relatively slow compared to the underlying C implementation.
**Action:** Use Pillow's native `stroke_width` and `stroke_fill` parameters instead of manually drawing shadows in a Python loop. This is ~1.85x faster and cleaner.
