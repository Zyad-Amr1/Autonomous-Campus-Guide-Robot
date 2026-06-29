"""Tests for RAG website source configuration management."""

from controllers.rag.source_config import (
    add_web_source,
    load_web_sources,
    remove_web_source,
    set_web_source_enabled,
)


def test_missing_config_returns_empty_list(tmp_path) -> None:
    config_path = tmp_path / "knowledge_sources" / "web_sources.json"

    assert load_web_sources(config_path) == []
    assert config_path.exists()


def test_add_valid_url(tmp_path) -> None:
    config_path = tmp_path / "web_sources.json"

    source = add_web_source("ECU", "https://example.edu", config_path=config_path)

    assert source == {"name": "ECU", "url": "https://example.edu", "enabled": True}
    assert load_web_sources(config_path) == [source]


def test_duplicate_url_ignored_safely(tmp_path) -> None:
    config_path = tmp_path / "web_sources.json"

    add_web_source("ECU", "https://example.edu", config_path=config_path)
    add_web_source("Duplicate", "https://example.edu", config_path=config_path)

    assert len(load_web_sources(config_path)) == 1


def test_invalid_url_rejected(tmp_path) -> None:
    config_path = tmp_path / "web_sources.json"

    try:
        add_web_source("Bad", "ftp://example.edu", config_path=config_path)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid URL should raise ValueError")


def test_remove_url_works(tmp_path) -> None:
    config_path = tmp_path / "web_sources.json"
    add_web_source("ECU", "https://example.edu", config_path=config_path)

    assert remove_web_source("https://example.edu", config_path=config_path) is True
    assert load_web_sources(config_path) == []


def test_enable_disable_works(tmp_path) -> None:
    config_path = tmp_path / "web_sources.json"
    add_web_source("ECU", "https://example.edu", config_path=config_path)

    assert set_web_source_enabled("https://example.edu", False, config_path=config_path) is True
    assert load_web_sources(config_path)[0]["enabled"] is False
    assert set_web_source_enabled("https://example.edu", True, config_path=config_path) is True
    assert load_web_sources(config_path)[0]["enabled"] is True


def test_invalid_json_does_not_crash(tmp_path) -> None:
    config_path = tmp_path / "web_sources.json"
    config_path.write_text("{not json", encoding="utf-8")

    assert load_web_sources(config_path) == []
