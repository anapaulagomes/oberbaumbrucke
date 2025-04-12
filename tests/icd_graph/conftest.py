import zipfile
from pathlib import Path

import pytest
import requests


@pytest.fixture
def icd10_who_file_dir(tmp_path):
    chapters_file = tmp_path / "icd102019syst_chapters.txt"
    chapters_file.write_text(
        "01;Certain infectious and parasitic diseases\n"
        "02;Neoplasms\n"
        "03;Diseases of the blood and blood-forming organs and certain disorders involving the immune mechanism\n"
        "04;Endocrine, nutritional and metabolic diseases\n"
        "05;Mental and behavioural disorders\n"
    )
    codes_file = tmp_path / "icd102019syst_codes.txt"
    codes_file.write_text(
        "3;N;X;01;A00;A00.-;A00;A00;Cholera;Cholera;;;001;4-002;3-003;2-001;1-002\n"
        "4;T;X;01;A00;A00.0;A00.0;A000;Cholera due to Vibrio cholerae 01, biovar cholerae;Cholera;Cholera due to Vibrio cholerae 01, biovar cholerae;;001;4-002;3-003;2-001;1-002\n"
        "4;T;X;01;A00;A00.1;A00.1;A001;Cholera due to Vibrio cholerae 01, biovar eltor;Cholera;Cholera due to Vibrio cholerae 01, biovar eltor;;001;4-002;3-003;2-001;1-002\n"
        "4;T;X;01;A00;A00.9;A00.9;A009;Cholera, unspecified;Cholera;Cholera, unspecified;;001;4-002;3-003;2-001;1-002\n"
    )
    blocks_file = tmp_path / "icd102019syst_groups.txt"
    blocks_file.write_text(
        "A00;A09;01;Intestinal infectious diseases\nA15;A19;01;Tuberculosis\n"
    )
    return str(tmp_path)


@pytest.fixture(scope="class")
def real_icd10_who_file_dir():
    icd_file_dir = "data/icd102019enMeta"
    if Path(icd_file_dir).exists() is False:
        response = requests.get("https://icdcdn.who.int/icd10/meta/icd102019enMeta.zip")
        response.raise_for_status()
        Path(icd_file_dir).mkdir(parents=True, exist_ok=True)
        with open(f"{icd_file_dir}/icd102019enMeta.zip", "wb") as output_file:
            output_file.write(response.content)
        with zipfile.ZipFile(f"{icd_file_dir}/icd102019enMeta.zip", "r") as zip_ref:
            zip_ref.extractall(icd_file_dir)
    yield icd_file_dir
