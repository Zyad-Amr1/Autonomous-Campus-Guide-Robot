from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_env_example_exists():
    assert (ROOT / ".env.example").exists()


def test_env_example_contains_gemini_settings():
    content = (ROOT / ".env.example").read_text(encoding="utf-8")

    assert "GEMINI_API_KEY" in content
    assert "GEMINI_MODEL" in content


def test_gitignore_ignores_real_env_file():
    content = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert ".env" in content
