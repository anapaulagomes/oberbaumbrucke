from dataclasses import dataclass

import networkx as nx
import networkx_algo_common_subtree

from oberbaum.icd_graph.graphs.base import ICDGraph


@dataclass
class ICDTreesComparator:
    graph1: ICDGraph
    graph2: ICDGraph

    def overlap(self, only_codes: bool = False):
        """Compare the two ICD trees using the maximum common ordered subtree isomorphism
        and return the overlap results."""
        node_affinity_func = (
            self.compare_nodes if not only_codes else self.compare_codes_only
        )
        subtree1, subtree2, score = (
            networkx_algo_common_subtree.maximum_common_ordered_subtree_isomorphism(
                self.graph1._graph,
                self.graph2._graph,
                node_affinity=node_affinity_func,  # TODO add node_affinity with a db call
            )
        )
        # see more about it here: https://github.com/Erotemic/networkx_algo_common_subtree/blob/409da0a6744d687b245b97b1e547848712e17215/networkx_algo_common_subtree/tree_isomorphism.py#L49

        # if only_codes:
        #     score = 0.0  # TODO calculate the score based on codes only

        return {"score": score, "subtree1": subtree1, "subtree2": subtree2}

    def compare_nodes(self, node1, node2):
        """
        Compare two nodes from ICD tree based on their attributes.

        Assume that the node1 and node2 belongs to graph1 and graph2 respectively.
        """
        # node1_version = self.graph1.version_name
        # node2_version = self.graph2.version_name
        # TODO make a db call to get the node affinity
        return self.graph1.get(node1).get("name") == self.graph2.get(node2).get("name")

    def compare_codes_only(self, node1, node2):
        """
        Compare two nodes from ICD tree based on their attributes.

        Assume that the node1 and node2 belongs to graph1 and graph2 respectively.
        """
        node1_graph1 = self.graph1.get(node1)
        node2_graph2 = self.graph2.get(node2)

        if all(
            [node1_graph1.get("type") == "code", node2_graph2.get("type") == "code"]
        ):
            return self.compare_nodes(node1, node2)

        return True


def compare_graphs(graph, another_graph, only_codes: bool = False):
    results = {}
    for chapter in range(1, 23):  # split by chapter due to memory constraints
        chapter_descendants = nx.descendants(another_graph, str(chapter))
        chapter_subgraph = another_graph._graph.subgraph(chapter_descendants)
        comparator = ICDTreesComparator(graph1=graph, graph2=chapter_subgraph)
        result = comparator.overlap(only_codes)
        results[chapter] = result

    # TODO reconstruct the subgraphs from the results
    return results
