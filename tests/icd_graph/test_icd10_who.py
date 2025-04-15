from unittest.mock import Mock

import networkx as nx
import pytest

from oberbaum.icd_graph import WHOICDGraph


class TestWHOICD10Graph:
    def test_create_who_icd10_graph(self, icd10_who_file_dir):
        graph = WHOICDGraph(files_dir=icd10_who_file_dir)
        assert graph.version_name == "icd-10-who"
        assert isinstance(graph.graph, nx.DiGraph)

    def test_get_all_chapters(self, icd10_who_file_dir):
        graph = WHOICDGraph(files_dir=icd10_who_file_dir)
        chapters = graph.chapters()
        assert isinstance(chapters, list)
        assert len(chapters) == 5

    def test_add_codes(self, icd10_who_file_dir):
        graph = WHOICDGraph(files_dir=icd10_who_file_dir)

        assert graph.graph.has_node("A00")
        assert graph.graph.has_node("A000")
        assert graph.graph.has_node("A001")
        assert graph.graph.has_edge("01", "A00-A09")  # chapter - block
        assert graph.graph.has_edge("A00-A09", "A00")  # block - 3-char
        assert graph.graph.has_edge("A00", "A000")  # 3-char - 4-char
        assert graph.graph.has_edge("A00", "A001")  # 3-char - 4-char
        assert graph.graph.has_edge("A00", "A009")  # 3-char - 4-char

    def test_get_codes(self, icd10_who_file_dir):
        graph = WHOICDGraph(files_dir=icd10_who_file_dir)
        codes = graph.codes()

        assert isinstance(codes, set)
        assert len(codes) == 4
        assert "A00" not in codes  # 3-char code # TODO define if this is correct
        assert "A15-A19" in codes  # block
        assert "A000" in codes
        assert "A001" in codes
        assert "A009" in codes

    def test_get_codes_including_3_char(self, icd10_who_file_dir):
        graph = WHOICDGraph(files_dir=icd10_who_file_dir)
        codes = graph.codes(exclude_3_char=False)

        assert isinstance(codes, set)
        assert len(codes) == 6
        assert "A00" in codes  # 3-char code
        assert "A000" in codes
        assert "A001" in codes

    def test_levels(self, icd10_who_file_dir):
        graph = WHOICDGraph(files_dir=icd10_who_file_dir)
        levels = graph.levels()
        expected_levels = {1: 5, 2: 2, 3: 1, 4: 3}

        assert levels == expected_levels

    def test_blocks(self, icd10_who_file_dir):
        graph = WHOICDGraph(files_dir=icd10_who_file_dir)
        blocks = graph.blocks()

        code = graph.graph.nodes["A009"]
        assert code["block"] == "A00-A09"
        assert "A00-A09" in blocks

    def test_codes_per_level(self, icd10_who_file_dir):
        graph = WHOICDGraph(files_dir=icd10_who_file_dir)
        codes_per_level = graph.codes_per_level()

        expected = {
            1: ["01", "02", "03", "04", "05"],
            2: ["A00-A09", "A15-A19"],
            3: ["A00"],
            4: ["A000", "A001", "A009"],
        }

        assert codes_per_level == expected

    def test_three_char_codes(self, icd10_who_file_dir):
        graph = WHOICDGraph(files_dir=icd10_who_file_dir)
        three_char_codes = graph.three_char_codes()

        assert three_char_codes == ["A00"]

    def test_four_char_codes(self, icd10_who_file_dir):
        graph = WHOICDGraph(files_dir=icd10_who_file_dir)
        three_char_codes = graph.four_char_codes()

        assert three_char_codes == ["A000", "A001", "A009"]

    def test_export_graph(self, icd10_who_file_dir, monkeypatch):
        graph = WHOICDGraph(files_dir=icd10_who_file_dir)
        mock_write_gml = Mock()
        monkeypatch.setattr(nx, "write_gml", mock_write_gml)

        assert mock_write_gml.called is False

        exported_path = graph.export()

        assert mock_write_gml.called is True
        assert exported_path == "icd-10-who.gml"

    @pytest.mark.integration
    def test_handle_loops(self, real_icd10_who_file_dir):
        graph = WHOICDGraph(files_dir=real_icd10_who_file_dir)
        assert list(nx.nodes_with_selfloops(graph.graph)) == []

    @pytest.mark.integration
    def test_all_codes_needs_to_start_with_a_letter(self, real_icd10_who_file_dir):
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
        graph = WHOICDGraph(files_dir=real_icd10_who_file_dir)
        codes = graph.codes()
        for code in codes:
            assert code[0].isalpha(), f"Code {code} does not start with a letter"

    @pytest.mark.integration
    def test_more_than_one_letter_in_the_first_position(self, real_icd10_who_file_dir):
        """
        Four chapters (Chapters I, II, XIX and XX) use more than one letter in the first position of their codes.

        World Health Organization. (2010). International statistical classification of diseases and related health
        problems (10th revision, 6th ed., Vol. 2). World Health Organization.
        """
        graph = WHOICDGraph(files_dir=real_icd10_who_file_dir)
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
    def test_get_blocks(self, real_icd10_who_file_dir):
        """
        The chapters are divided into blocks of three-character codes.

        World Health Organization. (2010). International statistical classification of diseases and related health
        problems (10th revision, 6th ed., Vol. 2). World Health Organization.
        """
        graph = WHOICDGraph(files_dir=real_icd10_who_file_dir)

        code = graph.graph.nodes["A009"]
        assert code["block"] == "A00-A09"
        assert len(graph.blocks()) == 263

    @pytest.mark.integration
    def test_levels_with_real_file(self, real_icd10_who_file_dir):
        graph = WHOICDGraph(files_dir=real_icd10_who_file_dir)
        levels = graph.levels()
        expected_levels = {1: 22, 2: 263, 3: 2050, 4: 10171}

        assert levels == expected_levels

    @pytest.mark.skip(reason="Bigger block not found in the code data")
    @pytest.mark.integration
    def test_support_sub_blocks(self, real_icd10_who_file_dir):
        # XX > Y40-Y84 > Y40-Y59 > Y40 > Y40.0
        graph = WHOICDGraph(files_dir=real_icd10_who_file_dir)
        blocks = graph.blocks()
        codes = graph.codes(exclude_3_char=False)

        assert "Y40-Y84" in blocks  # not supported
        assert "Y40-Y59" in blocks
        assert "Y40" in codes
        assert "Y400" in codes

    def test_return_chapters_in_roman_numerals(self, real_icd10_who_file_dir):
        graph = WHOICDGraph(files_dir=real_icd10_who_file_dir)
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

    @pytest.mark.integration
    def test_check_real_graph(self, real_icd10_who_file_dir):
        graph = WHOICDGraph(files_dir=real_icd10_who_file_dir)

        assert len(graph.chapters()) == 22
        assert len(graph.blocks()) == 263
        assert len(graph.three_char_codes()) == 2050
        assert len(graph.four_char_codes()) == 10171

        assert graph.predecessors("A152") == ["A15", "A15-A19", "01"]
        assert graph.predecessors("C439") == ["C43", "C43-C44", "02"]
        assert graph.predecessors("D561") == ["D56", "D55-D59", "03"]
        assert graph.predecessors("E112") == ["E11", "E10-E14", "04"]
        assert graph.predecessors("F202") == ["F20", "F20-F29", "05"]
        assert graph.predecessors("G473") == ["G47", "G40-G47", "06"]
        assert graph.predecessors("H251") == ["H25", "H25-H28", "07"]
        assert graph.predecessors("H810") == ["H81", "H80-H83", "08"]
        assert graph.predecessors("I252") == ["I25", "I20-I25", "09"]
        assert graph.predecessors("J459") == ["J45", "J40-J47", "10"]
        assert graph.predecessors("K704") == ["K70", "K70-K77", "11"]
        assert graph.predecessors("L408") == ["L40", "L40-L45", "12"]
        assert graph.predecessors("M320") == ["M32", "M30-M36", "13"]
        assert graph.predecessors("N185") == ["N18", "N17-N19", "14"]
        assert graph.predecessors("O141") == ["O14", "O10-O16", "15"]
        assert graph.predecessors("P220") == ["P22", "P20-P29", "16"]
        assert graph.predecessors("Q242") == ["Q24", "Q20-Q28", "17"]
        assert graph.predecessors("R572") == ["R57", "R50-R69", "18"]
        assert graph.predecessors("S065") == ["S06", "S00-S09", "19"]
        assert graph.predecessors("T201") == ["T20", "T20-T25", "19"]
