import pytest
from pydantic import ValidationError

from src.services.config import Settings, get_settings


def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "dummy")
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy")
    monkeypatch.setenv("TAVILY_API_KEY", "dummy")

    cfg = get_settings()

    assert isinstance(cfg, Settings)
    assert cfg.TELEGRAM_BOT_TOKEN == "dummy"
    assert cfg.OPENROUTER_API_KEY == "dummy"
    assert cfg.TAVILY_API_KEY == "dummy"


def test_settings_validation_error_when_required_missing(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # pyright: ignore[reportCallIssue]


def test_settings_bool_flags(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "dummy")
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy")
    monkeypatch.setenv("TAVILY_API_KEY", "dummy")
    monkeypatch.setenv("LLM_MOCK_ENABLED", "true")
    monkeypatch.setenv("SEARCH_MOCK_ENABLED", "1")
    monkeypatch.setenv("MAX_CONCURRENT_GENERATIONS", "4")

    cfg = Settings(_env_file=None)  # pyright: ignore[reportCallIssue]

    assert cfg.LLM_MOCK_ENABLED is True
    assert cfg.SEARCH_MOCK_ENABLED is True
    assert cfg.MAX_CONCURRENT_GENERATIONS == 4
