import pytest

from oberbaum.icd_graph.graph import (CID10Graph, ICDGraph, WHOICDGraph,
                                      get_graph)


class TestGetGraph:
    @pytest.mark.parametrize(
        "version, expected_class, file_dir",
        [
            ("icd-10-who", WHOICDGraph, "icd10_who_file_dir"),
            ("cid-10-bra", CID10Graph, "cid10_bra_file_dir"),
        ],
    )
    def test_get_graph_by_name(self, version, expected_class, file_dir, request):
        file_dir = request.getfixturevalue(file_dir)
        graph = get_graph(version, file_dir)

        assert isinstance(graph, ICDGraph)
        assert isinstance(graph, expected_class)
        assert graph.version_name == version

    def test_graph_class_from_graph_file(self):
        graph = get_graph("cid-10-bra", gml_filepath="subgraph_B180_cid10.gml")
        assert isinstance(graph, CID10Graph)


class TestLoadGraphFromFile:
    def test_load_graph_from_file(self):
        graph = CID10Graph(gml_filepath="tests/fixtures/subgraph_B180_cid10.gml")

        assert graph.chapters()
        assert graph.blocks()
        assert graph.codes()
