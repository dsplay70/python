"""Core recommendation logic."""

from paper_recommender.api import Paper, SemanticScholarClient


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

    def _resolve_paper(self, paper_input: str) -> Paper | None:
        source = self.client.get_paper(paper_input)
        if source is None:
            results = self.client.search(paper_input, limit=1)
            if results:
                source = results[0]
        return source
