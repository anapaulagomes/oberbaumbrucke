#!/bin/bash
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=example@example
#SBATCH --job-name=graphs_overlap_mcosi
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --array=0-65
#SBATCH --output=log_%A_%a.out
#SBATCH --error=log_%A_%a.err
source activate py311
source .venv/bin/activate
LINE=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" jobs.txt)
set -- $LINE
GRAPH=$1
CHAPTER=$3
# example: cid-10-bra-2008 icd-10-who 22
uv run oberbaum graph experiments graphs_overlap --method mcosi --chapter $CHAPTER --graph-version-name $GRAPH
