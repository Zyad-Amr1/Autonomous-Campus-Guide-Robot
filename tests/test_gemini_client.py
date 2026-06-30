from types import SimpleNamespace

import pytest

from services import gemini_client


class FakeConfig:
    def __init__(self, system_instruction, temperature, max_output_tokens):
        self.system_instruction = system_instruction
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens


@pytest.fixture(autouse=True)
def no_dotenv(monkeypatch):
    monkeypatch.setattr(gemini_client, "load_dotenv", lambda: None)
    monkeypatch.setattr(gemini_client, "_rate_limiter", None)
    monkeypatch.setattr(gemini_client, "_rate_limiter_limit", None)


def _install_fake_config(monkeypatch):
    monkeypatch.setattr(
        gemini_client.types,
        "GenerateContentConfig",
        FakeConfig,
    )


def _install_fake_client(monkeypatch, capture, response=None, exception=None):
    class FakeModels:
        def generate_content(self, model, contents, config):
            capture["call_count"] = capture.get("call_count", 0) + 1
            capture["model"] = model
            capture["contents"] = contents
            capture["config"] = config
            if exception is not None:
                raise exception
            return response

    class FakeClient:
        def __init__(self, api_key):
            capture["api_key"] = api_key
            self.models = FakeModels()

    monkeypatch.setattr(gemini_client.genai, "Client", FakeClient)


def test_missing_gemini_api_key_returns_missing_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)

    result = gemini_client.ask_gemini("Who are the professors?", [])

    assert result == {
        "ok": False,
        "answer": "",
        "error_type": "missing_api_key",
        "model": "gemini-2.5-flash",
    }


def test_context_blocks_are_included_in_prompt(monkeypatch):
    capture = {}
    _install_fake_config(monkeypatch)
    _install_fake_client(
        monkeypatch,
        capture,
        response=SimpleNamespace(text="Engineering is available at ECU."),
    )
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-key")

    gemini_client.ask_gemini(
        "Tell me about engineering",
        [
            {
                "source": "database",
                "title": "Faculty of Engineering",
                "content": "Robotics and software programs.",
            },
            {
                "source": "ecu_website",
                "title": "Engineering page",
                "url": "https://ecu.edu.eg/faculties/engineering-and-technology/",
                "content": "Official ECU engineering information.",
            },
        ],
    )

    assert "Source: database" in capture["contents"]
    assert "Faculty of Engineering" in capture["contents"]
    assert "Robotics and software programs." in capture["contents"]
    assert "Source: ecu_website" in capture["contents"]
    assert "Official ECU engineering information." in capture["contents"]


def test_system_instruction_contains_grounding_rule(monkeypatch):
    capture = {}
    _install_fake_config(monkeypatch)
    _install_fake_client(
        monkeypatch,
        capture,
        response=SimpleNamespace(text="Use the available ECU information."),
    )
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-key")

    gemini_client.ask_gemini("What can you answer?", [])

    assert (
        "Answer ONLY from the provided context"
        in capture["config"].system_instruction
    )


def test_successful_mocked_gemini_response_returns_answer(monkeypatch):
    capture = {}
    _install_fake_config(monkeypatch)
    _install_fake_client(
        monkeypatch,
        capture,
        response=SimpleNamespace(text="The cafeteria is in the Student Center."),
    )
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-key")

    result = gemini_client.ask_gemini("Where is the cafeteria?", [])

    assert result["ok"] is True
    assert result["answer"] == "The cafeteria is in the Student Center."
    assert result["error_type"] is None


def test_empty_mocked_gemini_response_returns_empty_response(monkeypatch):
    capture = {}
    _install_fake_config(monkeypatch)
    _install_fake_client(monkeypatch, capture, response=SimpleNamespace(text="  "))
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-key")

    result = gemini_client.ask_gemini("Tell me something", [])

    assert result["ok"] is False
    assert result["answer"] == ""
    assert result["error_type"] == "empty_response"


def test_mocked_rate_limit_exception_returns_rate_limited(monkeypatch):
    capture = {}
    _install_fake_config(monkeypatch)
    _install_fake_client(monkeypatch, capture, exception=Exception("429 quota exceeded"))
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-key")

    result = gemini_client.ask_gemini("Tell me about ECU", [])

    assert result["ok"] is False
    assert result["error_type"] == "rate_limited"


def test_mocked_generic_exception_returns_api_error(monkeypatch):
    capture = {}
    _install_fake_config(monkeypatch)
    _install_fake_client(monkeypatch, capture, exception=RuntimeError("service down"))
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-key")

    result = gemini_client.ask_gemini("Tell me about ECU", [])

    assert result["ok"] is False
    assert result["error_type"] == "api_error"


