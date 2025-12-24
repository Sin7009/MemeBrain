# Code Quality & Audit Report

## 1. Ghost Code & Imports

### `src/bot/handlers.py`
*   **[LOW] Unused Variable:** `TEMP_OUTPUT_FILE` is defined but seemingly replaced by `unique_output_file`. The comment acknowledges this technical debt.
    *   *Action:* Remove `TEMP_OUTPUT_FILE` if `unique_output_file` is fully verified.
*   **[MEDIUM] Ghost Code:** `face_swapper = FaceSwapper()` is initialized but never used in any handler.
    *   *Action:* Remove the initialization if Face Swap is not enabled.

### `src/services/face_swap.py`
*   **[HIGH] Ghost Code:** The entire file is commented out code. The class `FaceSwapper` has no active methods.
    *   *Action:* Delete the file or uncomment and fix if the feature is needed.

### `src/utils.py`
*   **[LOW] Unused Function:** `clean_filename` is defined but does not appear to be used in `handlers.py` (which constructs filenames manually).
    *   *Action:* Use `clean_filename` in `handlers.py` or remove it.

### `src/services/history.py`
*   **[LOW] Unused Logic:** `get_message_text` returns `None` (or empty string in some versions) but `handlers.py` seems to rely on `get_context` mostly.
    *   *Action:* Verify usage and unify return types (Optional[str] vs str).

## 2. Documentation & Naming

### `src/bot/handlers.py`
*   **[LOW] Naming:** Global variables `meme_brain`, `image_searcher` are instantiated at module level.
    *   *Action:* Consider wrapping them in a dependency injection container or a `BotContext` class.
*   **[LOW] Naming:** `reaction_handler` logic uses a complex lambda in the decorator.
    *   *Action:* Extract the lambda to a named function `is_meme_trigger`.

### `src/services/config.py`
*   **[LOW] Hardcoded Values:** `OPENROUTER_MODEL` default is specific ("google/gemini-3-flash-preview").
    *   *Action:* Ensure this defaults to a stable model alias if possible.

### `src/main.py`
*   **[LOW] Comments:** Mix of Russian and English comments.
    *   *Action:* Standardize on English for code comments.

## 3. TODO Archeology

*   **`src/bot/handlers.py`**: "But for preserving logic with TEMP_OUTPUT_FILE we will use it for now...".
    *   *Action:* Refactor to remove dependency on `TEMP_OUTPUT_FILE` concept completely.
*   **`src/services/face_swap.py`**: "ЗАГЛУШКА для сервиса Face Swap."
    *   *Action:* Decide on the future of this feature (implement or delete).
*   **`src/services/image_gen.py`**: "For newer Pillow versions, default size might be needed..."
    *   *Action:* Verify Pillow version compatibility and remove speculative comment.

## 4. Security Sanity Check

### `src/services/search.py`
*   **[MEDIUM] Hardcoded URL:** `https://api.tavily.com/search` is hardcoded.
    *   *Action:* Move to `config.py` as `TAVILY_API_URL`.
*   **[LOW] Error Logging:** Good practice observed (`Sentinel: Sanitize error logs`). Ensure this pattern is consistent across all external API calls (LLM, Telegram).

### `src/bot/handlers.py`
*   **[LOW] HTML Generation:** Uses `html.escape`, which is good. Ensure all user inputs (including `trigger_emoji`) are escaped if rendered.

## Summary
The codebase is relatively clean but has some "scaffolding" left from rapid development (Face Swap stub, temporary file naming). The primary focus should be cleaning up the `face_swap.py` ghost code and standardizing the configuration/instantiation of services.
