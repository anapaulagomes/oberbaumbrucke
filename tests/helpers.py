import zipfile
from pathlib import Path

import requests


def download_and_unzip(url, target_file_dir, filename):
    target_file_dir_path = Path(target_file_dir)
    if target_file_dir_path.exists() is False:
        response = requests.get(url)
        response.raise_for_status()
        target_file_dir_path.mkdir(parents=True, exist_ok=True)
        with open(f"{target_file_dir}/{filename}", "wb") as output_file:
            output_file.write(response.content)
        with zipfile.ZipFile(f"{target_file_dir}/{filename}", "r") as zip_ref:
            zip_ref.extractall(target_file_dir)
    return target_file_dir
