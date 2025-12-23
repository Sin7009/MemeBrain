# Code Quality Audit Report

## `src/main.py`
*   **[LOW] Ghost Code:** `load_dotenv` imported inside `if __name__ == "__main__":`.
    *   *Action:* Move `from dotenv import load_dotenv` to top-level imports or remove if handled by `pydantic-settings` (it usually is).
*   **[MEDIUM] Documentation:** `main` function lacks a docstring.
    *   *Action:* Add a docstring explaining the entry point logic.

## `src/utils.py`
*   **[LOW] Ghost Code:** `clean_filename` function is defined but never used in the codebase.
    *   *Action:* Remove `clean_filename` function if confirmed unnecessary.
*   **[LOW] Ghost Code:** `print` statements used in `safe_json_parse`.
    *   *Action:* Replace `print` with `logging.error` or `logging.warning`.
*   **[MEDIUM] Documentation:** Inconsistent docstring languages (Russian vs. English).
    *   *Action:* Standardize docstrings to English (or Russian, but be consistent).

## `src/bot/handlers.py`
*   **[LOW] Ghost Code:** `TEMP_OUTPUT_FILE` constant is unused; logic uses `unique_output_file`.
    *   *Action:* Remove `TEMP_OUTPUT_FILE` constant.
*   **[LOW] Ghost Code:** `face_swapper` instance is initialized but never used in any handler.
    *   *Action:* Remove `face_swapper` initialization and import until the feature is implemented.
*   **[MEDIUM] Complexity:** `generate_and_send_meme` is a complex function (> 15 lines) handling multiple responsibilities.
    *   *Action:* Refactor `generate_and_send_meme` into smaller helper functions (e.g., `_generate_meme_content`, `_send_meme_to_chat`).
*   **[LOW] Naming:** Variable name `bot_instance` is verbose.
    *   *Action:* Rename `bot_instance` to `bot`.

## `src/services/face_swap.py`
*   **[HIGH] Ghost Code:** Entire class is a placeholder with large commented-out blocks (`insightface`, `cv2`, `onnxruntime`).
    *   *Action:* Remove the file if face swap is not planned for immediate release, or use a proper feature flag mechanism without commenting out code.
*   **[LOW] Ghost Code:** `print` statements used for logging.
    *   *Action:* Replace `print` with `logging`.
*   **[LOW] TODO Archeology:** Implicit TODOs in comments: `# Тут будет логика...`, `# ВАЖНО...`.
    *   *Action:* Convert these to explicit `# TODO: Implement ...` markers or track in issue tracker.

## `src/services/image_gen.py`
*   **[LOW] Ghost Code:** `_download_image_bytes` uses `print` for errors.
    *   *Action:* Replace `print` with `logging`.

## `src/services/config.py`
*   **[MEDIUM] Documentation:** Inconsistent docstring languages (Russian vs. English).
    *   *Action:* Standardize docstrings to English.
*   **[LOW] Security:** `OPENROUTER_MODEL` default value `google/gemini-3-flash-preview` is hardcoded.
    *   *Action:* Ensure this defaults to a stable model or is purely environment-driven.

## `src/services/search.py`
*   **[LOW] Security:** `API_URL` is hardcoded (`https://api.tavily.com/search`).
    *   *Action:* Move `API_URL` to `config.py` (low priority, but good practice).
