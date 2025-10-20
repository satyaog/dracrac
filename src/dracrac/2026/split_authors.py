# for author in ...
# do
#   python3 filter.py paperoni-2024-10-09.json --author "${author}" >paperoni-2024-10-09_"${author// /_}".json
# done
import argparse
import json
import logging
import re
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


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


def filter_authors(papers: list[dict[str, Any | str]], author_emails: list):
    author_emails = set(author_emails)

    for p in papers:
        p_authors = {a["author"]["name"] for a in p["authors"]}

        for link in (link for a in p["authors"] for link in a["author"]["links"]):
            if link["type"].startswith("email"):
                email = link["link"].lower()
                if email in author_emails:
                    break

        else:
            logging.debug(
                f"Based on the author_emails not intersecting with {sorted(p_authors)}, filtered out {p['title']}"
            )
            continue

        yield p


def filter_peer_reviewed(papers: list):
    def check(v: dict):
        _check = v["peer_reviewed"] and v["status"] not in ["rejected", "withdrawn"]

        if not _check:
            logging.debug(
                f"Based on peer reviewed:{v['peer_reviewed']} and status:{v['status']}, filtered out {v['venue']['name']}"
            )

        return _check

    yield from filter_on_releases(papers, check=check)


def filter_date(papers: list, start: datetime, end: datetime):
    def check(v: dict):
        date = datetime.fromtimestamp(v["venue"]["date"]["timestamp"])

        _check = date >= start and date < end

        if not _check:
            logging.debug(
                f"Based on {start} <= {date} < {end}, filtered out {v['venue']['name']}"
            )

        return _check

    yield from filter_on_releases(papers, check=check)


def filter_papers(
    papers: list, author_emails: list[str], start: datetime, end: datetime
) -> list:
    papers = filter_peer_reviewed(papers)

    if author_emails:
        papers = filter_authors(papers, author_emails)

    if start or end:
        papers = filter_date(papers, start, end)

    return list(papers)


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
        metavar="TXT",
        type=Path,
        help="Authors emails file",
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
        default=datetime.now() + timedelta(weeks=52),
    )
    parser.add_argument(
        "--out",
        metavar="DIR",
        type=Path,
        default=None,
        help="Output directory",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=None,
        help="Set output verbosity",
    )
    options = parser.parse_args()

    if options.out is None:
        options.out = options.paperoni.resolve().parent

    logging.basicConfig(
        level=(
            (logging.CRITICAL - options.verbose * 10)
            if options.verbose is not None
            else logging.INFO
        )
    )

    author_emails = (
        sorted(set(options.authors.read_text().splitlines())) if options.authors else []
    )

    logging.info(f"Splitting papers for authors {author_emails}")

    all_papers = json.loads(options.paperoni.read_text())
    papers = filter_papers(all_papers, author_emails, options.start, options.end)

    logging.info(f"Filtered {len(papers)}/{len(all_papers)} papers")

    options.out.mkdir(parents=True, exist_ok=True)

    if not author_emails:
        (
            options.out
            / f"{options.paperoni.stem}-FILTERED-{options.start.strftime('%Y-%m-%d')}-{options.end.strftime('%Y-%m-%d')}.json"
        ).write_text(json.dumps(papers, indent=2, ensure_ascii=False))

    for author_email in author_emails:
        author_id = "_".join(
            [
                author_email.split("@")[
                    0
                ],  # sha256(author_email.encode()).hexdigest()[:8]
            ]
        )
        author_papers = list(filter_authors(papers, [author_email]))
        (options.out / f"{author_id}.json").write_text(
            json.dumps(author_papers, indent=2, ensure_ascii=False)
        )
        logging.info(
            f"Filtered {len(author_papers)}/{len(papers)} papers for {author_email}"
        )
