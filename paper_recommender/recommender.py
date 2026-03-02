"""Core recommendation logic."""

import re
from collections import Counter
from pathlib import Path

from paper_recommender.api import Paper, SemanticScholarClient


def _extract_keywords_from_text(text: str) -> list[str]:
    """Extract meaningful keyword phrases from research plan text.

    Splits text into candidate terms by punctuation/newlines, then filters
    to keep only short phrases that look like research topics.
    """
    # Split by common delimiters: commas, semicolons, newlines, bullets
    chunks = re.split(r"[,;\n\r\u2022\u30fb]+", text)
    keywords = []
    for chunk in chunks:
        chunk = chunk.strip().strip("-").strip("・").strip("•").strip()
        # Skip very short or very long fragments
        if len(chunk) < 3 or len(chunk) > 120:
            continue
        # Skip fragments that are clearly full sentences (rough heuristic)
        word_count = len(chunk.split())
        if word_count > 10:
            continue
        keywords.append(chunk)
    return keywords


class PaperRecommender:
    """Recommend papers via keyword search or from an existing paper."""

    def __init__(self):
        self.client = SemanticScholarClient()

    def search_by_keyword(self, query: str, limit: int = 10) -> list[Paper]:
        """Search papers by keyword or topic."""
        return self.client.search(query, limit=limit)

    def recommend_from_paper(
        self, paper_input: str, limit: int = 10
    ) -> tuple[Paper | None, list[Paper]]:
        """Find a paper and return recommendations for it.

        Args:
            paper_input: A paper title, DOI, arXiv ID, or URL.
            limit: Maximum number of recommendations.

        Returns:
            Tuple of (source_paper, recommended_papers).
            source_paper is None if the paper could not be found.
        """
        # First try to resolve as an identifier (DOI, arXiv, URL)
        source = self.client.get_paper(paper_input)

        # If direct lookup fails, try searching by title
        if source is None:
            results = self.client.search(paper_input, limit=1)
            if results:
                source = results[0]

        if source is None:
            return None, []

        recommendations = self.client.get_recommendations(
            source.paper_id, limit=limit
        )
        return source, recommendations

    def get_references(
        self, paper_input: str, limit: int = 10
    ) -> tuple[Paper | None, list[Paper]]:
        """Get the reference list of a paper.

        Useful for tracing foundational works that a paper builds on.
        """
        source = self._resolve_paper(paper_input)
        if source is None:
            return None, []
        refs = self.client.get_references(source.paper_id, limit=limit)
        return source, refs

    def get_citations(
        self, paper_input: str, limit: int = 10
    ) -> tuple[Paper | None, list[Paper]]:
        """Get papers that cite the given paper.

        Useful for finding newer work that builds on a paper.
        """
        source = self._resolve_paper(paper_input)
        if source is None:
            return None, []
        cites = self.client.get_citations(source.paper_id, limit=limit)
        return source, cites

    def recommend_from_profile(
        self,
        paper_list_path: str,
        plan_path: str | None = None,
        limit: int = 20,
    ) -> tuple[list[Paper], list[Paper], list[str]]:
        """Recommend papers based on a reading list and optional research plan.

        Args:
            paper_list_path: Path to a text file with one paper per line
                             (title, DOI, arXiv ID, or URL).
            plan_path: Optional path to a research plan text file.
            limit: Maximum number of recommendations to return.

        Returns:
            Tuple of (resolved_source_papers, recommended_papers, keywords_used).
        """
        # 1. Read and resolve the paper list
        lines = Path(paper_list_path).read_text(encoding="utf-8").splitlines()
        paper_inputs = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]

        resolved: list[Paper] = []
        for entry in paper_inputs:
            print(f"  Resolving: {entry}")
            paper = self._resolve_paper(entry)
            if paper:
                resolved.append(paper)
                print(f"    -> {paper.title} ({paper.year})")
            else:
                print(f"    -> Not found, skipping")

        if not resolved:
            return [], [], []

        # 2. Gather recommendations from each source paper
        rec_counts: Counter[str] = Counter()  # paper_id -> times recommended
        rec_map: dict[str, Paper] = {}
        source_ids = {p.paper_id for p in resolved}

        for paper in resolved:
            print(f"  Getting recommendations from: {paper.title}")
            recs = self.client.get_recommendations(paper.paper_id, limit=limit)
            for r in recs:
                if r.paper_id not in source_ids:
                    rec_counts[r.paper_id] += 1
                    rec_map[r.paper_id] = r

        # 3. If a research plan is provided, extract keywords and boost via search
        keywords_used: list[str] = []
        if plan_path:
            plan_text = Path(plan_path).read_text(encoding="utf-8")
            keywords_used = _extract_keywords_from_text(plan_text)
            print(f"  Extracted {len(keywords_used)} keywords from research plan")
            for kw in keywords_used[:5]:  # search top 5 keywords
                print(f"  Searching keyword: {kw}")
                results = self.client.search(kw, limit=5)
                for r in results:
                    if r.paper_id not in source_ids:
                        rec_counts[r.paper_id] += 1
                        rec_map[r.paper_id] = r

        # 4. Rank: papers recommended by more sources rank higher,
        #    break ties by citation count
        ranked_ids = sorted(
            rec_counts.keys(),
            key=lambda pid: (rec_counts[pid], rec_map[pid].citation_count),
            reverse=True,
        )

        recommended = [rec_map[pid] for pid in ranked_ids[:limit]]
        return resolved, recommended, keywords_used

    def _resolve_paper(self, paper_input: str) -> Paper | None:
        source = self.client.get_paper(paper_input)
        if source is None:
            results = self.client.search(paper_input, limit=1)
            if results:
                source = results[0]
        return source
