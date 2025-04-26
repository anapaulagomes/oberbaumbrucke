from oberbaum.icd_graph.graphs.brazil import CID10Graph


class TestLoadGraphFromFile:
    def test_load_graph_from_file(self):
        graph = CID10Graph(gml_filepath="tests/fixtures/subgraph_B180_cid10.gml")

        assert graph.chapters()
        assert graph.blocks()
        assert graph.codes()
