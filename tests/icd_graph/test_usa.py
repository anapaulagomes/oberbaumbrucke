from pathlib import Path
from unittest.mock import Mock

import networkx as nx
import pytest

from oberbaum.icd_graph.graphs.usa import ICD10CMGraph


@pytest.mark.integration
class TestICD10CMGraph:
    def test_get_all_codes(self, real_icd10_cm_file_dir):
        graph = ICD10CMGraph(files_dir=real_icd10_cm_file_dir)
        blocks = graph.blocks()
        codes = list(graph.get_codes())

        assert len(graph.chapters()) == 22
        assert len(blocks) == 250
        assert len(list(codes)) == 36024
        assert "A00" not in blocks
        assert "A00" not in codes  # FIXME should be in categories
        assert "A15-A19" in blocks
        assert "A000" in codes
        assert "A001" in codes
        assert "A009" in codes
        assert "A000" in codes  # 4-char code
        assert "Z5181" in codes  # 5-char code
        assert "H938X9" in codes  # 6-char code
        assert "C441021" in codes  # 7-char code

    def test_levels(self, real_icd10_cm_file_dir):
        graph = ICD10CMGraph(files_dir=real_icd10_cm_file_dir)
        levels = graph.levels()

        expected_levels = {
            1: 22,
            2: 250,
            3: 1917,
            4: 10070,
            5: 14483,
            6: 19936,
            7: 92,  # it does not include the 7th char
        }

        assert levels == expected_levels

    def test_export_graph(self, real_icd10_cm_file_dir, monkeypatch):
        graph = ICD10CMGraph(files_dir=real_icd10_cm_file_dir)
        mock_write_gml = Mock()
        monkeypatch.setattr(nx, "write_gml", mock_write_gml)

        assert mock_write_gml.called is False

        exported_path = graph.export()

        assert mock_write_gml.called is True
        assert exported_path == "icd-10-cm.gml"

    def test_handle_loops(self, real_icd10_cm_file_dir):
        graph = ICD10CMGraph(files_dir=real_icd10_cm_file_dir)
        assert list(nx.nodes_with_selfloops(graph._graph)) == []

    def test_all_codes_needs_to_start_with_a_letter(self, real_icd10_cm_file_dir):
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
        Also in: https://icd.cm.int/browse10/2019/en
        """
        graph = ICD10CMGraph(files_dir=real_icd10_cm_file_dir)
        codes = graph.codes()
        for code in codes:
            assert code[0].isalpha(), f"Code {code} does not start with a letter"

    def test_more_than_one_letter_in_the_first_position(self, real_icd10_cm_file_dir):
        """
        Four chapters (Chapters I, II, XIX and XX) use more than one letter in the first position of their codes.

        World Health Organization. (2010). International statistical classification of diseases and related health
        problems (10th revision, 6th ed., Vol. 2). World Health Organization.
        """
        graph = ICD10CMGraph(files_dir=real_icd10_cm_file_dir)
        more_than_one = ["1", "2", "19", "20"]
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

    def test_get_blocks(self, real_icd10_cm_file_dir):
        """
        The chapters are divided into blocks of three-character codes.

        World Health Organization. (2010). International statistical classification of diseases and related health
        problems (10th revision, 6th ed., Vol. 2). World Health Organization.
        """
        graph = ICD10CMGraph(files_dir=real_icd10_cm_file_dir)
        blocks = graph.blocks()
        code = graph.get("A009")

        assert len(blocks) == 250
        assert code["block"] == "A00-A09"
        assert "A00-A09" in blocks

    def test_return_chapters_in_roman_numerals(self, real_icd10_cm_file_dir):
        graph = ICD10CMGraph(files_dir=real_icd10_cm_file_dir)
        chapters_in_roman = [
            "I",
            "II",
            "III",
            "IV",
            "V",
            "VI",
            "VII",
            "VIII",
            "IX",
            "X",
            "XI",
            "XII",
            "XIII",
            "XIV",
            "XV",
            "XVI",
            "XVII",
            "XVIII",
            "XIX",
            "XX",
            "XXI",
            "XXII",
        ]

        assert graph.chapters(roman_numerals=True) == chapters_in_roman

    def test_check_random_codes_and_edge_cases(self, real_icd10_cm_file_dir):
        graph = ICD10CMGraph(files_dir=real_icd10_cm_file_dir)

        assert graph.predecessors("A154") == ["A15", "A15-A19", "1"]
        assert graph.predecessors("B188") == ["B18", "B15-B19", "1"]
        assert graph.predecessors("C439") == ["C43", "C43-C44", "2"]
        assert graph.predecessors("D561") == ["D56", "D55-D59", "3"]
        assert graph.predecessors("E112") == ["E11", "E08-E13", "4"]
        assert graph.predecessors("E09321") == ["E0932", "E093", "E09", "E08-E13", "4"]
        assert graph.predecessors("F202") == ["F20", "F20-F29", "5"]
        assert graph.predecessors("G473") == ["G47", "G40-G47", "6"]
        assert graph.predecessors("G43A1") == ["G43A", "G43", "G40-G47", "6"]
        assert graph.predecessors("G9001") == ["G900", "G90", "G89-G99", "6"]
        assert graph.predecessors("H251") == ["H25", "H25-H28", "7"]
        assert graph.predecessors("H442D2") == ["H442D", "H442", "H44", "H43-H44", "7"]
        assert graph.predecessors("H810") == ["H81", "H80-H83", "8"]
        assert graph.predecessors("I252") == ["I25", "I20-I25", "9"]
        assert graph.predecessors("J459") == ["J45", "J40-J4A", "10"]
        assert graph.predecessors("J45901") == ["J4590", "J459", "J45", "J40-J4A", "10"]
        assert graph.predecessors("K704") == ["K70", "K70-K77", "11"]
        assert graph.predecessors("L408") == ["L40", "L40-L45", "12"]
        assert graph.predecessors("M320") == ["M32", "M30-M36", "13"]
        assert graph.predecessors("N185") == ["N18", "N17-N19", "14"]
        assert graph.predecessors("O141") == ["O14", "O10-O16", "15"]
        assert graph.predecessors("P220") == ["P22", "P19-P29", "16"]
        assert graph.predecessors("Q242") == ["Q24", "Q20-Q28", "17"]
        assert graph.predecessors("R579") == ["R57", "R50-R69", "18"]
        assert graph.predecessors("S065") == ["S06", "S00-S09", "19"]
        assert graph.predecessors("T201") == ["T20", "T20-T25", "19"]


class TestCompareCodes:
    @pytest.fixture(scope="class")
    def icd10cm_codes_from_csv(self):
        codes_only = Path(
            "data/Code-desciptions-April-2025/icd10cm-order-April-2025.txt"
        )
        codes_only = {
            line[6:13].strip(): True for line in codes_only.read_text().splitlines()
        }
        return codes_only

    @pytest.fixture(scope="class")
    def graph(self, real_icd10_cm_file_dir):
        return ICD10CMGraph(files_dir=real_icd10_cm_file_dir)

    def test_all_nodes_from_the_graph_can_be_found_in_the_csv(
        self, request, graph, icd10cm_codes_from_csv
    ):
        found = 0
        not_found = []
        for code in graph.get_codes():
            if icd10cm_codes_from_csv.get(code):
                found += 1
            else:
                not_found.append(code)
        request.node._output = "</br>".join(not_found)
        assert not_found == []
