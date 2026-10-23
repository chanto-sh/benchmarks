#!/bin/bash
set -e
cp -R "$(dirname "$0")/pristine/." .
python3 -m unittest -q bottle_song_test
