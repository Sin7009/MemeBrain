# Code Quality & Security Audit Report

## Summary
This audit identifies areas of technical debt, "ghost code" (unused/commented logic), documentation gaps, and potential security improvements. The focus is on maintainability and hygiene without altering core business logic.

## Findings

### `src/services/face_swap.py`
**Severity:** [MEDIUM]
*   **Ghost Code:** The `FaceSwapper` class is effectively a placeholder. Core logic imports (`cv2`, `insightface`) and implementation are commented out to prevent `ImportError` in the MVP environment. The `swap_face` method acts as a pass-through.
*   **TODO Archeology:**
    *   `# --- ВАЖНО --- Комментируем все импорты...`
    *   `# Тут будет логика инициализации InsightFace...`
    *   `# Тут должна быть реальная логика InsightFace`
*   **Action:** If face swapping is not planned for the immediate next release, remove the file or move it to a `prototypes/` directory to declutter the production codebase. Alternatively, implement a proper feature flag check that doesn't rely on commented-out imports.

### `src/bot/handlers.py`
**Severity:** [MEDIUM]
*   **Ghost Code:** `FaceSwapper` is imported and instantiated (`face_swapper = FaceSwapper()`), but its logic is skipped in the pipeline (`# 5. Face Swap (опционально)...`).
*   **Ghost Code:** `FSInputFile` is imported but `aiogram.types` exposes it. `html` is used correctly.
*   **Global State/Race Condition:** `TEMP_OUTPUT_FILE = "temp_meme.jpg"` is a global constant. In a concurrent environment (e.g., multiple users triggering memes simultaneously), this will cause file collisions and race conditions.
*   **Hardcoded Configuration:** `MEME_TRIGGERS` list is hardcoded.
*   **Error Handling:** Uses `print(...)` for error logging instead of the configured `logging` module.
*   **TODO Archeology:**
    *   `# !!! Важно: в Telegram API/aiogram...` (regarding getting message text)
    *   `# NOTE: В реальном проекте FaceSwapper...`
*   **Action:**
    *   Remove unused `FaceSwapper` instantiation.
    *   **CRITICAL:** Replace `TEMP_OUTPUT_FILE` with a unique filename generator (e.g., `tempfile` module or `uuid`) to prevent race conditions.
    *   Move `MEME_TRIGGERS` to `src/services/config.py`.
    *   Replace `print` with `logging.error`.

### `src/services/image_gen.py`
**Severity:** [LOW]
*   **Documentation:** `_wrap_text` function logic is complex; the inner functions `get_text_width` and `get_text_size` could be refactored into private helper methods for better readability.
*   **Error Handling:** Uses `print(...)` for logging errors (e.g., network issues, image size limits).
*   **Ghost Code:** `UnidentifiedImageError` is imported.
*   **Action:** Replace `print` with `logging`. Extract inner functions in `_wrap_text` to class methods.

### `src/utils.py`
**Severity:** [LOW]
*   **Naming:** Variable `text` is shadowed/reused inside `safe_json_parse`.
*   **Error Handling:** Uses `print(...)` for JSON parse errors.
*   **Action:** Rename internal variable (e.g., `clean_text`). Replace `print` with `logging.warning`.

### `src/services/search.py`
**Severity:** [LOW]
*   **Error Handling:** Uses `print(...)` for errors.
*   **Action:** Replace `print` with `logging.error`.

### `src/services/llm.py`
**Severity:** [LOW]
*   **Hardcoded Values:** Model name `"openai/gpt-4o-mini"` is hardcoded as a default in `config.py`, which is fine, but the fallback/usage in `llm.py` relies on `config.OPENROUTER_MODEL`.
*   **Error Handling:** Uses `print(...)` for API errors.
*   **Action:** Replace `print` with `logging.error`.

### `src/main.py`
**Severity:** [LOW]
*   **Logging:** Implicitly uses `print` via `logging` (which is configured to stdout). This is acceptable but could be more structured (JSON logs) for production.
*   **Action:** None required for MVP, but consider structured logging later.

## Security & Reliability Sanity Check

1.  **Race Condition (`src/bot/handlers.py`):** The use of a static `temp_meme.jpg` filename is a high-risk issue for a multi-user bot. **Refactor immediately** to use unique temporary filenames.
2.  **API Keys:** No hardcoded keys found. All keys are correctly loaded from `src/services/config.py`.
3.  **Input Sanitization:** `src/bot/handlers.py` uses `html.escape` before sending text to Telegram, preventing HTML injection. `src/services/image_gen.py` validates image size and content length.
4.  **Error Leakage:** `src/services/search.py` actively sanitizes exception messages to avoid leaking API keys in logs. This is a good practice.

## Conclusion
The codebase is generally clean but exhibits typical "MVP shortcuts" like `print` debugging and placeholder logic for features not yet implemented (Face Swap). The most critical technical debt to address is the **file collision risk** in `src/bot/handlers.py`.
