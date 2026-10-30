
import asyncio
import ipaddress
import os
import socket
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TIMEOUT = httpx.Timeout(15.0, connect=5.0)



async def web_search(query: str, max_results: int = 5) -> dict:
    if not TAVILY_API_KEY:
        return {
            "success": False,
            "error": "TAVILY_API_KEY is not configured.",
            "results": [],
        }

    max_results = max(1, min(max_results, 5))
    last_error = "Unknown search error."

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(
                timeout=TIMEOUT,
                trust_env=False,
            ) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": TAVILY_API_KEY,
                        "query": query,
                        "max_results": max_results,
                        "search_depth": "basic",
                    },
                )

                # Retry only temporary server errors.
                if response.status_code >= 500 and attempt == 0:
                    await asyncio.sleep(0.5)
                    continue

                response.raise_for_status()
                data = response.json()

            if not isinstance(data, dict):
                raise ValueError("Search API returned an invalid response.")

            raw_results = data.get("results", [])
            if not isinstance(raw_results, list):
                raise ValueError("Search API returned an invalid results list.")

            results = []

            for item in raw_results:
                if not isinstance(item, dict):
                    continue

                title = item.get("title")
                url = item.get("url")
                snippet = item.get("content")

                if not all(
                    isinstance(value, str) and value.strip()
                    for value in (title, url, snippet)
                ):
                    continue

                if not is_public_web_url(url):
                    continue

                results.append({
                    "title": title.strip()[:300],
                    "url": url,
                    "snippet": snippet.strip()[:2000],
                })

            return {
                "success": True,
                "results": results,
                "count": len(results),
            }

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            last_error = f"Search API returned HTTP {status}."

            # Retry server errors and rate limits once.
            if attempt == 0 and (status == 429 or status >= 500):
                await asyncio.sleep(0.5)
                continue

            break

        except httpx.TimeoutException:
            last_error = "Search API request timed out."

        except httpx.RequestError as exc:
            last_error = f"Search API connection failed: {type(exc).__name__}."

        except ValueError as exc:
            last_error = str(exc)
            break

        if attempt == 0:
            await asyncio.sleep(0.5)

    return {
        "success": False,
        "error": last_error,
        "results": [],
    }


def is_public_web_url(url: str) -> bool:
    """Allow public HTTPS URLs; reject private and local destinations."""

    try:
        parsed = urlparse(url)

        if parsed.scheme != "https" or not parsed.hostname:
            return False

        if parsed.username or parsed.password:
            return False

        hostname = parsed.hostname

        if hostname.lower() == "localhost":
            return False

        try:
            addresses = [ipaddress.ip_address(hostname)]
        except ValueError:
            addresses = [
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(
                    hostname, None, type=socket.SOCK_STREAM
                )
            ]

        return bool(addresses) and all(
            address.is_global for address in addresses
        )

    except (ValueError, OSError):
        return False



async def fetch_webpage(url: str) -> dict:
    """Fetch a public HTTPS HTML page with bounded retries."""

    if not is_public_web_url(url):
        return {
            "success": False,
            "error": "URL is invalid or not a public HTTPS destination.",
        }

    last_error = "Page retrieval failed."

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(
                timeout=TIMEOUT,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "ResearchAgent/1.0",
                        "Accept": "text/html",
                    },
                )

            # Redirects remain disabled to avoid following an unchecked
            # redirect to a private or local destination.
            if response.is_redirect:
                return {
                    "success": False,
                    "error": "Page returned a redirect; redirects are not followed for security.",
                }

            if response.status_code == 429 or response.status_code >= 500:
                last_error = f"Page server returned HTTP {response.status_code}."
                if attempt == 0:
                    await asyncio.sleep(0.5)
                    continue
                break

            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type:
                return {
                    "success": False,
                    "error": "The URL did not return an HTML page.",
                }

            # Avoid parsing an unexpectedly large response.
            max_bytes = 2_000_000
            if len(response.content) > max_bytes:
                return {
                    "success": False,
                    "error": "Page response exceeded the 2 MB size limit.",
                }

            soup = BeautifulSoup(response.text, "html.parser")

            for element in soup(
                ["script", "style", "nav", "footer", "header", "noscript"]
            ):
                element.decompose()

            title = soup.title.get_text(" ", strip=True) if soup.title else ""
            text = soup.get_text(" ", strip=True)

            if not text.strip():
                return {
                    "success": False,
                    "error": "The HTML page contained no readable text.",
                }

            return {
                "success": True,
                "url": url,
                "title": title[:300],
                "text": text[:12000],
            }

        except httpx.TimeoutException:
            last_error = "Page retrieval timed out."

        except httpx.HTTPStatusError as exc:
            last_error = f"Page server returned HTTP {exc.response.status_code}."
            if not (
                attempt == 0
                and (exc.response.status_code == 429
                     or exc.response.status_code >= 500)
            ):
                break

        except httpx.RequestError as exc:
            last_error = f"Page connection failed: {type(exc).__name__}."

        except (ValueError, UnicodeError):
            last_error = "Page content could not be decoded."

        if attempt == 0:
            await asyncio.sleep(0.5)

    return {
        "success": False,
        "error": last_error,
    }




