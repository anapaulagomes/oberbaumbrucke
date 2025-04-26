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


@pytest.fixture(scope="class")
def real_cid10_bra_file_dir():
    icd_file_dir = "data/CID10CSV"
    if Path(icd_file_dir).exists() is False:
        response = requests.get(
            "http://www2.datasus.gov.br/cid10/V2008/downloads/CID10CSV.zip"
        )
        response.raise_for_status()
        Path(icd_file_dir).mkdir(parents=True, exist_ok=True)
        with open(f"{icd_file_dir}/CID10CSV.zip", "wb") as output_file:
            output_file.write(response.content)
        with zipfile.ZipFile(f"{icd_file_dir}/CID10CSV.zip", "r") as zip_ref:
            zip_ref.extractall(icd_file_dir)
    yield icd_file_dir


@pytest.fixture
def cid10_bra_file_dir(tmp_path):
    chapters_file = tmp_path / "CID-10-CAPITULOS.CSV"
    chapters_file.write_text(
        "NUMCAP;CATINIC;CATFIM;DESCRICAO;DESCRABREV;\n"
        "1;A00;B99;Capítulo I - Algumas doenças infecciosas e parasitárias;I.   Algumas doenças infecciosas e parasitárias;\n"
        "2;C00;D48;Capítulo II - Neoplasias [tumores];II.  Neoplasias (tumores);\n"
        "3;D50;D89;Capítulo III  - Doenças do sangue e dos órgãos hematopoéticos e alguns transtornos imunitários;III. Doenças sangue órgãos hemat e transt imunitár;\n"
    )
    categories_file = tmp_path / "CID-10-CATEGORIAS.CSV"
    categories_file.write_text(
        "CAT;CLASSIF;DESCRICAO;DESCRABREV;REFER;EXCLUIDOS;\n"
        "A00;;Cólera;A00   Colera;;;\n"
        "A01;;Febres tifóide e paratifóide;A01   Febres tifoide e paratifoide;;;\n"
        "A02;;Outras infecções por Salmonella;A02   Outr infecc p/Salmonella;;;\n"
        "A03;;Shiguelose;A03   Shiguelose;;;\n"
        "A04;;Outras infecções intestinais bacterianas;A04   Outr infecc intestinais bacter;;;\n"
    )
    subcategories_file = tmp_path / "CID-10-SUBCATEGORIAS.CSV"
    subcategories_file.write_text(
        "SUBCAT;CLASSIF;RESTRSEXO;CAUSAOBITO;DESCRICAO;DESCRABREV;REFER;EXCLUIDOS;\n"
        "A000;;;;Cólera devida a Vibrio cholerae 01, biótipo cholerae;A00.0 Colera dev Vibrio cholerae 01 biot cholerae;;;\n"
        "A001;;;;Cólera devida a Vibrio cholerae 01, biótipo El Tor;A00.1 Colera dev Vibrio cholerae 01 biot El Tor;;;\n"
        "A009;;;;Cólera não especificada;A00.9 Colera NE;;;\n"
        "A010;;;;Febre tifóide;A01.0 Febre tifoide;;;\n"
    )

    blocks_file = tmp_path / "CID-10-GRUPOS.CSV"
    blocks_file.write_text(
        "CATINIC;CATFIM;DESCRICAO;DESCRABREV;\n"
        "A00;A09;Doenças infecciosas intestinais;Doenças infecciosas intestinais;\n"
        "A15;A19;Tuberculose;Tuberculose;\n"
        "A20;A28;Algumas doenças bacterianas zoonóticas;Algumas doenças bacterianas zoonóticas;\n"
    )
    return str(tmp_path)


