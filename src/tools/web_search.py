from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

import httpx


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str


class WebSearch:
    def __init__(
        self,
        *,
        brave_api_key: str | None,
        serper_api_key: str | None,
        tavily_api_key: str | None,
    ) -> None:
        self._brave_api_key = brave_api_key
        self._serper_api_key = serper_api_key
        self._tavily_api_key = tavily_api_key

    async def search(self, *, query: str, limit: int = 5) -> list[SearchResult]:
        query = (query or "").strip()
        if not query:
            return []

        providers = [
            ("brave", self._brave_search),
            ("serper", self._serper_search),
            ("tavily", self._tavily_search),
        ]

        for name, fn in providers:
            try:
                results = await fn(query=query, limit=limit)
            except Exception:
                logger.exception("web_search provider failed: %s", name)
                continue
            if results:
                return results

        return []

    async def _brave_search(self, *, query: str, limit: int) -> list[SearchResult]:
        if not self._brave_api_key:
            return []
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {"X-Subscription-Token": self._brave_api_key}
        params = {"q": query, "count": str(limit)}
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
        web = data.get("web", {}) if isinstance(data, dict) else {}
        results = web.get("results", []) if isinstance(web, dict) else []
        out: list[SearchResult] = []
        for item in results[:limit]:
            if not isinstance(item, dict):
                continue
            out.append(
                SearchResult(
                    title=str(item.get("title", "")),
                    url=str(item.get("url", "")),
                    snippet=str(item.get("description", "")),
                    source="brave",
                )
            )
        return [r for r in out if r.url]

    async def _serper_search(self, *, query: str, limit: int) -> list[SearchResult]:
        if not self._serper_api_key:
            return []
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": self._serper_api_key, "Content-Type": "application/json"}
        payload = {"q": query, "num": limit}
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
        organic = data.get("organic", []) if isinstance(data, dict) else []
        out: list[SearchResult] = []
        for item in organic[:limit]:
            if not isinstance(item, dict):
                continue
            out.append(
                SearchResult(
                    title=str(item.get("title", "")),
                    url=str(item.get("link", "")),
                    snippet=str(item.get("snippet", "")),
                    source="serper",
                )
            )
        return [r for r in out if r.url]

    async def _tavily_search(self, *, query: str, limit: int) -> list[SearchResult]:
        if not self._tavily_api_key:
            return []
        url = "https://api.tavily.com/search"
        payload = {"api_key": self._tavily_api_key, "query": query, "max_results": limit}
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            data: Any = r.json()
        results = data.get("results", []) if isinstance(data, dict) else []
        out: list[SearchResult] = []
        for item in results[:limit]:
            if not isinstance(item, dict):
                continue
            out.append(
                SearchResult(
                    title=str(item.get("title", "")),
                    url=str(item.get("url", "")),
                    snippet=str(item.get("content", "")),
                    source="tavily",
                )
            )
        return [r for r in out if r.url]
