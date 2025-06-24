

import marimo

__generated_with = "0.13.0"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import networkx as nx
    import networkx_algo_common_subtree

    return Path, networkx_algo_common_subtree, nx


@app.cell
def _(Path, nx):
    G = nx.parse_gml(Path("icd-10-gm.gml").read_text())
    G2 = nx.parse_gml(Path("icd-10-who.gml").read_text())
    return G, G2


@app.cell
def _():
    def is_code(node):
        return "-" not in node and len(node) >= 3 and len(node) <= 7

    def get_leafs(graph):
        return [
            x
            for x in graph.nodes()
            if is_code(x) and graph.out_degree(x) == 0 and graph.in_degree(x) == 1
        ]

    return


@app.cell
def _(networkx_algo_common_subtree, nx):
    def run_mcosi(G1, G2, print_results=True):
        subtree1, subtree2, score = (
            networkx_algo_common_subtree.maximum_common_ordered_subtree_isomorphism(
                G1, G2
            )
        )

        if print_results:
            print(f"{score=}")
            print("Isomorphic Subtree 1:")
            nx.write_network_text(subtree1)
            print("Isomorphic Subtree 2:")
            nx.write_network_text(subtree2)
        return {"score": score, "subtree1": subtree1, "subtree2": subtree2}

    return (run_mcosi,)


@app.cell
def _(G, G2, nx, run_mcosi):
    results = {}
    for chapter in range(1, 23):
        _subgraph_descendants = nx.descendants(G2, str(chapter))
        result = run_mcosi(G, G2.subgraph(_subgraph_descendants))
        results[chapter] = result
    return (results,)


@app.cell
def _(G2, nx, results):
    for _chapter, _result in results.items():
        print(_chapter, len(nx.descendants(G2, str(_chapter))), _result["score"])

    return


@app.cell
def _(nx, results):
    in_common = nx.DiGraph()
    root = "root"
    in_common.add_node(root)

    for _chapter, _result in results.items():
        in_common.add_edge(root, _chapter)
        assert len(_result["subtree1"].nodes()) == len(_result["subtree2"].nodes())
        current_graph = _result["subtree1"]
        first_level_nodes = [
            n for n in current_graph.nodes if current_graph.in_degree(n) == 0
        ]
        for first_level_node in first_level_nodes:
            in_common.add_edge(_chapter, first_level_node)
        in_common.update(current_graph)

    return (in_common,)


@app.cell
def _(G, G2, in_common, nx):
    nx.set_node_attributes(G, "bra", name="version")
    nx.set_node_attributes(G2, "ger", name="version")
    nx.set_node_attributes(in_common, "in_common", name="version")
    return


@app.cell
def _(G, G2, in_common, nx):
    # merge graphs
    M = nx.compose(in_common, G)
    M = nx.compose(M, G2)
    len(M.nodes())
    return (M,)


@app.cell
def _(M, nx):
    nx.write_gml(M, "merged-icd-10-who-ger-in-common.gml")
    return


@app.cell
def _(in_common, nx):
    nx.write_gml(in_common, "in_common_who-ger.gml")
    return


@app.cell
def _():
    # list(nx.tree_all_pairs_lowest_common_ancestor(G, "U818"))
    # https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.lowest_common_ancestors.tree_all_pairs_lowest_common_ancestor.html
    return


if __name__ == "__main__":
    app.run()
