"""Semantic Scholar API client."""

import time
import urllib.error
import urllib.parse
import urllib.request
import json
from dataclasses import dataclass


BASE_URL = "https://api.semanticscholar.org/graph/v1"
RECOMMEND_URL = "https://api.semanticscholar.org/recommendations/v1/papers/forpaper"

PAPER_FIELDS = "paperId,title,authors,year,abstract,citationCount,url,externalIds"

# Rate limit: 1 request per second for unauthenticated access
REQUEST_INTERVAL = 1.0


@dataclass
class Paper:
    paper_id: str
    title: str
    authors: list[str]
    year: int | None
    abstract: str | None
    citation_count: int
    url: str
    arxiv_id: str | None = None

    def summary(self, index: int | None = None) -> str:
        prefix = f"[{index}] " if index is not None else ""
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += " et al."
        year_str = f" ({self.year})" if self.year else ""
        cite_str = f"  Citations: {self.citation_count}"
        lines = [
            f"{prefix}{self.title}{year_str}",
            f"  Authors: {authors_str}",
            cite_str,
            f"  URL: {self.url}",
        ]
        if self.abstract:
            short = self.abstract[:200]
            if len(self.abstract) > 200:
                short += "..."
            lines.append(f"  Abstract: {short}")
        return "\n".join(lines)


def _parse_paper(data: dict) -> Paper | None:
    """Parse API response into a Paper object."""
    if not data or not data.get("title"):
        return None
    authors = [a.get("name", "") for a in (data.get("authors") or [])]
    external_ids = data.get("externalIds") or {}
    arxiv_id = external_ids.get("ArXiv")
    return Paper(
        paper_id=data.get("paperId", ""),
        title=data.get("title", ""),
        authors=authors,
        year=data.get("year"),
        abstract=data.get("abstract"),
        citation_count=data.get("citationCount", 0),
        url=data.get("url", ""),
        arxiv_id=arxiv_id,
    )


class SemanticScholarClient:
    """Minimal client for the Semantic Scholar API."""

    def __init__(self):
        self._last_request_time = 0.0

    def _rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < REQUEST_INTERVAL:
            time.sleep(REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    def _get(self, url: str) -> dict | list | None:
        self._rate_limit()
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "PaperRecommender/0.1")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429:
                print("Rate limited. Waiting 5 seconds...")
                time.sleep(5)
                return self._get(url)
            raise
        except urllib.error.URLError as e:
            print(f"Network error: {e.reason}")
            return None

    def search(self, query: str, limit: int = 10) -> list[Paper]:
        """Search papers by keyword/query string."""
        encoded = urllib.parse.quote(query)
        url = f"{BASE_URL}/paper/search?query={encoded}&limit={limit}&fields={PAPER_FIELDS}"
        data = self._get(url)
        if not data or "data" not in data:
            return []
        papers = []
        for item in data["data"]:
            p = _parse_paper(item)
            if p:
                papers.append(p)
        return papers

    def get_paper(self, paper_id: str) -> Paper | None:
        """Get a paper by Semantic Scholar ID, DOI, arXiv ID, or URL.

        Accepts:
          - Semantic Scholar paper ID
          - DOI (e.g. "10.18653/v1/N18-3011")
          - arXiv ID (e.g. "arXiv:1706.03762")
          - Full URL (DOI or arXiv URLs are auto-detected)
        """
        identifier = self._normalize_identifier(paper_id)
        url = f"{BASE_URL}/paper/{identifier}?fields={PAPER_FIELDS}"
        data = self._get(url)
        if not data:
            return None
        return _parse_paper(data)

    def get_recommendations(self, paper_id: str, limit: int = 10) -> list[Paper]:
        """Get recommended papers based on a given paper."""
        url = f"{RECOMMEND_URL}/{paper_id}?limit={limit}&fields={PAPER_FIELDS}"
        data = self._get(url)
        if not data or "recommendedPapers" not in data:
            return []
        papers = []
        for item in data["recommendedPapers"]:
            p = _parse_paper(item)
            if p:
                papers.append(p)
        return papers

    def get_references(self, paper_id: str, limit: int = 10) -> list[Paper]:
        """Get papers referenced by the given paper."""
        url = f"{BASE_URL}/paper/{paper_id}/references?limit={limit}&fields={PAPER_FIELDS}"
        data = self._get(url)
        if not data or "data" not in data:
            return []
        papers = []
        for item in data["data"]:
            cited = item.get("citedPaper")
            if cited:
                p = _parse_paper(cited)
                if p:
                    papers.append(p)
        return papers

    def get_citations(self, paper_id: str, limit: int = 10) -> list[Paper]:
        """Get papers that cite the given paper."""
        url = f"{BASE_URL}/paper/{paper_id}/citations?limit={limit}&fields={PAPER_FIELDS}"
        data = self._get(url)
        if not data or "data" not in data:
            return []
        papers = []
        for item in data["data"]:
            citing = item.get("citingPaper")
            if citing:
                p = _parse_paper(citing)
                if p:
                    papers.append(p)
        return papers

    @staticmethod
    def _normalize_identifier(raw: str) -> str:
        """Convert a user-supplied string into a Semantic Scholar paper identifier."""
        raw = raw.strip()

        # arXiv URL
        if "arxiv.org" in raw:
            # e.g. https://arxiv.org/abs/1706.03762 or /pdf/1706.03762
            parts = raw.rstrip("/").split("/")
            arxiv_id = parts[-1]
            # Remove version suffix like v1
            if arxiv_id and arxiv_id[-1].isdigit() and "v" in arxiv_id:
                base, _, ver = arxiv_id.rpartition("v")
                if ver.isdigit():
                    arxiv_id = base
            return f"ArXiv:{arxiv_id}"

        # DOI URL
        if "doi.org/" in raw:
            doi = raw.split("doi.org/", 1)[1]
            return f"DOI:{doi}"

        # Semantic Scholar URL
        if "semanticscholar.org" in raw:
            # e.g. https://www.semanticscholar.org/paper/.../abc123
            parts = raw.rstrip("/").split("/")
            return parts[-1]

        # Bare arXiv ID (e.g. 1706.03762 or arXiv:1706.03762)
        if raw.lower().startswith("arxiv:"):
            return f"ArXiv:{raw[6:]}"

        # Bare DOI
        if raw.startswith("10."):
            return f"DOI:{raw}"

        # Otherwise assume Semantic Scholar paper ID
        return urllib.parse.quote(raw, safe=":")
