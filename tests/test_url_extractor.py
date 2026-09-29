import pytest
import requests

from agent import url_extractor


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://example.com/article", True),
        ("http://news.example.org:8080/story?id=1", True),
        ("  https://example.com  ", True),
        ("example.com/article", False),
        ("ftp://example.com/file", False),
        ("This is a claim, not a URL.", False),
    ],
)
def test_is_url_accepts_only_http_and_https_urls(value, expected):
    assert url_extractor.is_url(value) is expected


class FakeResponse:
    def __init__(self, text):
        self.text = text

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

    def fake_get(url, headers, timeout):
        captured.update(url=url, headers=headers, timeout=timeout)
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
    assert "User-Agent" in captured["headers"]


def test_extract_article_returns_structured_failure(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.Timeout("request timed out")

    monkeypatch.setattr(url_extractor.requests, "get", fake_get)

    result = url_extractor.extract_article_from_url("https://example.com/story")

    assert result["success"] is False
    assert result["title"] == "Extraction Failed"
    assert result["content"] == ""
    assert "timed out" in result["error"]
