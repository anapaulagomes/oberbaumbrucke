from oberbaum.icd_graph.graphs.brazil import CID10Graph
from oberbaum.icd_graph.graphs.who import WHOICDGraph


class TestLoadGraphFromFile:
    def test_load_graph_from_file(self):
        graph = CID10Graph(gml_filepath="tests/fixtures/subgraph_B180_cid10.gml")

        assert graph.chapters()
        assert graph.blocks()
        assert graph.codes()

    def test_is_code(self, real_icd10_who_file_dir):
        graph = WHOICDGraph(files_dir=real_icd10_who_file_dir)

        assert graph.is_code("1") is False
        assert graph.is_code("A92-A99") is False
        assert graph.is_code("A92") is False
        assert graph.is_code("A") is False
        assert graph.is_code("J10") is False
        assert graph.is_code("A929") is True
