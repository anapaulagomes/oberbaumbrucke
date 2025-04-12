from oberbaum.icd_graph import CID10Graph


class TestCID10Graph:
    def test_create_cid10_graph(self, icd_file_dir):
        graph = CID10Graph(files_dir=icd_file_dir)
        assert graph.version_name == "cid-10-bra"

    def test_get_all_chapters(self, icd_file_dir):
        graph = CID10Graph(files_dir=icd_file_dir)
        chapters = graph.chapters()
        assert isinstance(chapters, list)
        assert len(chapters) == 5
