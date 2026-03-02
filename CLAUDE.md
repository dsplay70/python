# CLAUDE.md

## Project Overview

Paper Recommender — a CLI tool that recommends academic papers using the Semantic Scholar API. Designed for CS researchers who want to discover related papers efficiently.

## Repository Structure

```
.
├── main.py                          # Entry point (runs CLI)
├── paper_recommender/
│   ├── __init__.py
│   ├── api.py                       # Semantic Scholar API client
│   ├── recommender.py               # Core recommendation logic
│   └── cli.py                       # CLI (argparse) interface
├── requirements.txt                 # pip dependencies
├── venv/                            # Python virtual environment (not committed)
└── CLAUDE.md                        # This file
```

## Development Environment

- **Python version**: 3.11
- **Virtual environment**: `venv/` (created via `python -m venv venv`)
- **Package manager**: pip with `requirements.txt`
- **External API**: Semantic Scholar (free, no API key required for basic use)

### Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running

```bash
# Search papers by keyword
python main.py search "transformer attention mechanism"

# Get recommendations based on a paper (title, DOI, arXiv ID, or URL)
python main.py recommend "Attention Is All You Need"
python main.py recommend "arXiv:1706.03762"
python main.py recommend "https://arxiv.org/abs/1706.03762"

# Show references of a paper
python main.py refs "Attention Is All You Need"

# Show papers that cite a paper
python main.py citations "Attention Is All You Need"

# Personalized recommendations from your reading list
python main.py for-me my_papers.txt
python main.py for-me my_papers.txt --plan research_plan.txt
python main.py for-me my_papers.txt --plan research_plan.txt -n 30

# Limit results
python main.py search "LLM alignment" -n 5
```

## Dependencies

Defined in `requirements.txt` (unpinned):
- `numpy`
- `pandas`
- `matplotlib`

The paper recommender itself uses only the Python standard library (`urllib`, `json`, `argparse`, `dataclasses`).

## Architecture

- **`api.py`**: Low-level HTTP client for Semantic Scholar. Handles rate limiting (1 req/sec), identifier normalization (DOI, arXiv, URL), and response parsing into `Paper` dataclasses.
- **`recommender.py`**: High-level operations — keyword search, paper-based recommendations, references, and citations. Resolves user input to a paper before querying.
- **`cli.py`**: Thin CLI layer using argparse subcommands. Each subcommand maps to a `PaperRecommender` method.

## Key Conventions

- Standard library only for core functionality — no external HTTP libraries needed.
- `Paper` dataclass in `api.py` is the shared data model.
- User input is normalized in `api.py._normalize_identifier()` to support DOI, arXiv, and URL inputs.
- No `.gitignore` is present — avoid committing `venv/`, `__pycache__/`, or `.pyc` files.

## Git

- **Primary branch**: `main`
- No CI/CD pipelines configured.
- No pre-commit hooks.
- No test framework configured yet.
