# Oberbaumbrücke[^1]

[![DOI](https://zenodo.org/badge/960290910.svg)](https://doi.org/10.5281/zenodo.19249566) [![Tests](https://github.com/anapaulagomes/oberbaumbrucke/actions/workflows/ci.yml/badge.svg)](https://github.com/anapaulagomes/oberbaumbrucke/actions/workflows/ci.yml)

A multilingual bridge between ICD-10 versions.

[^1]: https://en.wikipedia.org/wiki/Oberbaum_Bridge

This project consists of three main components:

1. ICD-10 modelled as a graph (currently available for WHO, Brazil, Germany and USA, but easily extendable for other national versions)
2. Comparison of semantic similarity between ICD-10 codes using different multilingual embedding models

## Usage

### Graphs

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

### Subgraphs

```
oberbaum graph subgraph icd-10-who data/icd102019enMeta "X53" --include-children
oberbaum graph subgraph icd-10-cm data/icd10cm-table-index-April-2025 "H938" --include-children
```

### Embeddings

To run this step you will need all graphs from the previous section.
After, create the db: `oberbaum db create` (you can pass the db name with `--db-name <name>`). Then, run:

```bash
oberbaum graph embeddings
```

It will encode all descriptions from all codes for [all models](oberbaum/models.py) and store them in a table.

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

### Running experiments in HPC

You can run the experiments in Slurm by using the bash script in `bin/graphs_match.sh`.
Make a copy of the script and edit it to your needs. The experiment will run the matches from
the versions available against the WHO 2019 version. For this, you will need to have:

1. All versions graph files created upfront (use the command `oberbaum graph create`)
2. Embeddings stored in the db

It will run all thresholds from 0.3-0.9, with all [models available](oberbaum/models.py).

You can run all these steps with `bin/prepare_matches.sh` assuming data the version's file are in the `data/` directory.

Run the parallel jobs with: `sbatch bin/graphs_match.sh`

### Troubleshooting

#### Pygraphviz

```
export C_INCLUDE_PATH="$(brew --prefix graphviz)/include/"
export LIBRARY_PATH="$(brew --prefix graphviz)/lib/"
uv pip install --config-setting="--global-option=build_ext" pygraphviz
```

In case the issues to install it persists, try the other solutions presented [here](https://github.com/HalcyonSolutions/MultiHopKG/issues/16).
