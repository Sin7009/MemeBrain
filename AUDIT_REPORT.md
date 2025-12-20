# Code Quality & Security Audit Report

## Summary
This audit identifies areas of technical debt, "ghost code" (unused/commented logic), documentation gaps, and potential security improvements. The focus is on maintainability and hygiene without altering core business logic.

## Findings

### `src/bot/handlers.py`
**Severity:** [MEDIUM]
*   **Ghost Code:** `TEMP_OUTPUT_FILE` constant is defined but unused (replaced by `unique_output_file` in logic).
    *   *Action:* Remove `TEMP_OUTPUT_FILE` and update comments to reflect the actual race-condition-free implementation.
*   **Naming:** `bot_instance` variable name in `generate_and_send_meme` is slightly verbose.
    *   *Action:* Rename `bot_instance` to `bot` (standard aiogram convention).
*   **Error Handling:** Uses `print(...)` for error logging instead of the configured `logging` module.
    *   *Action:* Replace `print` with `logging.error`.

### `src/services/face_swap.py`
**Severity:** [HIGH]
*   **Ghost Code:** The `FaceSwapper` class is effectively a placeholder/ghost feature. Core logic is commented out.
    *   *Action:* Move file to `prototypes/` or delete until feature is actively developed to reduce noise.
*   **TODO Archeology:** Heavy "TODO-style" comments (`# Тут будет логика...`, `# ВАЖНО: Комментируем...`).
    *   *Action:* Convert to standard `TODO` markers or track in issue tracker; remove code comments.

### `src/utils.py`
**Severity:** [LOW]
*   **Ghost Code:** `clean_filename` function is defined but not used anywhere in the codebase.
    *   *Action:* Remove `clean_filename` function.
*   **Error Handling:** Uses `print(...)` inside `safe_json_parse`.
    *   *Action:* Replace `print` with `logging.warning`.

### `src/services/image_gen.py`
**Severity:** [LOW]
*   **Documentation/Structure:** `get_text_width` and `get_text_size` are helper functions defined *inside* methods.
    *   *Action:* Refactor these into private static methods (e.g., `_get_text_width`) to declutter the main logic.
*   **Error Handling:** Uses `print(...)` for logging errors (e.g., network issues, image size limits).
    *   *Action:* Replace `print` with `logging.error` or `logging.warning`.

### `src/services/llm.py`
**Severity:** [LOW]
*   **Security/Configuration:** `HTTP-Referer` header is hardcoded to a placeholder (`https://t.me/your_meme_bot`).
    *   *Action:* Move this value to `src/services/config.py` as `BOT_URL`.
*   **Error Handling:** Uses `print(...)` for API errors.
    *   *Action:* Replace `print` with `logging.error`.

### `src/services/search.py`
**Severity:** [LOW]
*   **Error Handling:** Uses `print(...)` for errors.
    *   *Action:* Replace `print` with `logging.error`.

## Security Sanity Check

1.  **Race Condition:** The potential race condition in `handlers.py` (file collisions) was previously identified but **has been fixed** in the code (`unique_output_file`). However, the confusing comments and unused `TEMP_OUTPUT_FILE` constant remain, creating a risk that someone might revert to the "simple" (broken) logic based on the comments.
2.  **Secrets:** No hardcoded API keys found. Mocks are enabled/disabled via config.
3.  **Input Sanitization:** `html.escape` is correctly used in `handlers.py`.
