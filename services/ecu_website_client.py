"""Safe single-page ECU website text fetching."""

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://ecu.edu.eg/"
REQUEST_TIMEOUT_SECONDS = 5
MIN_TEXT_LENGTH = 20
MAX_CONTENT_LENGTH = 6000
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)
NOISY_TAGS = ("script", "style", "nav", "footer", "header", "noscript", "svg")
ECU_WEBSITE_PAGES = {
    "about": {
        "title": "ECU University Profile",
        "path": "about-ecu/university-profile/",
        "keywords": [
            "about",
            "profile",
            "university",
            "ecu",
            "history",
            "overview",
            "عن الجامعة",
        ],
    },
    "engineering": {
        "title": "Faculty of Engineering and Technology",
        "path": "faculties/engineering-and-technology/",
        "keywords": [
            "engineering",
            "technology",
            "software",
            "mechatronics",
            "construction",
            "energy",
            "هندسة",
        ],
    },
    "computers": {
        "title": "Faculty of Computers and Information Systems",
        "path": "faculties/faculty-of-computers-and-information-systems/",
        "keywords": [
            "computers",
            "computer science",
            "information systems",
            "ai",
            "cybersecurity",
            "data science",
            "حاسبات",
        ],
    },
    "pharmacy": {
        "title": "Faculty of Pharmacy and Drug Technology",
        "path": "faculties/faculty-of-pharmacy-and-drug-technology/",
        "keywords": ["pharmacy", "drug technology", "pharmd", "صيدلة"],
    },
    "physical_therapy": {
        "title": "Faculty of Physical Therapy",
        "path": "faculties/faculty-of-physical-therapy/",
        "keywords": ["physical therapy", "physiotherapy", "therapy", "علاج طبيعي"],
    },
    "veterinary": {
        "title": "Faculty of Veterinary Medicine",
        "path": "faculties/faculty-of-veterinary-medicine/",
        "keywords": ["veterinary", "medicine", "animals", "طب بيطري"],
    },
    "business": {
        "title": "Faculty of Economics and International Trade",
        "path": "faculties/faculty-of-economics-and-international-trade/",
        "keywords": [
            "business",
            "economics",
            "trade",
            "marketing",
            "finance",
            "accounting",
            "اقتصاد",
            "تجارة",
        ],
    },
    "mass_communication": {
        "title": "Faculty of Mass Communication",
        "path": "faculties/faculty-of-mass-communication/",
        "keywords": ["mass communication", "media", "journalism", "imc", "إعلام"],
    },
    "art_design": {
        "title": "Faculty of Art and Design",
        "path": "faculties/faculty-of-art-and-design/",
        "keywords": [
            "art",
            "design",
            "graphic",
            "fashion",
            "cinema",
            "multimedia",
            "فنون",
            "تصميم",
        ],
    },
}


def fetch_ecu_page(path: str) -> str | None:
    """Fetch one ECU page path and return cleaned visible text, or ``None``."""
    try:
        url = _build_ecu_url(path)
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            return None

        text = _extract_visible_text(response.text)
        if len(text) < MIN_TEXT_LENGTH:
            return None
        return text
    except Exception:
        return None


def select_ecu_website_page(query: str) -> dict | None:
    """Return the best known ECU page for a query without fetching it."""
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return None

    best_key = None
    best_page = None
    best_score = 0

    for key, page in ECU_WEBSITE_PAGES.items():
        title = page["title"].casefold()
        keywords = [keyword.casefold() for keyword in page["keywords"]]
        score = _page_match_score(normalized_query, title, keywords)
        if score > best_score:
            best_key = key
            best_page = page
            best_score = score

    if best_page is None or best_key is None or best_score <= 0:
        return None

    return {
        "key": best_key,
        "title": best_page["title"],
        "path": best_page["path"],
        "keywords": list(best_page["keywords"]),
    }


def retrieve_from_website(query: str) -> dict | None:
    """Retrieve one relevant ECU website page for later chatbot context."""
    try:
        selected_page = select_ecu_website_page(query)
        if selected_page is None:
            return None

        content = fetch_ecu_page(selected_page["path"])
        if not content:
            return None

        trimmed_content = _trim_content(content)
        if not trimmed_content:
            return None

        return {
            "source": "ecu_website",
            "title": selected_page["title"],
            "url": _build_ecu_url(selected_page["path"]),
            "path": selected_page["path"],
            "content": trimmed_content,
        }
    except Exception:
        return None


def _build_ecu_url(path: str) -> str:
    clean_path = str(path).strip().lstrip("/")
    return urljoin(BASE_URL, clean_path)


def _extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(NOISY_TAGS):
        tag.decompose()

    text = soup.get_text(separator=" ")
    return " ".join(text.split())


def _page_match_score(query: str, title: str, keywords: list[str]) -> int:
    score = 0
    if query in title:
        score += len(query)
    for word in query.split():
        if word in title:
            score += len(word)
    for keyword in keywords:
        if keyword in query:
            score += len(keyword) * 2
        elif query in keyword:
            score += len(query)
    return score


def _trim_content(content: str) -> str:
    cleaned_content = " ".join(content.split())
    if len(cleaned_content) <= MAX_CONTENT_LENGTH:
        return cleaned_content

    truncated = cleaned_content[:MAX_CONTENT_LENGTH].rstrip()
    sentence_end = max(
        truncated.rfind("."),
        truncated.rfind("!"),
        truncated.rfind("?"),
        truncated.rfind("。"),
        truncated.rfind("؟"),
    )
    if sentence_end >= int(MAX_CONTENT_LENGTH * 0.6):
        return truncated[: sentence_end + 1].strip()
    return truncated.strip()
