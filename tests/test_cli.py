import pytest

from oberbaum.cli import get_graph
from oberbaum.icd_graph.graphs.base import ICDGraph
from oberbaum.icd_graph.graphs.brazil import CID10Graph2008
from oberbaum.icd_graph.graphs.germany import ICD10GMGraph
from oberbaum.icd_graph.graphs.who import WHOICDGraph


class TestGetGraph:
    @pytest.mark.parametrize(
        "version, expected_class, file_dir",
        [
            ("icd-10-who", WHOICDGraph, "icd10_who_file_dir"),
            ("cid-10-bra-2008", CID10Graph2008, "cid10_bra_2018_file_dir"),
            ("icd-10-gm", ICD10GMGraph, "icd10_gm_file_dir"),
        ],
    )
    def test_get_graph_by_name(self, version, expected_class, file_dir, request):
        file_dir = request.getfixturevalue(file_dir)
        graph = get_graph(version, file_dir)

        assert isinstance(graph, ICDGraph)
        assert isinstance(graph, expected_class)
        assert graph.version_name == version

    def test_graph_class_from_graph_file(self):
        graph = get_graph(
            "cid-10-bra", gml_filepath="tests/fixtures/subgraph_B180_cid10.gml"
        )
        assert isinstance(graph, CID10Graph2008)
