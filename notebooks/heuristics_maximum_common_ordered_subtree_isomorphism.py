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
    G = nx.parse_gml(Path("cid-10-bra.gml").read_text())
    G2 = nx.parse_gml(Path("icd-10-gm.gml").read_text())
    S = nx.parse_gml(Path("subgraph-icd-10-gm-A4151.gml").read_text())
    return G, G2, S


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

    return (get_leafs,)


@app.cell
def _(S, get_leafs):
    get_leafs(S)
    return


@app.cell
def _(G, get_leafs):
    G_leafs = get_leafs(G)
    G_leafs
    return (G_leafs,)


@app.cell
def _(G_leafs):
    G_leafs[10]
    return


@app.cell
def _(G, nx):
    nx.shortest_path(G, source="root", target="A415")
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
def _(G2, nx):
    # networkx.exception.NodeNotFound: Target A4151 is not in G
    # shortest_path = nx.shortest_path(G2, source='root', target='A4151')
    subgraph_descendants = nx.descendants(G2, "22")
    s = G2.subgraph(subgraph_descendants)
    nx.write_network_text(s)
    return (s,)


@app.cell
def _(G, run_mcosi, s):
    run_mcosi(G, s, print_results=True)  # G bra in S from G2 ger
    return


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
def _(G, nx):
    list(nx.tree_all_pairs_lowest_common_ancestor(G, "U818"))
    # https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.lowest_common_ancestors.tree_all_pairs_lowest_common_ancestor.html
    return


if __name__ == "__main__":
    app.run()
