import pytest

from oberbaum.icd_graph import ICDGraph, get_graph, WHOICDGraph, CID10Graph


class TestGetGraph:
    @pytest.mark.parametrize(
        "version, expected_class",
        [
            ("icd-10-who", WHOICDGraph),
            ("cid-10-bra", CID10Graph),
        ],
    )
    def test_get_graph_by_name(self, icd10_who_file_dir, version, expected_class):
        graph = get_graph(version, icd10_who_file_dir)
        assert isinstance(graph, ICDGraph)
        assert isinstance(graph, expected_class)
        assert graph.version_name == version
