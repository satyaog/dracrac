#!/bin/bash

dir=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
years=$( cd "$(dirname "${dir}")" ; basename "${PWD}" )
json=$( cd "${dir}" ; ls paperoni-*-"${years}".json )
# remove extension
json="${json%.*}"

cat "${dir}"/../authors | while read author
do
    python3 filter.py "${dir}"/"${json}".json --author "${author}" \
    >"${dir}"/"${json}"_"${author// /_}".json
done
