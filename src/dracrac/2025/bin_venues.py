from datetime import datetime
import io
import json
from pathlib import Path
from pprint import pprint


json_file = Path("all_w_dates.json")
papers = json.loads(json_file.read_text())

papers = []
for json_file in Path("2023-04-2024-04/ICLR").glob("*.json"):
    papers.extend(json.loads(json_file.read_text()))

# out = io.StringIO()

venues_map = {}
papers_titles = set()

for p in papers:
    if p['title'] in papers_titles:
        print(f"filtered title:{p['title']}")
        continue

    for v in p["releases"]:
        v_name = v["venue"]["name"]
        v_type = v['venue']['type']
        v_date = datetime.fromtimestamp(v["venue"]["date"]["timestamp"])
        if v["status"] in ("rejected", "withdrawn"):
            print(f"filtered status:{v['status']}")
            continue
        if v_date < datetime(2023, 4, 1) or v_date >= datetime(2024, 4, 1):
            print(f"filtered date:{v_date}")
            continue
        if not any(conf in v_name.lower() for conf in ("icml", "iclr", "neurips")):
            print(f"filtered conf:{v_name}")
            continue
        venues_map.setdefault((v_type, v["status"], v_name), set())
        venues_map[(v_type, v["status"], v_name)].add(p['title'])
        # print(date, p['title'], v_type, name, file=out)

    papers_titles.add(p['title'])

pprint(venues_map, width=160)

# cnts = {}
# for (v_type, status, name), titles in venues_map.items():
#     for conf in ("icml", "iclr", "neurips"):
#         if conf in name.lower():
#             break
#     else:
#         assert False

#     # print(conf, name)
#     cnts.setdefault(conf, set())
#     cnts[conf].update(titles)

# for conf, titles in cnts.items():
#     print(len(titles), "\t", conf)

cnts = sorted((len(set(titles)), v) for v, titles in venues_map.items())
all_titles = set()
list(map(all_titles.update, venues_map.values()))
pprint(sorted(all_titles), width=160)

for c in cnts:
    print(c[0], "\t", *c[1])
# print(*cnts, sep="\n")
print(sum(c[0] for c in cnts))
print(len(all_titles))
# print(*sorted(out.getvalue().splitlines()), sep="\n")
