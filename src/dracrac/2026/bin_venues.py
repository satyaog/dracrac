# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pyyaml",
#   "rootutils",
# ]
# ///

import argparse
import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import yaml

try:
    from .filter import filter_papers

except ImportError:
    import rootutils

    rootutils.setup_root(__file__, indicator=".project-root")
    from filter import filter_papers  # pyright: ignore[reportMissingImports]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paperoni",
        metavar="JSON",
        type=Path,
        help="Paperoni json output of papers to filter",
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
        "--bins",
        metavar="YAML",
        type=Path,
        default=None,
        help="YAML file containing venue bin names and aliases",
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

    papers = json.loads(options.paperoni.read_text())
    papers = filter_papers(papers, None, options.start, options.end)

    venue_papers = defaultdict(set)
    for paper in papers:
        for v in paper["releases"]:
            v = v["venue"]
            venue_name = None
            if v["type"] in ("conference", "symposium"):
                venue_name = v["volume"]
            if not venue_name:
                venue_name = v["name"]
            venue_papers[venue_name].add(paper["title"].lower().strip())

    if options.bins is not None:
        bins = yaml.safe_load(options.bins.read_text())
        for name, aliases in bins.items():
            bins[name] = sorted(set(aliases + [name.lower()]))

        venues = defaultdict(set)
        for venue, papers in venue_papers.items():
            for bin, aliases in bins.items():
                if any(alias.lower() in venue.lower() for alias in aliases):
                    venues[bin].update(papers)
    else:
        venues = venue_papers

    counter = Counter({venue: len(papers) for venue, papers in venues.items()})

    content = []
    for venue, count in sorted(counter.items()):
        content.append(f"{count:>4}  {venue}")

    (options.out.write_text if options.out else print)("\n".join(content))
