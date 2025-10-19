#!/bin/bash
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=example@example
#SBATCH --job-name=graphs_match
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=48:00:00
#SBATCH --array=0-5
#SBATCH --output=log_match_%A_%a.out
#SBATCH --error=log_match_%A_%a.err
source activate py311
source .venv/bin/activate

THRESHOLDS=(0.7 0.75 0.8 0.85 0.9 0.95)
THRESHOLD=${THRESHOLDS[$SLURM_ARRAY_TASK_ID]}

uv run oberbaum graph experiments match_all --threshold "$THRESHOLD"
