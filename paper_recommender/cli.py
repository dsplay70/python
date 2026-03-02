"""CLI interface for the paper recommender."""

import argparse
import sys

from paper_recommender.recommender import PaperRecommender


def _print_papers(papers, label="Results"):
    if not papers:
        print(f"\n{label}: No papers found.")
        return
    print(f"\n{label} ({len(papers)} papers):")
    print("-" * 60)
    for i, paper in enumerate(papers, 1):
        print(paper.summary(index=i))
        print()


def cmd_search(args):
    """Handle the 'search' subcommand."""
    recommender = PaperRecommender()
    query = " ".join(args.query)
    print(f'Searching for: "{query}"')
    papers = recommender.search_by_keyword(query, limit=args.limit)
    _print_papers(papers, label="Search results")


def cmd_recommend(args):
    """Handle the 'recommend' subcommand."""
    recommender = PaperRecommender()
    paper_input = " ".join(args.paper)
    print(f'Finding recommendations for: "{paper_input}"')
    source, papers = recommender.recommend_from_paper(paper_input, limit=args.limit)
    if source is None:
        print("Error: Could not find the specified paper.")
        sys.exit(1)
    print(f"\nSource paper: {source.title} ({source.year})")
    _print_papers(papers, label="Recommended papers")


def cmd_references(args):
    """Handle the 'refs' subcommand."""
    recommender = PaperRecommender()
    paper_input = " ".join(args.paper)
    print(f'Finding references for: "{paper_input}"')
    source, papers = recommender.get_references(paper_input, limit=args.limit)
    if source is None:
        print("Error: Could not find the specified paper.")
        sys.exit(1)
    print(f"\nSource paper: {source.title} ({source.year})")
    _print_papers(papers, label="References")


def cmd_citations(args):
    """Handle the 'citations' subcommand."""
    recommender = PaperRecommender()
    paper_input = " ".join(args.paper)
    print(f'Finding citations for: "{paper_input}"')
    source, papers = recommender.get_citations(paper_input, limit=args.limit)
    if source is None:
        print("Error: Could not find the specified paper.")
        sys.exit(1)
    print(f"\nSource paper: {source.title} ({source.year})")
    _print_papers(papers, label="Citing papers")


def main():
    parser = argparse.ArgumentParser(
        description="Paper Recommender - Find and discover academic papers",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # search
    sp_search = subparsers.add_parser("search", help="Search papers by keyword")
    sp_search.add_argument("query", nargs="+", help="Search keywords")
    sp_search.add_argument("-n", "--limit", type=int, default=10, help="Max results (default: 10)")
    sp_search.set_defaults(func=cmd_search)

    # recommend
    sp_rec = subparsers.add_parser("recommend", help="Get recommendations from a paper")
    sp_rec.add_argument("paper", nargs="+", help="Paper title, DOI, arXiv ID, or URL")
    sp_rec.add_argument("-n", "--limit", type=int, default=10, help="Max results (default: 10)")
    sp_rec.set_defaults(func=cmd_recommend)

    # refs
    sp_refs = subparsers.add_parser("refs", help="Show references of a paper")
    sp_refs.add_argument("paper", nargs="+", help="Paper title, DOI, arXiv ID, or URL")
    sp_refs.add_argument("-n", "--limit", type=int, default=10, help="Max results (default: 10)")
    sp_refs.set_defaults(func=cmd_references)

    # citations
    sp_cites = subparsers.add_parser("citations", help="Show papers that cite a paper")
    sp_cites.add_argument("paper", nargs="+", help="Paper title, DOI, arXiv ID, or URL")
    sp_cites.add_argument("-n", "--limit", type=int, default=10, help="Max results (default: 10)")
    sp_cites.set_defaults(func=cmd_citations)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
