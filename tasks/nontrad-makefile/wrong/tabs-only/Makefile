# Builds dist/summary.json from the per-store sales exports in data/.
PY ?= python3
DATA := $(wildcard data/*.csv)
OUT := dist

all: build

build: $(OUT)/summary.json

$(OUT)/summary.json: scripts/summarize.py
	mkdir -p $(OUT)
	$(PY) scripts/summarize.py $(DATA) > $@

test:
	$(PY) -m unittest discover -s test -v

clean:
	rm -rf $(OUT)
