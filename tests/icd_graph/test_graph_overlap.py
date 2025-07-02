import networkx as nx

from oberbaum.cli import get_graph
from oberbaum.icd_graph.graph_overlap import ICDTreesComparator


def print_results(result):
    print(f"Score: {result['score']}")
    print("Isomorphic Subtree 1:")
    nx.write_network_text(result["subtree1"])
    print("Isomorphic Subtree 2:")
    nx.write_network_text(result["subtree2"])


class TestGraphOverlap:
    def test_get_overlap(self):
        who_graph = get_graph(
            "icd-10-who", gml_filepath="subgraph-icd-10-who-Z75-include-children.gml"
        )
        ger_graph = get_graph(
            "icd-10-gm", gml_filepath="subgraph-icd-10-gm-Z75-include-children.gml"
        )

        graph_overlap = ICDTreesComparator(who_graph, ger_graph)
        result = graph_overlap.overlap()

        print_results(result)

        assert result["score"] == 7  # perfect match

    def test_get_overlap_from_partial_matches(self):
        who_graph = get_graph(
            "icd-10-who", gml_filepath="subgraph-icd-10-who-H93-include-children.gml"
        )
        usa_graph = get_graph(
            "icd-10-cm", gml_filepath="subgraph-icd-10-cm-H938-include-children.gml"
        )

        graph_overlap = ICDTreesComparator(who_graph, usa_graph)
        result = graph_overlap.overlap()

        print_results(result)

        assert result["score"] == 2
        assert result["subtree1"].nodes() == ["root", "8"]
        assert result["subtree2"].nodes() == ["root", "8"]

    def test_get_overlap_only_from_codes(self):
        who_graph = get_graph(
            "icd-10-who", gml_filepath="subgraph-icd-10-who-H93-include-children.gml"
        )
        usa_graph = get_graph(
            "icd-10-cm", gml_filepath="subgraph-icd-10-cm-H938-include-children.gml"
        )

        graph_overlap = ICDTreesComparator(who_graph, usa_graph)
        result = graph_overlap.overlap(only_codes=True)

        print_results(result)

        assert (
            result["score"] == 1
        )  # FIXME currently it is 5, but it should be 1 because only codes are compared
        assert result["subtree1"].nodes() == [
            "H93"
        ]  # not "H938" because in one it is a leaf and in the other it is a parent
        assert result["subtree2"].nodes() == ["H93"]

    def test_no_overlap(self):
        who_graph = get_graph(
            "icd-10-who", gml_filepath="subgraph-icd-10-who-H93-include-children.gml"
        )
        ger_graph = get_graph(
            "icd-10-gm", gml_filepath="subgraph-icd-10-gm-Z75-include-children.gml"
        )

        graph_overlap = ICDTreesComparator(who_graph, ger_graph)
        result = graph_overlap.overlap()

        print_results(result)

        assert result["score"] == 1  # only root node is common