def evaluate_source_quality(
    question: str,
    evidence: list[dict],
) -> dict:
    """
    Deterministic evidence-quality evaluation.
    This measures evidence availability and relevance,
    not factual correctness.
    """

    warnings = []

    if not isinstance(evidence, list) or not evidence:
        return {
            "success": True,
            "score": 0.0,
            "quality": "poor",
            "source_count": 0,
            "duplicate_count": 0,
            "snippet_only_count": 0,
            "warnings": ["No usable evidence was available."],
        }

    question_words = {
        word.lower().strip(".,?!:;()[]{}\"'")
        for word in question.split()
        if len(word) > 2
    }

    unique_evidence = {}
    duplicate_count = 0
    snippet_only_count = 0
    malformed_count = 0
    scores = []

    for item in evidence:
        if not isinstance(item, dict):
            malformed_count += 1
            continue

        url = item.get("url")
        title = item.get("title")
        content = item.get("text")
        evidence_type = item.get("evidence_type")

        if not (
            isinstance(url, str)
            and isinstance(title, str)
            and isinstance(content, str)
            and content.strip()
            and is_public_web_url(url)
        ):
            malformed_count += 1
            continue

        normalized_url = url.strip().lower().rstrip("/")

        if normalized_url in unique_evidence:
            duplicate_count += 1
            continue

        unique_evidence[normalized_url] = item

        if evidence_type != "webpage":
            snippet_only_count += 1

        searchable_text = f"{title} {content}".lower()

        matched_words = sum(
            1 for word in question_words
            if word in searchable_text
        )

        relevance = (
            matched_words / len(question_words)
            if question_words else 0.0
        )

        content_score = min(len(content.strip()) / 1500, 1.0)

        item_score = (
            0.7 * relevance
            + 0.3 * content_score
        )

        if evidence_type != "webpage":
            item_score *= 0.6

        scores.append(item_score)

    unique_count = len(unique_evidence)

    if malformed_count:
        warnings.append(
            f"{malformed_count} malformed or invalid evidence item(s) were ignored."
        )

    if duplicate_count:
        warnings.append(
            f"Detected {duplicate_count} duplicate source URL(s)."
        )

    if snippet_only_count:
        warnings.append(
            f"{snippet_only_count} source(s) rely on search snippets."
        )

    if unique_count < 2:
        warnings.append(
            "Fewer than two unique sources are available."
        )

    if not scores:
        return {
            "success": True,
            "score": 0.0,
            "quality": "poor",
            "source_count": 0,
            "duplicate_count": duplicate_count,
            "snippet_only_count": 0,
            "warnings": warnings or ["No usable evidence was available."],
        }

    final_score = sum(scores) / len(scores)

    if unique_count < 2:
        final_score *= 0.7

    if snippet_only_count:
        final_score *= 1 - (
            0.2 * snippet_only_count / unique_count
        )

    final_score = round(max(0.0, min(1.0, final_score)), 2)

    if (
        final_score >= 0.65
        and unique_count >= 2
        and snippet_only_count == 0
    ):
        quality = "good"
    elif final_score >= 0.35:
        quality = "moderate"
    else:
        quality = "poor"

    return {
        "success": True,
        "score": final_score,
        "quality": quality,
        "source_count": unique_count,
        "duplicate_count": duplicate_count,
        "snippet_only_count": snippet_only_count,
        "warnings": warnings,
    }

