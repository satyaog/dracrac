#!/bin/bash

dir=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
years=$( cd "$(dirname "${dir}")" ; basename "${PWD}" )
json=$( cd "${dir}/../paperoni" ; ls paperoni-*-"${years}".json )
# remove extension
json="${json%.*}"

for fmt in html json out
do

if [[ "${fmt}" == "json" ]]
then
    echo "{" >"${dir}"/ALL."${fmt}"
else
    echo -n "" >"${dir}"/ALL."${fmt}"
fi

cat "${dir}"/../authors | while read author
do
    if [[ "${fmt}" == "json" ]]
    then
        echo -n "\"${author}\": {\"papers\": " >>"${dir}"/ALL."${fmt}"
    elif [[ "${fmt}" == "html" ]]
    then
        echo "<h3>${author}</h3>" >>"${dir}"/ALL."${fmt}"
    elif [[ "${fmt}" == "out" ]]
    then
        echo "${author}" >>"${dir}"/ALL."${fmt}"
    fi

    python3 print_ref.py "${dir}"/../paperoni/"${json}"_"${author// /_}".json --format "${fmt}" \
    >>"${dir}"/ALL."${fmt}"

    if [[ "${fmt}" == "json" ]]
    then
        # The last "," needs to be removed
        echo "}," >>"${dir}"/ALL."${fmt}"
    elif [[ "${fmt}" == "out" ]]
    then
        echo "" >>"${dir}"/ALL."${fmt}"
    fi
done

if [[ "${fmt}" == "json" ]]
then
    echo "}" >>"${dir}"/ALL."${fmt}"
fi

done
