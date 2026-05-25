#!/bin/bash

tasks=(

)

printf "%s\n" "${tasks[@]}" | xargs -n 2 -P 4 bash -c 'python self-correct-distil.py --model "$0" --task "$1"'