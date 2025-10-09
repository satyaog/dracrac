# for author in ...
# do
#   python3 print_ref.py paperoni-2024-10-09.json --year 2024 --format json >"${author}".html
# done
import argparse
import csv
import io
import json
import logging
from datetime import datetime
from pathlib import Path


def list_papers(papers: dict):
    for p in papers:
        authors = [a["author"]["name"] for a in p["authors"]]
        title = p["title"]
        venue = None
        year = None
        url = None

        for v in p["releases"]:
            _date = datetime.fromtimestamp(v["venue"]["date"]["timestamp"])
            if not v["peer_reviewed"] or v["status"] == "rejected":
                continue

            v = v["venue"]

            if v["type"] in ("conference", "symposium"):
                venue = v["volume"]

            if not venue:
                venue = v["name"]

            year = _date.year

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

        if not all([venue, year]):
            continue

        yield (
            title,
            venue,
            year,
            authors,
            url,
        )


def format_data(prof, papers: list):
    return [
        {
            "prof": prof,
            "title": title,
            "journal": venue,
            "year": year,
            "authors": authors,
            "url": url,
        }
        for title, venue, year, authors, url in papers
    ]


def format_json(data: list[dict]):
    return json.dumps(data, indent=2, ensure_ascii=False)


def format_csv(data: list[dict]):
    if not data:
        return ""
    output = io.StringIO()
    fieldnames = list(next(iter(data), {}).keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for paper in data:
        row = {**paper}
        # Expand authors into separate rows
        for author in row.pop("authors"):
            writer.writerow({**row, "authors": author})
    return output.getvalue()


FORMAT_MAP = {
    "json": format_json,
    "csv": format_csv,
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paperoni",
        metavar="JSON",
        nargs="+",
        type=Path,
        help="Paperoni json outputs of papers to print",
    )
    parser.add_argument(
        "--format",
        metavar="FMT",
        default="json",
        choices=list(FORMAT_MAP.keys()),
        type=str,
        help="Output format",
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

    logging.basicConfig(
        level=(
            (logging.CRITICAL - options.verbose * 10)
            if options.verbose is not None
            else logging.INFO
        )
    )

    content = []
    for paperoni in options.paperoni:
        paperoni: Path
        prof = f"{paperoni.stem}@mila.quebec"
        content.extend(format_data(prof, list_papers(json.loads(paperoni.read_text()))))

    if options.out is not None:
        options.out.parent.mkdir(parents=True, exist_ok=True)

    (options.out.write_text if options.out else print)(
        FORMAT_MAP[options.format](content)
    )
