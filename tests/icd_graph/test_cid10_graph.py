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

    def test_find_chapter(self, cid10_bra_file_dir):
        # TODO move test to the right place
        graph = CID10Graph(files_dir=cid10_bra_file_dir)

        assert graph.find_chapter("A00") == "1"
        assert graph.find_chapter("A009") == "1"
        assert graph.find_chapter("XXXX") is None

    def test_codes(self, cid10_bra_file_dir):
        graph = CID10Graph(files_dir=cid10_bra_file_dir)
        expected = {"A009", "A00", "A00-A09", "A01", "A010", "A001", "A000"}
        codes = graph.codes(exclude_3_char=False)

        assert codes == expected

        expected = {"A009", "A001", "A010", "A000"}
        codes = graph.codes(exclude_3_char=True)

        assert codes == expected
