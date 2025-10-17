# Oberbaumbrücke[^1]

[![Tests](https://github.com/anapaulagomes/oberbaumbrucke/actions/workflows/ci.yml/badge.svg)](https://github.com/anapaulagomes/oberbaumbrucke/actions/workflows/ci.yml)

A multilingual bridge between ICD-10 versions.

[^1]: https://en.wikipedia.org/wiki/Oberbaum_Bridge

This project consists of three main components:

1. ICD-10 modelled as a graph (currently available for WHO, Brazil, Germany and USA)
2. Comparison of semantic similarity between ICD-10 codes using different multilingual embedding models
3. Comparison of the ICD-10 versions through its graph structure using Maximum Common Embedded Subtree (MCES)

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

### Embeddings

To run this step you will need all graphs from the previous section.
After, create the db: `oberbaum db create` (you can pass the db name with `--db-name <name>`). Then, run:

```bash
oberbaum graph embeddings
```

It will encode all descriptions from all codes for [all models](oberbaum/icd_graph/models.py) and store them in a table.

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

You can run the graph overlap experiment in Slurm by using the bash script in `bin/graphs_overlap_array.sh`.
Make a copy of the script and edit it to your needs. The experiment will check the overlap from a version against
the WHO 2019 version.
To run it, you will need to specify a list of jobs with the params required for the command:

```bash
oberbaum graph experiments graphs_overlap --method mcosi --chapter $CHAPTER --graph-version-name $GRAPH --threshold $THRESHOLD
```

You can accomplish this with this bash script:

```bash
./bin/generate_jobs.sh icd-10-gm cid-10-bra > jobs.txt
```

In the example above, we are generating the params for each chapter for two versions: `cid-10-bra` and `icd-10-gm`.
This is the format expected:

```text
icd-10-gm 1 0.75
icd-10-gm 1 0.8
icd-10-gm 1 0.85
icd-10-gm 1 0.9
icd-10-gm 1 0.95
...
cid-10-bra 22 0.8
cid-10-bra 22 0.85
cid-10-bra 22 0.9
cid-10-bra 22 0.95
```

After the `jobs.txt` is created, you're ready to run: `sbatch graphs_overlap_array.sh`

### Troubleshooting

#### Pygraphviz

```
export C_INCLUDE_PATH="$(brew --prefix graphviz)/include/"
export LIBRARY_PATH="$(brew --prefix graphviz)/lib/"
uv pip install --config-setting="--global-option=build_ext" pygraphviz
```

In case the issues to install it persists, try the other solutions presented [here](https://github.com/HalcyonSolutions/MultiHopKG/issues/16).
