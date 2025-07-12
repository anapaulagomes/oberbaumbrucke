import networkx as nx
import pytest

from oberbaum.cli import get_graph
from oberbaum.icd_graph.graph_overlap import ICDTreesComparator, compare_graphs


def print_results(result):
    print(f"Score: {result['score']}")
    print("Isomorphic Subtree 1:")
    nx.write_network_text(result["subtree1"])
    print("Isomorphic Subtree 2:")
    nx.write_network_text(result["subtree2"])


class TestGraphOverlap:
    def test_get_overlap(self):
        ger_graph = get_graph(
            "icd-10-gm",
            gml_filepath="tests/fixtures/subgraph-icd-10-gm-Z75-include-children.gml",
        )
        who_graph = get_graph(
            "icd-10-who",
            gml_filepath="tests/fixtures/subgraph-icd-10-who-Z75-include-children.gml",
        )

        graph_overlap = ICDTreesComparator(ger_graph, who_graph)
        result = graph_overlap.mcosi()

        print_results(result)

        assert result["score"] == 6  # perfect match

    def test_get_overlap_from_partial_matches(self):
        usa_graph = get_graph(
            "icd-10-cm",
            gml_filepath="tests/fixtures/subgraph-icd-10-cm-H938-include-children.gml",
        )
        who_graph = get_graph(
            "icd-10-who",
            gml_filepath="tests/fixtures/subgraph-icd-10-who-H93-include-children.gml",
        )

        graph_overlap = ICDTreesComparator(usa_graph, who_graph)
        result = graph_overlap.mcosi()

        print_results(result)

        assert result["score"] == 2
        assert list(result["subtree1"].nodes()) == ["H93", "H938"]
        assert list(result["subtree2"].nodes()) == ["H93", "H938"]

    def test_no_overlap(self):
        ger_graph = get_graph(
            "icd-10-gm",
            gml_filepath="tests/fixtures/subgraph-icd-10-gm-Z75-include-children.gml",
        )
        who_graph = get_graph(
            "icd-10-who",
            gml_filepath="tests/fixtures/subgraph-icd-10-who-H93-include-children.gml",
        )

        graph_overlap = ICDTreesComparator(ger_graph, who_graph)
        result = graph_overlap.mcosi()

        print_results(result)

        assert result["score"] == 0  # only root node is common


@pytest.mark.skip
class TestCompareGraphs:
    def test_compare_graphs(self):
        usa_graph = get_graph(
            "icd-10-cm",
            gml_filepath="tests/fixtures/subgraph-icd-10-cm-H938-include-children.gml",  # "icd-10-gm.gml"
        )
        who_graph = get_graph(
            "icd-10-who",
            gml_filepath="tests/fixtures/subgraph-icd-10-who-H93-include-children.gml",  # "icd-10-who.gml"
        )

        results = compare_graphs(usa_graph, who_graph)

        assert results["score"] == 6
        assert results["subtree1"]
        assert results["subtree2"]
