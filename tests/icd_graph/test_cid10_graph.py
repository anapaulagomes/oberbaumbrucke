import pytest

from oberbaum.icd_graph import CID10Graph


class TestCID10Graph:
    def test_create_cid10_graph(self, cid10_bra_file_dir):
        graph = CID10Graph(files_dir=cid10_bra_file_dir)
        assert graph.version_name == "cid-10-bra"

    def test_get_all_chapters(self, cid10_bra_file_dir):
        graph = CID10Graph(files_dir=cid10_bra_file_dir)
        chapters = graph.chapters()
        assert isinstance(chapters, list)
        assert len(chapters) == 3

    def test_blocks(self, cid10_bra_file_dir):
        graph = CID10Graph(files_dir=cid10_bra_file_dir)

        assert "A00-A09" in graph.blocks()
        assert "A15-A19" in graph.blocks()
        assert "A20-A28" in graph.blocks()

        code = graph.graph.nodes["A009"]
        assert code["block"] == "A00-A09"

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "code,chapter,block,message",
        [
            ("A01", "1", "A00-A09", "Different but close letters e.g. A00-B99"),
            (
                "D89",
                "3",
                "D80-D89",
                "Same letters but different intervals e.g. D50-D89",
            ),
            ("J101", "10", "J09-J18", "Same letters, all intervals e.g. J09-J18"),
            (
                "W010",
                "20",
                "V01-X59",
                "Different letters but within interval e.g. V01-Y98",
            ),
            (
                "C490",
                "2",
                "C00-C97",
                "Same letters but different intervals e.g. C00;D48",
            ),
            (
                "X850",
                "20",
                "X85-Y09",
                "Different letters but within interval e.g. X85-Y09",
            ),
            ("Y99", None, None, "Nonexistent chapter"),
        ],
    )
    def test_find_chapter_and_block(
        self, real_cid10_bra_file_dir, code, chapter, block, message
    ):
        graph = CID10Graph(files_dir=real_cid10_bra_file_dir)
        found_chapter = graph.find_chapter(code)
        found_block = graph.find_block(code)

        assert found_chapter == chapter, message
        assert found_block == block, message

    def test_codes(self, cid10_bra_file_dir):
        graph = CID10Graph(files_dir=cid10_bra_file_dir)
        expected = {"A009", "A00", "A00-A09", "A01", "A010", "A001", "A000"}
        codes = graph.codes(exclude_3_char=False)

        assert codes == expected

        expected = {"A009", "A001", "A010", "A000"}
        codes = graph.codes(exclude_3_char=True)

        assert codes == expected

    @pytest.mark.integration
    def test_check_real_graph(self, real_cid10_bra_file_dir):
        graph = CID10Graph(files_dir=real_cid10_bra_file_dir)

        assert len(graph.chapters()) == 22
        assert len(graph.blocks()) == 275
        assert len(graph.three_char_codes()) == 1626
        assert len(graph.four_char_codes()) == 8859
        assert len(graph.categories()) == 14281  # both three and four char codes

    def test_handle_sublocks(self, tmp_path):
        blocks_file = tmp_path / "CID-10-GRUPOS.CSV"
        blocks_file.write_text(
            "CATINIC;CATFIM;DESCRICAO;DESCRABREV;\n"
            "T20;T32;Queimaduras e corrosões;Queimaduras e corrosões;\n"
            "T20;T25;Queimaduras e corrosões da superfície externa do corpo, especificadas por local;Queimad e corros superf ext corpo, espec p/local;\n"
            "T26;T28;Queimaduras e corrosões limitadas ao olho e aos órgãos internos;Queimad e corrosões limit olho e órgãos internos;\n"
            "T29;T32;Queimaduras e corrosões de múltiplas regiões e de regiões não especificadas do corpo;Queimad e corrosões múlt reg e reg não espec corpo;\n"
        )
        chapters_file = tmp_path / "CID-10-CAPITULOS.CSV"
        chapters_file.write_text(
            "NUMCAP;CATINIC;CATFIM;DESCRICAO;DESCRABREV;\n"
            "19;S00;T98;Capítulo XIX - Lesões, envenenamento e algumas outras conseqüências de causas externas;XIX. Lesões enven e alg out conseq causas externas;\n"
        )
        subcategories_file = tmp_path / "CID-10-SUBCATEGORIAS.CSV"
        subcategories_file.write_text(
            "SUBCAT;CLASSIF;RESTRSEXO;CAUSAOBITO;DESCRICAO;DESCRABREV;REFER;EXCLUIDOS;\n"
            "T200;;;;Queimadura da cabeça e do pescoço, grau não especificado;T20.0 Queim da cabeca e do pescoco grau NE;;;\n"
            "T201;;;N;Queimadura de primeiro grau da cabeça e do pescoço;T20.1 Queim de 1.grau da cabeca e pescoco;;;\n"
            "T210;;;;Queimadura do tronco, grau não especificado;T21.0 Queim do tronco grau NE;;;\n"
            "T211;;;N;Queimadura de primeiro grau do tronco;T21.1 Queim de 1.grau do tronco;;;\n"
        )
        graph = CID10Graph(files_dir=str(tmp_path))

        assert graph.graph.has_edge("T20-T32", "T20-T25")  # block and sub-blocks
        assert graph.graph.has_edge("T20-T32", "T26-T28")
        assert graph.graph.has_edge("T20-T32", "T29-T32")
        assert graph.graph.has_edge("19", "T20-T32")  # chapter and block