@pytest.fixture
def icd10_gm_file_dir(tmp_path):
    chapters_file = tmp_path / "icd10gm2025syst_kapitel.txt"
    chapters_file.write_text(
        "20;Äußere Ursachen von Morbidität und Mortalität\n"
        "21;Faktoren, die den Gesundheitszustand beeinflussen und zur Inanspruchnahme des Gesundheitswesens führen\n"
        "22;Schlüsselnummern für besondere Zwecke\n"
    )
    blocks_file = tmp_path / "icd10gm2025syst_gruppen.txt"
    blocks_file.write_text(
        "Y40;Y84;20;Komplikationen bei der medizinischen und chirurgischen Behandlung\n"
        "Z00;Z13;21;Personen, die das Gesundheitswesen zur Untersuchung und Abklärung in Anspruch nehmen\n"
        "Z20;Z29;21;Personen mit potentiellen Gesundheitsrisiken hinsichtlich übertragbarer Krankheiten\n"
    )
    codes_file = tmp_path / "icd10gm2025syst_kodes.txt"
    codes_file.write_text(
        "3;N;X;21;Z20;Z20.-;Z20;Z20;Kontakt mit und Exposition gegenüber übertragbaren Krankheiten;Kontakt mit und Exposition gegenüber übertragbaren Krankheiten;;;V;V;UNDEF;UNDEF;UNDEF;UNDEF;292;9;9;9999;9999;9;N;J;N;N\n"
        "4;T;X;21;Z20;Z20.0;Z20.0;Z200;Kontakt mit und Exposition gegenüber infektiösen Darmkrankheiten;Kontakt mit und Exposition gegenüber übertragbaren Krankheiten;Kontakt mit und Exposition gegenüber infektiösen Darmkrankheiten;;P;P;UNDEF;UNDEF;UNDEF;UNDEF;292;9;9;9999;9999;9;N;J;N;N\n"
        "4;T;X;21;Z20;Z20.1;Z20.1;Z201;Kontakt mit und Exposition gegenüber Tuberkulose;Kontakt mit und Exposition gegenüber übertragbaren Krankheiten;Kontakt mit und Exposition gegenüber Tuberkulose;;P;P;UNDEF;UNDEF;UNDEF;UNDEF;292;9;9;9999;9999;9;N;J;N;N\n"
        "4;T;X;21;Z20;Z20.2;Z20.2;Z202;Kontakt mit und Exposition gegenüber Infektionen, die vorwiegend durch Geschlechtsverkehr übertragen werden;Kontakt mit und Exposition gegenüber übertragbaren Krankheiten;Kontakt mit und Exposition gegenüber Infektionen, die vorwiegend durch Geschlechtsverkehr übertragen werden;;P;P;UNDEF;UNDEF;UNDEF;UNDEF;292;9;9;9999;9999;9;N;J;N;N\n"
        "4;T;X;21;Z20;Z20.3;Z20.3;Z203;Kontakt mit und Exposition gegenüber Tollwut;Kontakt mit und Exposition gegenüber übertragbaren Krankheiten;Kontakt mit und Exposition gegenüber Tollwut;;P;P;UNDEF;UNDEF;UNDEF;UNDEF;292;9;9;9999;9999;9;N;J;N;N\n"
        "4;T;X;21;Z20;Z20.4;Z20.4;Z204;Kontakt mit und Exposition gegenüber Röteln;Kontakt mit und Exposition gegenüber übertragbaren Krankheiten;Kontakt mit und Exposition gegenüber Röteln;;P;P;UNDEF;UNDEF;UNDEF;UNDEF;292;9;9;9999;9999;9;N;J;N;N\n"
        "4;T;X;21;Z20;Z20.5;Z20.5;Z205;Kontakt mit und Exposition gegenüber Virushepatitis;Kontakt mit und Exposition gegenüber übertragbaren Krankheiten;Kontakt mit und Exposition gegenüber Virushepatitis;;P;P;UNDEF;UNDEF;UNDEF;UNDEF;292;9;9;9999;9999;9;N;J;N;N\n"
        "4;T;X;21;Z20;Z20.6;Z20.6;Z206;Kontakt mit und Exposition gegenüber HIV [Humanes Immundefizienz-Virus];Kontakt mit und Exposition gegenüber übertragbaren Krankheiten;Kontakt mit und Exposition gegenüber HIV [Humanes Immundefizienz-Virus];;P;P;UNDEF;UNDEF;UNDEF;UNDEF;292;9;9;9999;9999;9;N;J;N;N\n"
        "4;T;X;21;Z20;Z20.7;Z20.7;Z207;Kontakt mit und Exposition gegenüber Pedikulose [Läusebefall], Akarinose [Milbenbefall] oder anderem Parasitenbefall;Kontakt mit und Exposition gegenüber übertragbaren Krankheiten;Kontakt mit und Exposition gegenüber Pedikulose [Läusebefall], Akarinose [Milbenbefall] oder anderem Parasitenbefall;;P;P;UNDEF;UNDEF;UNDEF;UNDEF;292;9;9;9999;9999;9;N;J;N;N\n"
        "4;T;X;21;Z20;Z20.8;Z20.8;Z208;Kontakt mit und Exposition gegenüber sonstigen übertragbaren Krankheiten;Kontakt mit und Exposition gegenüber übertragbaren Krankheiten;Kontakt mit und Exposition gegenüber sonstigen übertragbaren Krankheiten;;P;P;UNDEF;UNDEF;UNDEF;UNDEF;292;9;9;9999;9999;9;N;J;N;N\n"
        "4;T;X;21;Z20;Z20.9;Z20.9;Z209;Kontakt mit und Exposition gegenüber nicht näher bezeichneter übertragbarer Krankheit;Kontakt mit und Exposition gegenüber übertragbaren Krankheiten;Kontakt mit und Exposition gegenüber nicht näher bezeichneter übertragbarer Krankheit;;P;P;UNDEF;UNDEF;UNDEF;UNDEF;292;9;9;9999;9999;9;N;J;N;N\n"
        "3;T;X;21;Z20;Z21;Z21;Z21;Asymptomatische HIV-Infektion [Humane Immundefizienz-Virusinfektion];Asymptomatische HIV-Infektion [Humane Immundefizienz-Virusinfektion];;;P;P;UNDEF;UNDEF;UNDEF;UNDEF;291;9;9;9999;9999;9;N;J;N;N\n"
        "3;N;X;21;Z20;Z22.-;Z22;Z22;Keimträger von Infektionskrankheiten;Keimträger von Infektionskrankheiten;;;V;V;UNDEF;UNDEF;UNDEF;UNDEF;292;9;9;9999;9999;9;N;J;N;N\n"
    )
    return str(tmp_path)


