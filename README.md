# Oberbaumbrücke[^1]

[![Tests](https://github.com/anapaulagomes/oberbaumbrucke/actions/workflows/ci.yml/badge.svg)](https://github.com/anapaulagomes/oberbaumbrucke/actions/workflows/ci.yml)

A multilingual bridge between ICD-10 versions.

[^1]: https://en.wikipedia.org/wiki/Oberbaum_Bridge

## Usage

Create a graph from the data:

```bash
oberbaum graph create icd-10-who data/icd102019enMeta
oberbaum graph create cid-10-bra data/CID-10-2025
oberbaum graph create icd-10-gm data/icd10gm2025/Klassifikationsdateien --export  # this create a graph file icd-10-gm.gml
oberbaum graph create icd-10-cm data/icd10cm-table-index-April-2025
```

Finding the CM code corresponding to the GM code:

```bash
oberbaum graph match icd-10-who icd-10-who.gml cid-10-bra cid-10-bra.gml --output "icd-10-who___cid-10-bra.csv"
```

## Development

First, install [uv](https://docs.astral.sh/uv/).

### Install dependencies

```bash
uv sync
```

`pygraphviz` is also required. Please follow the instructions [here](https://pygraphviz.github.io/) to install it.
If you have any issues with `pygraphviz`, you can try the troubleshooting steps described below.

### Activate the virtual environment

```bash
source .venv/bin/activate
```

Then, create the db: `oberbaum db create` (you can pass the db name with `--db-name <name>`).

### Run tests

```bash
uv run pytest
```

### Troubleshooting

#### Pygraphviz

```
export C_INCLUDE_PATH="$(brew --prefix graphviz)/include/"
export LIBRARY_PATH="$(brew --prefix graphviz)/lib/"
uv pip install --config-setting="--global-option=build_ext" pygraphviz
```

In case the issues to install it persists, try the other solutions presented [here](https://github.com/HalcyonSolutions/MultiHopKG/issues/16).
