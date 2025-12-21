# GitHub Copilot Instructions for MemeBrain

## Project Overview

MemeBrain is a Telegram bot that automatically generates situational memes directly in chat. The bot activates when users react to messages with specific emoji triggers (🤡, 🔥, ❤, etc.), analyzes the conversation context using LLM, searches for appropriate meme templates, and generates memes with text overlay.

## Tech Stack

- **Python 3.10+**: Primary programming language
- **aiogram 3.x**: Telegram Bot API framework for asynchronous bot development
- **OpenAI SDK**: For LLM integration via OpenRouter API
- **Pillow**: Image processing and text overlay for meme generation
- **pydantic-settings**: Configuration management with validation
- **pytest**: Testing framework for unit and integration tests

## Architecture

### Project Structure
```
src/
├── main.py              # Bot entry point with async main loop
├── bot/
│   └── handlers.py      # Message and reaction handlers
├── services/
│   ├── config.py        # Configuration with environment variables
│   ├── history.py       # Chat message history management
│   ├── llm.py           # LLM integration (OpenRouter/GPT)
│   ├── search.py        # Meme template image search
│   ├── image_gen.py     # Image generation with text overlay
│   └── face_swap.py     # Face swap functionality (future feature)
└── utils.py             # Utility functions
```

### Key Components

1. **History Manager**: Stores and manages conversation context (last N messages per chat)
2. **MemeBrain (LLM)**: Analyzes context and generates meme text + search queries
3. **Image Searcher**: Finds meme templates via external search APIs
4. **Meme Generator**: Overlays text on images in classic meme style
5. **Face Swapper**: Planned feature for personalized memes (not implemented in MVP)

## Code Conventions

### Python Style
- Use **Russian comments and docstrings** for consistency with existing codebase
- Follow Python naming conventions: `snake_case` for functions/variables, `PascalCase` for classes
- Use type hints where applicable (but not strictly enforced)
- Async/await pattern for all I/O operations

### Imports
- Group imports: standard library → third-party → local imports
- Use relative imports for local modules (e.g., `from ..services.config import config`)

### Error Handling
- Use try-except blocks for external API calls
- Log errors with `logging` module
- Graceful degradation: mock modes available for testing without API calls

### Configuration
- All configuration via environment variables in `.env` file
- Use `pydantic-settings` for type-safe configuration
- Never hardcode API keys or sensitive data

## Patterns and Best Practices

### Async Programming
- Always use `async def` for handlers and I/O operations
- Use `await` for all async calls (bot operations, HTTP requests, etc.)
- Properly handle async context managers

### Service Layer Pattern
- Each service is a class with clear responsibility
- Services are initialized once at module level in handlers
- Services can be mocked for testing (via `MOCK_ENABLED` flags)

### Message History
```python
# History is stored per chat_id
history_manager.add_message(chat_id, username, text)
context = history_manager.get_context(chat_id)
```

### LLM Integration
- Use structured output with JSON schema for predictable responses
- Always validate and parse LLM responses safely
- Include reaction context in prompts for better meme relevance

### Image Generation
- Classic meme style: white Impact font with black stroke
- Text wrapping handled automatically
- Handle edge cases (tiny images, empty text, etc.)

## Testing Strategy

### Test Types
1. **Unit Tests**: Test individual services (history, image_gen, llm)
2. **Integration Tests**: Test full meme generation pipeline with mocks
3. **Destructive Tests**: Test edge cases and error handling

### Running Tests
```bash
# Unit tests
python -m unittest test_history.py

# Integration test (with mocks)
python test_generation.py

# Destructive tests
pytest test_destructive_meme.py
```

### Mock Modes
- `LLM_MOCK_ENABLED=True`: Skip LLM API calls, use predefined responses
- `SEARCH_MOCK_ENABLED=True`: Skip image search, use local test images
- Use mocks for CI/CD and local development without API costs

## Important Considerations

### Telegram Bot Setup
- Bot requires **Group Privacy disabled** in BotFather to read all messages
- Bot monitors reactions via `MessageReactionUpdated` event
- Supports multiple emoji triggers with semantic meanings

### Performance
- History is stored in-memory (per-chat dictionary)
- No database in MVP; suitable for small-scale deployment
- Consider caching for template images in future

### Security
- Never commit `.env` file (already in `.gitignore`)
- Validate all user inputs before processing
- Be cautious with generated content (future: add moderation)

### Localization
- Primary language: **Russian** (comments, logs, user messages)
- Meme text can be in any language based on context

## Future Features (Roadmap)

When implementing these, maintain backward compatibility:
- **Face Swap**: Replace faces on meme templates (requires `insightface`, GPU)
- **Template Caching**: Store frequently used templates locally
- **Content Moderation**: Check for NSFW/toxic content
- **Image/Sticker Analysis**: Generate memes from images using Vision LLM
- **Custom Reactions**: User-configurable trigger emoji

## Common Tasks

### Adding New Emoji Triggers
Edit `MEME_TRIGGERS` dict in `src/bot/handlers.py`:
```python
MEME_TRIGGERS = {
    "🎯": "Точно в цель, попадание",
    # ... existing triggers
}
```

### Modifying LLM Prompt
Edit prompt in `src/services/llm.py` → `generate_meme_idea()` method

### Changing History Size
Set `HISTORY_SIZE` in `.env` file (default: 10 messages)

### Adding New Service
1. Create new file in `src/services/`
2. Import and initialize in `src/bot/handlers.py`
3. Use in handler functions as needed

## Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from BotFather | ✅ Yes | - |
| `OPENROUTER_API_KEY` | OpenRouter API key for LLM | ✅ Yes | - |
| `OPENROUTER_MODEL` | LLM model to use | No | `google/gemini-3-flash-preview` |
| `TAVILY_API_KEY` | Tavily API key for image search | ✅ Yes | - |
| `HISTORY_SIZE` | Number of messages to keep in context | No | `10` |
| `FACE_SWAP_ENABLED` | Enable face swap feature | No | `False` |
| `LLM_MOCK_ENABLED` | Use mock LLM responses for testing | No | `False` |
| `SEARCH_MOCK_ENABLED` | Use mock image search for testing | No | `False` |

## Tips for Development

1. **Always test with mocks first** to avoid API costs during development
2. **Use logging liberally** for debugging async issues
3. **Handle Unicode properly** - Telegram supports emoji and multilingual text
4. **Keep handlers lightweight** - move logic to service layer
5. **Write tests for new features** - follow existing test patterns
6. **Document configuration changes** in README.md

## When Suggesting Code

- Prefer async/await over sync operations
- Use existing service patterns and abstractions
- Add appropriate error handling and logging
- Consider edge cases (empty messages, API failures, etc.)
- Follow the Russian comment convention for consistency
- Keep changes minimal and focused
- Test with mock modes before suggesting API integrations
