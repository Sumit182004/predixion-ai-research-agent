

import pytest
import httpx
from app.tools import is_public_web_url


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "http://example.com",
        "https://localhost",
        "https://127.0.0.1",
        "https://user:password@example.com",
    ],
)
def test_url_validation(url):
    assert is_public_web_url(url) is (
        url == "https://example.com"
    )


@pytest.mark.asyncio
async def test_web_search_handles_missing_api_key(monkeypatch):
    from app import tools

    monkeypatch.setattr(tools, "TAVILY_API_KEY", None)

    result = await tools.web_search("Test research question")

    assert result["success"] is False
    assert result["results"] == []
    assert "not configured" in result["error"]


@pytest.mark.asyncio
async def test_fetch_webpage_rejects_invalid_url(monkeypatch):
    from app import tools

    monkeypatch.setattr(
        tools,
        "is_public_web_url",
        lambda url: False,
    )

    result = await tools.fetch_webpage("http://localhost")

    assert result["success"] is False
    assert "invalid" in result["error"].lower()


@pytest.mark.asyncio
async def test_fetch_webpage_handles_timeout(monkeypatch):
    from app import tools

    attempts = {"count": 0}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, *args, **kwargs):
            attempts["count"] += 1
            raise httpx.TimeoutException("Simulated timeout")

    monkeypatch.setattr(
        tools,
        "is_public_web_url",
        lambda url: True,
    )

    monkeypatch.setattr(
        tools.httpx,
        "AsyncClient",
        lambda **kwargs: FakeClient(),
    )

    async def fake_sleep(seconds):
        return None

    monkeypatch.setattr(tools.asyncio, "sleep", fake_sleep)

    result = await tools.fetch_webpage("https://example.com")

    assert result["success"] is False
    assert "timed out" in result["error"].lower()
    assert attempts["count"] == 2
