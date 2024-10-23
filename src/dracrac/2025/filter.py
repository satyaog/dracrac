# for author in ...
# do
#   python3 filter.py paperoni-2024-10-09.json --author "${author}" >paperoni-2024-10-09_"${author// /_}".json
# done
import argparse
from datetime import datetime, timedelta
import json
import logging
import re
from pathlib import Path
import unicodedata

logging.basicConfig(level=logging.DEBUG)


def str_normalize(string):
    string = unicodedata.normalize("NFKC", string).lower()
    string = re.sub(pattern=r"[^ a-z]", string=string, repl="")
    return string


def filter_on_releases(papers: list, check: callable):
    for p in papers:
        for v in p["releases"][:]:
            if not check(v):
                p["releases"].remove(v)

        if not p["releases"]:
            continue

        yield p


def filter_authors(papers: list, author: str):
    author = str_normalize(author)
    for p in papers:
        authors = [str_normalize(a["author"]["name"]) for a in p["authors"]]

        if author not in authors:
            continue

        yield p


def filter_peer_reviewed(papers: list):
    check = lambda v: v["peer_reviewed"] and v["status"] != "rejected"
    yield from filter_on_releases(papers, check=check)


def filter_date(papers: list, start: datetime, end: datetime):
    def check(v:dict):
        date = datetime.fromtimestamp(v["venue"]["date"]["timestamp"])
        return date >= start and date < end
    yield from filter_on_releases(papers, check=check)


def filter_venue(papers: list, venue: str):
    venue = str_normalize(venue)
    def check(v:dict):
        name = str_normalize(v["venue"]["name"])
        return re.match(f".*{venue}.*", name)
    yield from filter_on_releases(papers, check=check)


def format_html(papers: list):
    print("<ul>")
    for authors, title, venue, date, url in papers:
        print("<li>", end="")
        print(
            ". ".join(
                (
                    authors,
                    title,
                    venue,
                    date,
                    *([f"Available: <a href='{url}'>{url}</a>"] if url else []),
                )
            ),
            end="",
        )
        print("</li>")
    print("</ul>")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paperoni",
        metavar="JSON",
        type=Path,
        help="Paperoni json output of papers to filter",
    )
    parser.add_argument(
        "--author",
        metavar="STR",
        default=None,
        help="Author name",
    )
    parser.add_argument(
        "--start",
        metavar="YYYY-MM-DD",
        type=lambda value: datetime.strptime(value, "%Y-%m-%d"),
        default=datetime(1970, 1, 1),
    )
    parser.add_argument(
        "--end",
        metavar="YYYY-MM-DD",
        type=lambda value: datetime.strptime(value, "%Y-%m-%d"),
        default=(datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
    )
    parser.add_argument(
        "--venue",
        metavar="STR",
        default=None,
    )
    options = parser.parse_args()

    logging.info(f"Filtering papers for author {options.author}")

    papers = filter_peer_reviewed(json.loads(options.paperoni.read_text()))

    if options.author:
        papers = filter_authors(papers, options.author)

    if options.start or options.end:
        papers = filter_date(papers, options.start, options.end)

    if options.venue:
        papers = filter_venue(papers, options.venue)

    papers = list(papers)
    print(json.dumps(papers))

    logging.info(f"Filtered {len(papers)} papers")
