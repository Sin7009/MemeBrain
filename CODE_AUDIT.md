# Code Quality Audit Report

**Date:** 2024-05-22
**Auditor:** Senior Technical Lead
**Scope:** `src/`, `tests/`

---

## 1. Ghost Code & Imports

### `src/bot/handlers.py`
*   **[LOW]** Unused imports/Commented Code: Logic for Face Swap is heavily commented out.
    *   *Action:* Remove commented code blocks for Face Swap if not planned for immediate release, or move to a feature branch.
*   **[LOW]** Verbose Comments: Long explanation about `MessageReactionUpdated` API limitations.
    *   *Action:* Condense into a concise docstring or link to internal wiki.

### `src/services/face_swap.py`
*   **[MEDIUM]** Dead Code: Entire class is a stub with commented-out dependencies (`insightface`, `cv2`).
    *   *Action:* Delete file if feature is postponed, or properly mock dependencies to avoid import errors.

### `src/main.py`
*   **[LOW]** `load_dotenv` inside `if __name__`.
    *   *Action:* Move `load_dotenv()` to the top of the file to ensure env vars are loaded for all modules if imported.

---

## 2. Documentation & Naming

### `src/bot/handlers.py`
*   **[MEDIUM]** Complex Function: `reaction_handler` is ~90 lines long with mixed responsibilities (history check, LLM call, Search call, Image Gen, Error handling).
    *   *Action:* Extract logic into a `MemeOrchestrator` service class.
*   **[HIGH]** Dangerous Global: `TEMP_OUTPUT_FILE = "temp_meme.jpg"`. This name implies a temporary variable but acts as a global shared resource.
    *   *Action:* Use `tempfile.NamedTemporaryFile` inside the handler scope.

### `src/services/image_gen.py`
*   **[LOW]** Hardcoded Constants: `MAX_SIZE` (5MB) defined inside `_download_image_bytes`.
    *   *Action:* Move to `src/services/config.py`.

---

## 3. TODO Archeology

### `src/bot/handlers.py`
*   `# 5. Face Swap (опционально)`
*   `# NOTE: В реальном проекте FaceSwapper...`
    *   *Action:* Convert to GitHub Issues or Jira tickets and remove comments.

### `src/services/face_swap.py`
*   `# Тут будет логика инициализации...`
    *   *Action:* Implement or remove.

---

## 4. Security Sanity Check

### `src/bot/handlers.py`
*   **[HIGH]** **Race Condition:** `TEMP_OUTPUT_FILE` is a static filename. Concurrent users will overwrite each other's memes, leading to data leakage (User A sees User B's meme).
    *   *Action:* **IMMEDIATE FIX REQUIRED.** Use `tempfile` module or unique filenames (e.g., `uuid`).

### `src/services/search.py`
*   **[MEDIUM]** Error Logging: `print(f"... {e}")` might leak API keys if they are part of the URL parameters in the exception message (common with `requests`).
    *   *Action:* Use `logging` and ensure sensitive data is sanitized before logging.

### General
*   **[MEDIUM]** Logging: Widespread use of `print()` instead of `logging` module. `print` is not thread-safe and lacks metadata (time, level).
    *   *Action:* Replace all `print()` calls with `logging.info/error`.

---

## Summary of Critical Actions

1.  **Fix Race Condition:** Eliminate `TEMP_OUTPUT_FILE` global.
2.  **Sanitize Logs:** Ensure `requests` exceptions do not log API keys.
3.  **Cleanup:** Remove Face Swap stub if not in use.
