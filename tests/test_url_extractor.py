import pytest
import requests

from agent import url_extractor


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://example.com/article", True),
        ("http://news.example.org:8080/story?id=1", True),
        ("  https://example.com  ", True),
        ("http://127.0.0.1/internal", True),
        ("example.com/article", False),
        ("ftp://example.com/file", False),
        ("This is a claim, not a URL.", False),
    ],
)
def test_is_url_accepts_only_http_and_https_urls(value, expected):
    assert url_extractor.is_url(value) is expected


class FakeResponse:
    def __init__(self, text="", status_code=200, headers=None):
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}

    def raise_for_status(self):
        return None


def test_extract_article_prefers_open_graph_title_and_article_text(monkeypatch):
    html = """
    <html>
      <head>
        <title>Fallback title</title>
        <meta property="og:title" content="Verified article title">
      </head>
      <body>
        <nav>This navigation text must not be included in the article.</nav>
        <article>
          <p>This paragraph is intentionally long enough to be extracted as article content.</p>
          <p>A second substantial paragraph provides more evidence for the extraction test.</p>
        </article>
      </body>
    </html>
    """
    captured = {}

    monkeypatch.setattr(
        url_extractor.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (url_extractor.socket.AF_INET, url_extractor.socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ],
    )

    def fake_get(url, headers, timeout, allow_redirects):
        captured.update(
            url=url,
            headers=headers,
            timeout=timeout,
            allow_redirects=allow_redirects,
        )
        return FakeResponse(html)

    monkeypatch.setattr(url_extractor.requests, "get", fake_get)

    result = url_extractor.extract_article_from_url(" https://example.com/story ")

    assert result["success"] is True
    assert result["title"] == "Verified article title"
    assert "intentionally long enough" in result["content"]
    assert "second substantial paragraph" in result["content"]
    assert "navigation text" not in result["content"]
    assert captured["url"] == "https://example.com/story"
    assert captured["timeout"] == 12
    assert captured["allow_redirects"] is False
    assert "User-Agent" in captured["headers"]


def test_extract_article_returns_structured_failure(monkeypatch):
    monkeypatch.setattr(
        url_extractor.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (url_extractor.socket.AF_INET, url_extractor.socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ],
    )

    def fake_get(*args, **kwargs):
        raise requests.Timeout("request timed out")

    monkeypatch.setattr(url_extractor.requests, "get", fake_get)

    result = url_extractor.extract_article_from_url("https://example.com/story")

    assert result["success"] is False
    assert result["title"] == "Extraction Failed"
    assert result["content"] == ""
    assert "timed out" in result["error"]


def test_extract_article_blocks_private_network_addresses(monkeypatch):
    def unexpected_request(*args, **kwargs):
        pytest.fail("A blocked private URL must not trigger an HTTP request.")

    monkeypatch.setattr(url_extractor.requests, "get", unexpected_request)

    result = url_extractor.extract_article_from_url("http://127.0.0.1/internal")

    assert result["success"] is False
    assert "non-public network address" in result["error"]


def test_extract_article_validates_redirect_destinations(monkeypatch):
    monkeypatch.setattr(
        url_extractor.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (url_extractor.socket.AF_INET, url_extractor.socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ],
    )
    request_count = 0

    def fake_get(*args, **kwargs):
        nonlocal request_count
        request_count += 1
        return FakeResponse(
            status_code=302,
            headers={"Location": "http://169.254.169.254/latest/meta-data"},
        )

    monkeypatch.setattr(url_extractor.requests, "get", fake_get)

    result = url_extractor.extract_article_from_url("https://example.com/redirect")

    assert result["success"] is False
    assert "non-public network address" in result["error"]
    assert request_count == 1