def test_model_defaults_to_gemini_2_5_flash(monkeypatch):
    capture = {}
    _install_fake_config(monkeypatch)
    _install_fake_client(monkeypatch, capture, response=SimpleNamespace(text="Answer."))
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-key")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)

    result = gemini_client.ask_gemini("Question", [])

    assert result["model"] == "gemini-2.5-flash"
    assert capture["model"] == "gemini-2.5-flash"


def test_gemini_model_env_var_overrides_default_model(monkeypatch):
    capture = {}
    _install_fake_config(monkeypatch)
    _install_fake_client(monkeypatch, capture, response=SimpleNamespace(text="Answer."))
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-custom-model")

    result = gemini_client.ask_gemini("Question", [])

    assert result["model"] == "gemini-custom-model"
    assert capture["model"] == "gemini-custom-model"


def test_real_api_key_is_not_exposed_in_returned_dict(monkeypatch):
    capture = {}
    secret_key = "real-looking-secret-key"
    _install_fake_config(monkeypatch)
    _install_fake_client(monkeypatch, capture, response=SimpleNamespace(text="Answer."))
    monkeypatch.setenv("GEMINI_API_KEY", secret_key)

    result = gemini_client.ask_gemini("Question", [])

    assert secret_key not in str(result)
    assert capture["api_key"] == secret_key


def test_limiter_allows_requests_under_limit(monkeypatch):
    current_time = {"value": 100.0}
    monkeypatch.setattr(
        gemini_client.time,
        "monotonic",
        lambda: current_time["value"],
    )
    limiter = gemini_client.GeminiRateLimiter(max_requests_per_minute=2)

    assert limiter.can_send_now() is True
    limiter.record_request()

    assert limiter.can_send_now() is True


def test_limiter_blocks_requests_over_limit(monkeypatch):
    current_time = {"value": 100.0}
    monkeypatch.setattr(
        gemini_client.time,
        "monotonic",
        lambda: current_time["value"],
    )
    limiter = gemini_client.GeminiRateLimiter(max_requests_per_minute=1)

    limiter.record_request()

    assert limiter.can_send_now() is False
    assert limiter.seconds_until_available() == 60.0


def test_limiter_expires_old_timestamps_after_60_seconds(monkeypatch):
    current_time = {"value": 100.0}
    monkeypatch.setattr(
        gemini_client.time,
        "monotonic",
        lambda: current_time["value"],
    )
    limiter = gemini_client.GeminiRateLimiter(max_requests_per_minute=1)
    limiter.record_request()

    current_time["value"] = 161.0

    assert limiter.can_send_now() is True
    assert limiter.seconds_until_available() == 0.0


def test_ask_gemini_returns_rate_limited_local_when_limit_exceeded(monkeypatch):
    capture = {}
    _install_fake_config(monkeypatch)
    _install_fake_client(monkeypatch, capture, response=SimpleNamespace(text="Answer."))
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-key")
    monkeypatch.setenv("GEMINI_MAX_REQUESTS_PER_MINUTE", "1")

    first_result = gemini_client.ask_gemini("First question", [])
    second_result = gemini_client.ask_gemini("Second question", [])

    assert first_result["ok"] is True
    assert second_result["ok"] is False
    assert second_result["error_type"] == "rate_limited_local"
    assert second_result["retry_after_seconds"] > 0


def test_locally_rate_limited_does_not_call_gemini_client(monkeypatch):
    capture = {}
    _install_fake_config(monkeypatch)
    _install_fake_client(monkeypatch, capture, response=SimpleNamespace(text="Answer."))
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-key")
    monkeypatch.setenv("GEMINI_MAX_REQUESTS_PER_MINUTE", "1")

    gemini_client.ask_gemini("First question", [])
    gemini_client.ask_gemini("Second question", [])

    assert capture["call_count"] == 1


def test_gemini_max_requests_per_minute_overrides_default(monkeypatch):
    capture = {}
    _install_fake_config(monkeypatch)
    _install_fake_client(monkeypatch, capture, response=SimpleNamespace(text="Answer."))
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-key")
    monkeypatch.setenv("GEMINI_MAX_REQUESTS_PER_MINUTE", "1")

    gemini_client.ask_gemini("First question", [])
    result = gemini_client.ask_gemini("Second question", [])

    assert result["error_type"] == "rate_limited_local"
    assert capture["call_count"] == 1


def test_invalid_gemini_max_requests_per_minute_falls_back_safely(monkeypatch):
    capture = {}
    _install_fake_config(monkeypatch)
    _install_fake_client(monkeypatch, capture, response=SimpleNamespace(text="Answer."))
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-key")
    monkeypatch.setenv("GEMINI_MAX_REQUESTS_PER_MINUTE", "not-a-number")

    first_result = gemini_client.ask_gemini("First question", [])
    second_result = gemini_client.ask_gemini("Second question", [])

    assert first_result["ok"] is True
    assert second_result["ok"] is True
    assert capture["call_count"] == 2
