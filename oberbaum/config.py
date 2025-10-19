import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_results_dir(subfolder=None) -> str:
    results_dir = os.getenv("RESULTS_DIR", "results")
    if subfolder:
        results_dir = Path(f"{results_dir}/{subfolder}")
        results_dir.mkdir(exist_ok=True)
        results_dir = str(results_dir)
    return results_dir
