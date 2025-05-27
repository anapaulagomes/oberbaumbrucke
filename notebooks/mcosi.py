from pathlib import Path

import networkx as nx
import networkx_algo_common_subtree

G1_filepath = "icd-10-who.gml"
G2_filepath = "cid-10-bra.gml"

print(f"{G1_filepath} vs {G2_filepath}")

G1 = nx.parse_gml(Path(G1_filepath).read_text())
G2 = nx.parse_gml(Path(G2_filepath).read_text())

print(f"Graph 1: {len(G1.nodes)} nodes, {len(G1.edges)} edges")
print(f"Graph 2: {len(G2.nodes)} nodes, {len(G2.edges)} edges\n\n")

subtree1, subtree2, score = (
    networkx_algo_common_subtree.maximum_common_ordered_subtree_isomorphism(G1, G2)
)
print(f"{score=}")
print(f"Isomorphic Subtree 1: {len(subtree1.nodes)} nodes, {len(subtree1.edges)} edges")
nx.write_network_text(subtree1, path=Path(f"mcosi_{G1_filepath}.txt"))
print(f"Isomorphic Subtree 2: {len(subtree2.nodes)} nodes, {len(subtree2.edges)} edges")
nx.write_network_text(subtree2, path=Path(f"mcosi_{G2_filepath}.txt"))
