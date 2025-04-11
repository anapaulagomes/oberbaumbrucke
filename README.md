# Oberbaumbrücke[^1]

[![Tests](https://github.com/anapaulagomes/oberbaumbrucke/actions/workflows/ci.yml/badge.svg)](https://github.com/anapaulagomes/oberbaumbrucke/actions/workflows/ci.yml)

A multilingual bridge between ICD-10 versions.

[^1]: https://en.wikipedia.org/wiki/Oberbaum_Bridge

## Usage

First, install [uv](https://docs.astral.sh/uv/).

Create a graph from the data:

```bash
oberbaum graph create data/icd102019enMeta
```

Finding the CM code corresponding to the GM code:

```bash
oberbaum match "icd-10-gm" "icd-10-cm" --output "icd-10-gm___icd-10-cm.csv"
```

## Development

### Install dependencies

```bash
uv sync
```

### Activate the virtual environment

```bash
source .venv/bin/activate
```

### Run tests

```bash
uv run pytest
```
