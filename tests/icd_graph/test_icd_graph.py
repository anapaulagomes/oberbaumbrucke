import pytest

from oberbaum.icd_graph import CID10Graph, ICDGraph, WHOICDGraph, get_graph


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
