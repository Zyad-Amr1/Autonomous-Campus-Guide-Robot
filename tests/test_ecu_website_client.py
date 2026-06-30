import requests

from services.ecu_website_client import (
    ECU_WEBSITE_PAGES,
    fetch_ecu_page,
    retrieve_from_website,
    select_ecu_website_page,
)


class FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code


def test_successful_html_returns_cleaned_visible_text(monkeypatch):
    def fake_get(url, headers, timeout):
        return FakeResponse(
            """
            <html>
                <body>
                    <main>
                        ECU University Profile
                        <p>Engineering and Computer Science programs.</p>
                        <p>مرحبا بكم في الجامعة</p>
                    </main>
                </body>
            </html>
            """
        )

    monkeypatch.setattr("services.ecu_website_client.requests.get", fake_get)

    text = fetch_ecu_page("about-ecu/university-profile/")

    assert text == (
        "ECU University Profile Engineering and Computer Science programs. "
        "مرحبا بكم في الجامعة"
    )


def test_noisy_tags_are_removed(monkeypatch):
    def fake_get(url, headers, timeout):
        return FakeResponse(
            """
            <html>
                <header>Header menu</header>
                <nav>Navigation links</nav>
                <body>
                    <script>tracking code</script>
                    <style>.hidden { display: none; }</style>
                    <noscript>Enable scripts</noscript>
                    <svg>icon label</svg>
                    <main>Visible ECU admissions information for students.</main>
                </body>
                <footer>Footer contacts</footer>
            </html>
            """
        )

    monkeypatch.setattr("services.ecu_website_client.requests.get", fake_get)

    text = fetch_ecu_page("admissions/")

    assert text == "Visible ECU admissions information for students."
    assert "Header menu" not in text
    assert "Navigation links" not in text
    assert "tracking code" not in text
    assert "Footer contacts" not in text


def test_timeout_or_request_exception_returns_none(monkeypatch):
    def fake_get(url, headers, timeout):
        raise requests.Timeout("request timed out")

    monkeypatch.setattr("services.ecu_website_client.requests.get", fake_get)

    assert fetch_ecu_page("about-ecu/university-profile/") is None


def test_non_200_response_returns_none(monkeypatch):
    def fake_get(url, headers, timeout):
        return FakeResponse("Page missing", status_code=404)

    monkeypatch.setattr("services.ecu_website_client.requests.get", fake_get)

    assert fetch_ecu_page("missing-page/") is None


def test_empty_html_returns_none(monkeypatch):
    def fake_get(url, headers, timeout):
        return FakeResponse("<html><body> </body></html>")

    monkeypatch.setattr("services.ecu_website_client.requests.get", fake_get)

    assert fetch_ecu_page("empty/") is None


def test_path_with_leading_slash_still_works_safely(monkeypatch):
    calls = {}

    def fake_get(url, headers, timeout):
        calls["url"] = url
        return FakeResponse("Visible ECU profile content for students.")

    monkeypatch.setattr("services.ecu_website_client.requests.get", fake_get)

    assert fetch_ecu_page("/about-ecu/university-profile/")
    assert calls["url"] == "https://ecu.edu.eg/about-ecu/university-profile/"


def test_requests_get_is_called_with_timeout_5(monkeypatch):
    calls = {}

    def fake_get(url, headers, timeout):
        calls["timeout"] = timeout
        return FakeResponse("Visible ECU profile content for students.")

    monkeypatch.setattr("services.ecu_website_client.requests.get", fake_get)

    fetch_ecu_page("about-ecu/university-profile/")

    assert calls["timeout"] == 5


def test_user_agent_header_is_sent(monkeypatch):
    calls = {}

    def fake_get(url, headers, timeout):
        calls["headers"] = headers
        return FakeResponse("Visible ECU profile content for students.")

    monkeypatch.setattr("services.ecu_website_client.requests.get", fake_get)

    fetch_ecu_page("about-ecu/university-profile/")

    assert "User-Agent" in calls["headers"]
    assert "Mozilla/5.0" in calls["headers"]["User-Agent"]


def test_ecu_website_pages_exists_and_is_not_empty():
    assert ECU_WEBSITE_PAGES


def test_every_page_has_title_path_and_keywords():
    for page in ECU_WEBSITE_PAGES.values():
        assert page["title"]
        assert page["path"]
        assert page["keywords"]
        assert isinstance(page["keywords"], list)


