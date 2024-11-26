#!/bin/bash

dir=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
dates=$( cd "${dir}" ; basename "${PWD}" )
start=$(echo "${dates}" | cut -d'-' -f1-2)-01
end=$(echo "${dates}" | cut -d'-' -f3-4)-01
json="paperoni-2024-10-09-2022-2025"

for venue in ICLR
do
    mkdir -p "${dir}/${venue}"
    cat "${dir}/../2022-2025/authors" | while read author
    do
        python3 filter.py "${dir}/../2022-2025/paperoni/${json}.json" --authors "${author}" \
        > "${dir}/${venue}/${author// /_}.json"
    done
done

ls -d "${dir}"/{ICLR,ICML,NeurIPS}/ | while read d
do
    ls "$d" | while read f
    do
        echo "$f" ; python3 -c "
from pathlib import Path
import json
for p in json.loads(Path('$d$f').read_text()):
  print('paper:'+p['title'], *[(v['venue']['name'], v['venue']['type'], v['venue']['date']['text']) for v in p['releases']], sep='\n  ')
"
    done
done >"${dir}"/ICLR-ICML-NeurIPS.out
