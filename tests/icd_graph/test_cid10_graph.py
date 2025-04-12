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

        assert graph.blocks()

        code = graph.graph.nodes["A009"]
        assert code["block"] == "A00-A09"

    @pytest.mark.parametrize(
        "chapter,code,message",
        [
            ("1", "A01", "Different but close letters e.g. A00-B99"),
            ("3", "D89", "Same letters but different intervals e.g. D50-D89"),
            ("10", "J101", "Same letters, all intervals e.g. J09-J18"),
            ("20", "W010", "Different letters but within interval e.g. V01-Y98"),
            ("2", "C490", "Same letters but different intervals e.g. C00;D48"),
            ("20", "X850", "Different letters but within interval e.g. X85-Y09"),
            (None, "Y99", "Nonexistent chapter"),
        ],
    )
    def test_find_chapter(self, real_cid10_bra_file_dir, chapter, code, message):
        graph = CID10Graph(files_dir=real_cid10_bra_file_dir)

        assert graph.find_chapter(code) == chapter, message

    def test_codes(self, cid10_bra_file_dir):
        graph = CID10Graph(files_dir=cid10_bra_file_dir)
        expected = {"A009", "A00", "A00-A09", "A01", "A010", "A001", "A000"}
        codes = graph.codes(exclude_3_char=False)

        assert codes == expected

        expected = {"A009", "A001", "A010", "A000"}
        codes = graph.codes(exclude_3_char=True)

        assert codes == expected
