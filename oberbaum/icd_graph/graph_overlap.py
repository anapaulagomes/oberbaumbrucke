from dataclasses import dataclass

import networkx as nx
import networkx_algo_common_subtree

from oberbaum.icd_graph.embeddings import fetch_matches
from oberbaum.icd_graph.graphs.base import ICDGraph


@dataclass
class ICDTreesComparator:
    graph1: ICDGraph
    graph2: ICDGraph
    model: str = "jinaai/jina-embeddings-v3"

    def overlap(self):
        """Compare the two ICD trees using the maximum common ordered subtree isomorphism
        and return the overlap results."""
        subtree1, subtree2, score = (
            networkx_algo_common_subtree.maximum_common_ordered_subtree_isomorphism(
                self.graph1._graph,
                self.graph2._graph,
                node_affinity=self.compare_nodes,
            )
        )
        # see more about it here: https://github.com/Erotemic/networkx_algo_common_subtree/blob/409da0a6744d687b245b97b1e547848712e17215/networkx_algo_common_subtree/tree_isomorphism.py#L49

        return {"score": score, "subtree1": subtree1, "subtree2": subtree2}

    def compare_nodes(self, node1, node2):
        """
        Compare two nodes from ICD tree based on their attributes.

        Assume that the node1 and node2 belongs to graph1 and graph2 respectively.
        """
        node1_version = self.graph1.version_name
        node2_version = self.graph2.version_name
        result = fetch_matches(node1_version, node2_version, node1, node2, self.model)
        if not result:
            return False

        return result[0] != "not_found"  # match type


def compare_graphs(graph, another_graph):
    results = {}
    for chapter in range(1, 23):  # split by chapter due to memory constraints
        chapter_descendants = nx.descendants(another_graph, str(chapter))
        chapter_subgraph = another_graph._graph.subgraph(chapter_descendants)
        comparator = ICDTreesComparator(graph1=graph, graph2=chapter_subgraph)
        result = comparator.overlap()
        results[chapter] = result

    # TODO reconstruct the subgraphs from the results
    return results
