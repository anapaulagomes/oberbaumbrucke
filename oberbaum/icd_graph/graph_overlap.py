import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import networkx as nx
import networkx_algo_common_subtree
import polars as pl

from oberbaum.icd_graph.embeddings import fetch_all_matches
from oberbaum.icd_graph.graphs.base import ICDGraph


@dataclass
class ICDTreesComparator:
    graph1: ICDGraph
    graph2: ICDGraph
    model: str = "jinaai/jina-embeddings-v3"

    def __post_init__(self):
        self.df = fetch_all_matches(
            self.graph1.version_name, self.graph2.version_name, self.model
        )

    def overlap(self, subgraph: nx.DiGraph = None):
        """Compare the two ICD trees using the maximum common ordered subtree isomorphism
        and return the overlap results."""
        subtree1, subtree2, score = (
            networkx_algo_common_subtree.maximum_common_ordered_subtree_isomorphism(
                self.graph1._graph,
                subgraph or self.graph2._graph,
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
        result = self.df.filter(
            pl.col("from_icd_code") == node1, pl.col("to_icd_code") == node2
        )

        if result.is_empty():
            return False

        result = result.to_dicts()[0]
        return result["match_type"] and result["match_type"] != "not_found"


def compare_graphs(graph: ICDGraph, another_graph: ICDGraph):
    results = {
        "from": graph.version_name,
        "to": another_graph.version_name,
        "score": 0.0,
    }
    comparator = ICDTreesComparator(graph1=graph, graph2=another_graph)
    # description = f"Checking overlap of {graph.version_name} with {another_graph.version_name} by chapter..."
    # split by chapter due to memory constraints
    for chapter in range(1, 23):
        print(chapter)
        chapter_descendants = nx.descendants(another_graph._graph, str(chapter))
        chapter_subgraph = another_graph._graph.subgraph(chapter_descendants)
        result = comparator.overlap(chapter_subgraph)
        results[chapter] = {
            "score": result["score"],
            "nodes_subtree1": list(result["subtree1"].nodes()),
            "nodes_subtree2": list(result["subtree2"].nodes()),
        }
        results["score"] += result["score"]

    filename = f"overlap-results-{graph.version_name}-{another_graph.version_name}-{datetime.now().strftime('%d%m%Y%H%M%S')}.json"
    Path(filename).write_text(json.dumps(results))

    # TODO reconstruct the subgraphs from the results
    return results
