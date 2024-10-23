# for author in ...
# do
#   python3 print_ref.py paperoni-2024-10-09.json --year 2024 --format json >"${author}".html
# done
import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)


def list_papers(json_data: dict, year: datetime):
    for p in json_data:
        authors = [a["author"]["name"] for a in p["authors"]]
        title = p["title"]
        venue = None
        date = None
        url = None

        for v in p["releases"]:
            _date = datetime.fromtimestamp(v["venue"]["date"]["timestamp"])
            if not v["peer_reviewed"] or v["status"] == "rejected" or _date < year:
                continue

            v = v["venue"]

            if v["type"] in ("conference", "symposium"):
                venue = v["volume"]
            else:
                venue = v["name"]

            date = _date.year

            logging.debug(
                "Selected [{}] from\n  {}".format(
                    venue, "\n  ".join([str(_) for _ in p["releases"]])
                )
            )
            break
        else:
            logging.error(
                "Could not find a suitable venue for paper {} in\n  {}".format(
                    title, "\n  ".join([str(_["venue"]) for _ in p["releases"]])
                )
            )

        for l in p["links"]:
            if "url" in l:
                url = l["url"]

                logging.debug(
                    "Selected [{}] from\n  {}".format(
                        url, "\n  ".join([str(_) for _ in p["links"]])
                    )
                )
                break
        else:
            logging.error(
                "Could not find a suitable link for paper {} in\n  {}".format(
                    title, "\n  ".join([str(_) for _ in p["links"]])
                )
            )

        if not all([venue, date]):
            continue

        yield (
            authors,
            title,
            venue,
            date,
            url,
        )


def format_html(papers: list):
    print("<ul>")
    for authors, title, venue, date, url in papers:
        authors = [[part for part in a.split(" ") if part] for a in authors]
        authors = [
            f"{name[-1]} {''.join([n[0] for n in name[:-1]])}" for name in authors
        ]
        url = [f"Available: <a href='{url}'>{url}</a>"] if url else []
        print("<li>", end="")
        print(
            ". ".join(
                (
                    ", ".join(authors).rstrip("."),
                    title.rstrip("."),
                    venue.rstrip("."),
                    str(date),
                    *url,
                )
            ),
            end="",
        )
        print("</li>")
    print("</ul>")


def format_json(papers: list):
    print(
        json.dumps(
            [
                {
                    "author": authors,
                    "title": title,
                    "journal": venue,
                    "year": date,
                    "url": url,
                }
                for authors, title, venue, date, url in papers
            ],
            indent=2,
        )
    )


def format_plain(papers: list):
    for authors, title, venue, date, url in papers:
        authors = [[part for part in a.split(" ") if part] for a in authors]
        authors = [
            f"{name[-1]} {''.join([n[0] for n in name[:-1]])}" for name in authors
        ]
        url = [f"Available: {url}"] if url else []
        print(
            ". ".join(
                (
                    ", ".join(authors).rstrip("."),
                    title.rstrip("."),
                    venue.rstrip("."),
                    str(date),
                    *url,
                )
            ),
        )


FORMAT_MAP = {
    "html": format_html,
    "json": format_json,
    "txt": format_plain,
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paperoni",
        metavar="JSON",
        type=Path,
        help="Paperoni json output of papers to filter",
    )
    parser.add_argument(
        "--year",
        metavar="YYYY",
        default=datetime(1970, 1, 1),
        type=lambda value: datetime.strptime(value, "%Y"),
        help="Publication date",
    )
    parser.add_argument(
        "--format",
        metavar="FMT",
        default="txt",
        choices=list(FORMAT_MAP.keys()),
        type=str,
        help="Output format",
    )
    options = parser.parse_args()

    FORMAT_MAP[options.format](
        list_papers(json.loads(options.paperoni.read_text()), options.year)
    )
