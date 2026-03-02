"""Preprocessor module for NotebookLM MCP integration.

Defines the schema for preprocessed research data and provides utilities
to load it from JSON. When used with Claude Code + NotebookLM MCP server,
Claude queries the user's notebooks to extract structured research context,
saves it as JSON, and the CLI consumes it for better recommendations.

JSON schema (preprocessed.json):
{
    "keywords": ["multi-agent systems", "RLHF", ...],
    "themes": ["AI alignment", "LLM safety", ...],
    "research_gaps": ["scalable oversight for LLMs", ...],
    "paper_ids": ["arXiv:1706.03762", "10.18653/v1/N18-3011", ...]
}
"""

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ResearchProfile:
    """Structured research context extracted by LLM preprocessing."""

    keywords: list[str] = field(default_factory=list)
    themes: list[str] = field(default_factory=list)
    research_gaps: list[str] = field(default_factory=list)
    paper_ids: list[str] = field(default_factory=list)

    @property
    def search_queries(self) -> list[str]:
        """Generate search queries ordered by specificity.

        Research gaps are the most specific (best for finding novel work),
        followed by keywords, then broader themes.
        """
        queries: list[str] = []
        seen: set[str] = set()
        for q in self.research_gaps + self.keywords + self.themes:
            normalized = q.strip().lower()
            if normalized and normalized not in seen:
                queries.append(q.strip())
                seen.add(normalized)
        return queries


def load_profile(path: str) -> ResearchProfile:
    """Load a ResearchProfile from a JSON file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ResearchProfile(
        keywords=data.get("keywords", []),
        themes=data.get("themes", []),
        research_gaps=data.get("research_gaps", []),
        paper_ids=data.get("paper_ids", []),
    )


# Prompt template for Claude to use when querying NotebookLM MCP.
# Claude Code can use this to generate the right query.
NOTEBOOKLM_PROMPT = """\
Based on the research papers and documents in this notebook, extract:

1. **keywords**: Specific technical terms and method names (e.g., "RLHF", \
"transformer", "chain-of-thought prompting")
2. **themes**: Broader research areas and topics (e.g., "AI alignment", \
"natural language processing")
3. **research_gaps**: Open problems or underexplored directions mentioned \
or implied by the papers
4. **paper_ids**: Any DOIs or arXiv IDs found in the documents

Return ONLY valid JSON in this exact format:
{
    "keywords": ["keyword1", "keyword2", ...],
    "themes": ["theme1", "theme2", ...],
    "research_gaps": ["gap1", "gap2", ...],
    "paper_ids": ["arXiv:XXXX.XXXXX", "10.XXXX/XXXXX", ...]
}
"""
