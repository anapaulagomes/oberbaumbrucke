import zipfile
from pathlib import Path
from unittest.mock import Mock

import networkx as nx
import pytest
import requests

from oberbaum.icd_graph import ICDGraph, get_graph, WHOICDGraph


@pytest.fixture
def icd_file_dir(tmp_path):
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
def real_icd_file_dir():
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


class TestWHOICD10Graph:
    def test_create_who_icd10_graph(self, icd_file_dir):
        graph = WHOICDGraph(files_dir=icd_file_dir)
        assert graph.version_name == "icd-10-who"
        assert isinstance(graph.graph, nx.DiGraph)

    def test_get_all_chapters(self, icd_file_dir):
        graph = WHOICDGraph(files_dir=icd_file_dir)
        chapters = graph.chapters()
        assert isinstance(chapters, list)
        assert len(chapters) == 5

    def test_add_codes(self, icd_file_dir):
        graph = WHOICDGraph(files_dir=icd_file_dir)

        assert graph.graph.has_node("A00")
        assert graph.graph.has_node("A000")
        assert graph.graph.has_node("A001")
        assert graph.graph.has_edge("01", "A00-A09")  # chapter - block
        assert graph.graph.has_edge("A00-A09", "A00")  # block - 3-char
        assert graph.graph.has_edge("A00", "A000")  # 3-char - 4-char
        assert graph.graph.has_edge("A00", "A001")  # 3-char - 4-char
        assert graph.graph.has_edge("A00", "A009")  # 3-char - 4-char

    def test_get_codes(self, icd_file_dir):
        graph = WHOICDGraph(files_dir=icd_file_dir)
        codes = graph.codes()

        assert isinstance(codes, set)
        assert len(codes) == 3
        assert "A00" not in codes  # 3-char code
        assert "A000" in codes
        assert "A001" in codes

    def test_get_codes_including_3_char(self, icd_file_dir):
        graph = WHOICDGraph(files_dir=icd_file_dir)
        codes = graph.codes(exclude_3_char=False)

        assert isinstance(codes, set)
        assert len(codes) == 5
        assert "A00" in codes  # 3-char code
        assert "A000" in codes
        assert "A001" in codes

    def test_levels(self, icd_file_dir):
        graph = WHOICDGraph(files_dir=icd_file_dir)
        levels = graph.levels()
        expected_levels = {1: 5, 2: 1, 3: 1, 4: 3}

        assert levels == expected_levels

    def test_blocks(self, icd_file_dir):
        graph = WHOICDGraph(files_dir=icd_file_dir)

        code = graph.graph.nodes["A009"]
        assert code["block"] == "A00-A09"

    def test_export_graph(self, icd_file_dir, monkeypatch):
        graph = WHOICDGraph(files_dir=icd_file_dir)
        mock_write_gml = Mock()
        monkeypatch.setattr(nx, "write_gml", mock_write_gml)

        assert mock_write_gml.called is False

        exported_path = graph.export()

        assert mock_write_gml.called is True
        assert exported_path == "icd-10-who.gml"

    @pytest.mark.integration
    def test_handle_loops(self, real_icd_file_dir):
        graph = WHOICDGraph(files_dir=real_icd_file_dir)
        assert list(nx.nodes_with_selfloops(graph.graph)) == []

    @pytest.mark.integration
    def test_all_codes_needs_to_start_with_a_letter(self, real_icd_file_dir):
        """
        The classification is divided into 21 chapters. The first character of the ICD
        code is a letter, and each letter is associated with a particular chapter, except
        for the letter D, which is used in both Chapter II, Neoplasms, and Chapter III,
        Diseases of the blood and blood-forming organs and certain disorders
        involving the immune mechanism, and the letter H, which is used in both
        Chapter VII, Diseases of the eye and adnexa and Chapter VIII, Diseases of
        the ear and mastoid process

        World Health Organization. (2010). International statistical classification of diseases and related health
        problems (10th revision, 6th ed., Vol. 2). World Health Organization.

        Even though the guideline states 21 chapters, the file has 22 chapters.
        Also in: https://icd.who.int/browse10/2019/en
        """
        graph = WHOICDGraph(files_dir=real_icd_file_dir)
        codes = graph.codes()
        for code in codes:
            assert code[0].isalpha(), f"Code {code} does not start with a letter"

    @pytest.mark.integration
    def test_more_than_one_letter_in_the_first_position(self, real_icd_file_dir):
        """
        Four chapters (Chapters I, II, XIX and XX) use more than one letter in the first position of their codes.

        World Health Organization. (2010). International statistical classification of diseases and related health
        problems (10th revision, 6th ed., Vol. 2). World Health Organization.
        """
        graph = WHOICDGraph(files_dir=real_icd_file_dir)
        more_than_one = ["01", "02", "19", "20"]
        for chapter in graph.chapters():
            codes = graph.codes(from_chapter=chapter)
            letters = []
            for code in codes:
                letters.append(code[0])

            if chapter in more_than_one:
                assert len(set(letters)) > 1, (
                    f"Code {chapter} does not have than one letter in their chapter"
                )
            else:
                assert len(set(letters)) == 1, (
                    f"Code {chapter} have than one letter in their chapter"
                )

    @pytest.mark.integration
    def test_get_blocks(self, real_icd_file_dir):
        """
        The chapters are divided into blocks of three-character codes.

        World Health Organization. (2010). International statistical classification of diseases and related health
        problems (10th revision, 6th ed., Vol. 2). World Health Organization.
        """
        graph = WHOICDGraph(files_dir=real_icd_file_dir)

        code = graph.graph.nodes["A009"]
        assert code["block"] == "A00-A09"
        assert len(graph.blocks()) == 263


class TestGetGraph:
    def test_get_graph_by_name(self, icd_file_dir):
        graph = get_graph("icd-10-who", icd_file_dir)
        assert isinstance(graph, ICDGraph)
        assert isinstance(graph, WHOICDGraph)
        assert graph.version_name == "icd-10-who"
