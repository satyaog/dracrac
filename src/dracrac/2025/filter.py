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
import sys
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


def filter_authors(papers: list, authors: list):
    authors = {str_normalize(author) for author in authors}
    for p in papers:
        p_authors = {str_normalize(a["author"]["name"]) for a in p["authors"]}

        _check = authors & p_authors

        if not _check:
            logging.debug(f"Based on {sorted(authors)} not intersecting with {sorted(p_authors)}, filtered out {p['title']}")

        if _check:
            continue

        yield p


def filter_peer_reviewed(papers: list):
    def check(v:dict):
        _check = v["peer_reviewed"] and v["status"] not in ["rejected", "withdrawn"]

        if not _check:
            logging.debug(f"Based on peer reviewed:{v['peer_reviewed']} and status:{v['status']}, filtered out {v['venue']['name']}")

        return _check

    yield from filter_on_releases(papers, check=check)


def filter_date(papers: list, start: datetime, end: datetime):
    def check(v:dict):
        date = datetime.fromtimestamp(v["venue"]["date"]["timestamp"])

        _check = date >= start and date < end

        if not _check:
            logging.debug(f"Based on {start} <= {date} < {end}, filtered out {v['venue']['name']}")

        return _check

    yield from filter_on_releases(papers, check=check)


def filter_venue(papers: list, venue: str):
    venue = str_normalize(venue)
    def check(v:dict):
        name = str_normalize(v["venue"]["name"])

        _check = re.match(f".*{venue}.*", name)

        if not _check:
            logging.debug(f"Based on {name} not matching {venue}, filtered out {v['venue']['name']}")

        return _check

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
        "--authors",
        metavar="STR",
        nargs="*",
        default=None,
        help="Authors names",
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
        default=datetime.now() + timedelta(weeks=52)
    )
    parser.add_argument(
        "--venue",
        metavar="STR",
        default=None,
    )
    options = parser.parse_args()

    logging.info(f"Filtering papers for authors {options.authors}")

    # papers = filter_peer_reviewed(json.loads(options.paperoni.read_text()))
    papers = json.loads(options.paperoni.read_text())

    if options.authors:
        papers = filter_authors(papers, options.authors)

    if options.start or options.end:
        papers = filter_date(papers, options.start, options.end)

    if options.venue:
        papers = filter_venue(papers, options.venue)

    papers = list(papers)
    print(json.dumps(papers, indent=2, sort_keys=True))

    logging.info(f"Filtered {len(papers)} papers")
