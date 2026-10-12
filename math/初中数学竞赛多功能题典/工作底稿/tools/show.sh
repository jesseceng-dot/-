#!/bin/bash
# usage: show.sh first last  -> prints linear text and writes img/c_first_last.png
cd /tmp/claude-0/-home-user--/ed1d617a-1db0-5d04-973a-e3f591d01893/scratchpad
a=$1; b=$2
python3 tools/vis.py src/book.pdf $(seq $a $b) | sed -E 's/^ *[0-9.]+ +[0-9.]+ \| //' | grep -v -E '^(1\.[12]|[0-9]+\.[0-9]+) [^ ]+$' 
python3 tools/compact.py src/book.pdf img/c_${a}_${b}.png $(seq $a $b) >/dev/null