def test_engineering_query_selects_engineering_page():
    page = select_ecu_website_page("Tell me about engineering technology")

    assert page["key"] == "engineering"
    assert page["title"] == "Faculty of Engineering and Technology"


def test_computers_ai_query_selects_computers_page():
    page = select_ecu_website_page("AI and cybersecurity programs")

    assert page["key"] == "computers"


def test_arabic_engineering_query_selects_engineering_page():
    page = select_ecu_website_page("ما هي كلية هندسة؟")

    assert page["key"] == "engineering"


def test_pharmacy_query_selects_pharmacy_page():
    page = select_ecu_website_page("pharmd pharmacy program")

    assert page["key"] == "pharmacy"


def test_unrelated_query_returns_none():
    assert select_ecu_website_page("weather forecast today") is None


def test_selected_page_path_does_not_start_with_full_url():
    page = select_ecu_website_page("engineering")

    assert not page["path"].startswith("http")


def test_selected_page_path_can_be_passed_to_fetch_later(monkeypatch):
    calls = {}

    def fake_get(url, headers, timeout):
        calls["url"] = url
        return FakeResponse("Visible ECU engineering content for students.")

    monkeypatch.setattr("services.ecu_website_client.requests.get", fake_get)
    page = select_ecu_website_page("engineering")

    assert fetch_ecu_page(page["path"])
    assert calls["url"] == "https://ecu.edu.eg/faculties/engineering-and-technology/"


def test_retrieve_from_website_returns_none_for_unrelated_query():
    assert retrieve_from_website("weather forecast today") is None


def test_retrieve_from_website_returns_none_when_fetch_fails(monkeypatch):
    def fake_fetch(path):
        return None

    monkeypatch.setattr("services.ecu_website_client.fetch_ecu_page", fake_fetch)

    assert retrieve_from_website("engineering") is None


def test_retrieve_from_website_returns_dict_when_fetch_succeeds(monkeypatch):
    def fake_fetch(path):
        return "Visible ECU engineering content for chatbot context."

    monkeypatch.setattr("services.ecu_website_client.fetch_ecu_page", fake_fetch)

    result = retrieve_from_website("engineering")

    assert result["source"] == "ecu_website"
    assert result["title"] == "Faculty of Engineering and Technology"
    assert result["url"] == "https://ecu.edu.eg/faculties/engineering-and-technology/"
    assert result["path"] == "faculties/engineering-and-technology/"
    assert result["content"] == "Visible ECU engineering content for chatbot context."


def test_retrieve_from_website_result_has_required_fields(monkeypatch):
    def fake_fetch(path):
        return "Visible ECU pharmacy content for chatbot context."

    monkeypatch.setattr("services.ecu_website_client.fetch_ecu_page", fake_fetch)

    result = retrieve_from_website("pharmacy")

    assert result["source"] == "ecu_website"
    assert result["title"]
    assert result["url"]
    assert result["path"]
    assert result["content"]


def test_retrieve_from_website_url_starts_with_ecu_base_url(monkeypatch):
    def fake_fetch(path):
        return "Visible ECU computers content for chatbot context."

    monkeypatch.setattr("services.ecu_website_client.fetch_ecu_page", fake_fetch)

    result = retrieve_from_website("computers")

    assert result["url"].startswith("https://ecu.edu.eg/")


def test_retrieve_from_website_trims_long_content(monkeypatch):
    long_content = ("ECU engineering sentence. " * 400).strip()

    def fake_fetch(path):
        return long_content

    monkeypatch.setattr("services.ecu_website_client.fetch_ecu_page", fake_fetch)

    result = retrieve_from_website("engineering")

    assert len(result["content"]) <= 6000
    assert result["content"].endswith(".")


def test_retrieve_from_website_fetches_selected_path(monkeypatch):
    calls = {}

    def fake_fetch(path):
        calls["path"] = path
        return "Visible ECU engineering content for chatbot context."

    monkeypatch.setattr("services.ecu_website_client.fetch_ecu_page", fake_fetch)

    retrieve_from_website("engineering")

    assert calls["path"] == "faculties/engineering-and-technology/"


def test_retrieve_from_website_returns_none_if_fetch_raises(monkeypatch):
    def fake_fetch(path):
        raise RuntimeError("unexpected fetch failure")

    monkeypatch.setattr("services.ecu_website_client.fetch_ecu_page", fake_fetch)

    assert retrieve_from_website("engineering") is None