@pytest.fixture(scope="class")
def real_icd10_gm_file_dir():
    icd_file_dir = Path("data/icd10gm2025")
    if icd_file_dir.exists() is False:
        response = requests.get(
            "https://multimedia.gsb.bund.de/BfArM/downloads/klassifikationen/icd-10-gm/version2025/icd10gm2025syst-meta.zip"
        )
        response.raise_for_status()

        icd_file_dir.mkdir(parents=True, exist_ok=True)

        zip_path = f"{icd_file_dir}/icd10gm2025syst-meta.zip"
        with open(zip_path, "wb") as output_file:
            output_file.write(response.content)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(icd_file_dir)

    yield icd_file_dir / "Klassifikationsdateien"


@pytest.fixture(scope="class")
def real_icd10_cm_file_dir():
    icd_file_dir = Path("data/icd10cm-table-index-April-2025")
    if icd_file_dir.exists() is False:
        response = requests.get(
            "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/ICD10CM/2025-Update/icd10cm-table-index-April-2025.zip"
        )
        response.raise_for_status()

        icd_file_dir.mkdir(parents=True, exist_ok=True)

        zip_path = f"{icd_file_dir}/icd10cm-table-index-April-2025.zip"
        with open(zip_path, "wb") as output_file:
            output_file.write(response.content)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(icd_file_dir)

    yield icd_file_dir
