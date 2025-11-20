import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import networkx as nx
import networkx_algo_common_subtree
import polars as pl
from networkx.algorithms.similarity import graph_edit_distance

from oberbaum.config import get_results_dir
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

    def mcosi(self, subgraph: nx.DiGraph = None):
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

    def edit_distance_similarity(self, current_chapter: int = None):
        """
        Compare the two ICD trees using tree edit distance.
        Returns the edit distance and a normalized similarity score (1 - normalized edit distance).
        Uses self.compare_nodes to determine node equality.
        """
        kwargs = {}
        if current_chapter:
            kwargs["roots"] = (str(current_chapter), str(current_chapter))
        edit_dist = graph_edit_distance(
            self.graph1._graph,
            self.graph2._graph,
            node_match=self.compare_nodes,
            timeout=30,
            **kwargs,
        )

        # Normalize similarity: 1 - (edit_dist / max(|V1|, |V2|))
        max_nodes = max(
            self.graph1._graph.number_of_nodes(), self.graph2._graph.number_of_nodes()
        )
        similarity = 1 - (edit_dist / max_nodes) if max_nodes > 0 else 0.0
        return {"edit_distance": edit_dist, "similarity": similarity}

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


def compare_graphs(
    graph: ICDGraph,
    another_graph: ICDGraph,
    method: str = "mcosi",
    target_chapter: int = None,
):
    results = {
        "from": graph.version_name,
        "to": another_graph.version_name,
        "score": 0.0,
    }
    description = f"Checking overlap of {graph.version_name} with {another_graph.version_name} by chapter..."
    print(description, flush=True)
    comparator = ICDTreesComparator(graph1=graph, graph2=another_graph)
    print(f"Method: {method}", flush=True)
    # split by chapter due to memory constraints
    for chapter in range(1, 23):
        if target_chapter and target_chapter != chapter:
            continue
        print(chapter, flush=True)
        chapter_descendants = nx.descendants(another_graph._graph, str(chapter))
        chapter_subgraph = another_graph._graph.subgraph(chapter_descendants)
        match method:
            case "edit_distance_similarity":
                results.update(comparator.edit_distance_similarity(chapter))
            case "mcosi":
                result = comparator.mcosi(chapter_subgraph)
                results.update(
                    {
                        "score": result["score"],
                        "nodes_subtree1": list(result["subtree1"].nodes()),
                        "nodes_subtree2": list(result["subtree2"].nodes()),
                    }
                )

    results_dir = get_results_dir(subfolder="overlap")
    now = datetime.now().strftime("%d%m%Y%H%M%S")
    filename = f"{results_dir}/overlap-results-{graph.version_name}-{another_graph.version_name}-{target_chapter or 'all-chapters'}-{now}.json"
    print(f"Exporting results to: {filename}", flush=True)
    Path(filename).write_text(json.dumps(results))

    # TODO reconstruct the subgraphs from the results
    return results


def merge_graphs(from_graph, to_graph, overlapped_nodes):
    G1 = from_graph._graph
    G2 = to_graph._graph
    from_name = from_graph.version_name
    to_name = to_graph.version_name
    G_result = nx.compose(G1, G2)

    attrs = {}
    # consider all chapters as overlapped nodes
    # given that this is not changed, and they were split
    # during the job parallelization
    for chapter in range(1, 23):
        attrs[str(chapter)] = {
            "overlap": True,
            "from": from_name,
            "to": to_name,
        }
    for node in overlapped_nodes:
        if node == "root":
            continue
        attrs[node] = {
            "overlap": True,
            "from": from_name,
            "to": to_name,
            # "from_info": G1.nodes[node],
            # "to_info": G2.nodes[node]
        }
    nx.set_node_attributes(G_result, attrs)
    return G_result
