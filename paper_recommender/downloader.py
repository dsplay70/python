"""PDF downloader for recommended papers."""

import re
import urllib.error
import urllib.request
from pathlib import Path

from paper_recommender.api import Paper


def _sanitize_filename(title: str) -> str:
    """Convert a paper title into a safe filename."""
    # Keep alphanumeric, spaces, hyphens
    name = re.sub(r"[^\w\s-]", "", title)
    # Collapse whitespace
    name = re.sub(r"\s+", "_", name.strip())
    # Truncate to reasonable length
    return name[:80] if len(name) > 80 else name


def download_pdf(paper: Paper, output_dir: str) -> Path | None:
    """Download a paper's PDF to the output directory.

    Tries open access URL first, then falls back to arXiv.
    Returns the path to the downloaded file, or None on failure.
    """
    pdf_url = paper.best_pdf_url
    if not pdf_url:
        return None

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    filename = _sanitize_filename(paper.title)
    if paper.year:
        filename = f"{filename}_{paper.year}"
    filepath = out_path / f"{filename}.pdf"

    if filepath.exists():
        return filepath

    req = urllib.request.Request(pdf_url)
    req.add_header("User-Agent", "PaperRecommender/0.1")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            filepath.write_bytes(resp.read())
        return filepath
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        print(f"    Download failed ({pdf_url}): {e}")
        return None


def download_papers(
    papers: list[Paper], output_dir: str = "papers"
) -> list[tuple[Paper, Path]]:
    """Download PDFs for a list of papers.

    Returns list of (paper, filepath) tuples for successful downloads.
    """
    downloaded: list[tuple[Paper, Path]] = []
    total = len(papers)

    for i, paper in enumerate(papers, 1):
        pdf_url = paper.best_pdf_url
        if not pdf_url:
            print(f"  [{i}/{total}] {paper.title} - No PDF available")
            continue

        print(f"  [{i}/{total}] Downloading: {paper.title}")
        path = download_pdf(paper, output_dir)
        if path:
            print(f"    -> {path}")
            downloaded.append((paper, path))
        else:
            print(f"    -> Failed")

    return downloaded
