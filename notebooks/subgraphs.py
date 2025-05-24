import marimo

__generated_with = "0.13.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import itertools

    import marimo as mo
    import networkx as nx
    import plotly.graph_objects as go
    from grandiso import find_motifs, find_motifs_iter
    from networkx.algorithms.isomorphism import DiGraphMatcher
    from plotly.subplots import make_subplots

    return (
        DiGraphMatcher,
        find_motifs,
        find_motifs_iter,
        go,
        itertools,
        make_subplots,
        mo,
        nx,
    )


@app.cell
def _(mo):
    mo.md(
        r"""
        # ICD-10 versions

        ## Visualize the ICD-10 trees for specific codes
        """
    )
    return


@app.cell
def _(mo):
    upload = mo.ui.file(filetypes=[".gml"], multiple=True)
    upload
    return (upload,)


@app.function
# expected: subgraph-icd-10-who-S361-include-children.gml
# expected: subgraph-icd-10-who-S361.gml

def get_version_target_node(filename):
    filename = (
        filename.replace("subgraph-", "")
        .replace("-include-children.gml", "")
        .replace(".gml", "")
    )
    version, target_node = filename.rsplit("-", 1)
    return version, target_node


@app.cell
def _(nx):
    def parse_gml(content):
        content_str = content.decode("utf-8")
        G = nx.parse_gml(content_str)
        return nx.DiGraph(G) if not isinstance(G, nx.DiGraph) else G

    def get_trees_from(upload):
        trees = {}
        target_node = None
        for index, gml_file in enumerate(upload.value):
            version = upload.name(index)
            version, target_node = get_version_target_node(upload.name(index))
            content = upload.value[index].contents
            trees[version] = parse_gml(content)
        return trees, target_node

    return (get_trees_from,)


@app.function
def get_hierarchical_pos(G):
    prog = "dot"
    try:
        from networkx.drawing.nx_agraph import graphviz_layout

        return graphviz_layout(G, prog=prog)
    except ImportError:
        try:
            from networkx.drawing.nx_pydot import graphviz_layout

            return graphviz_layout(G, prog=prog)
        except ImportError:
            raise ImportError("You need to install pygraphviz or pydot and Graphviz")


@app.cell
def _(go, make_subplots):
    def plot_trees(trees, target_node):
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=list(trees.keys()),
            horizontal_spacing=0.05,
            vertical_spacing=0.1,
        )

        for i, (name, G) in enumerate(trees.items()):
            if G is None:
                continue
            try:
                pos = get_hierarchical_pos(G)
            except Exception as e:
                print(f"Error computing layout for Tree {i + 1}: {e}")
                continue

            edge_x, edge_y = [], []
            for u, v in G.edges():
                x0, y0 = pos[u]
                x1, y1 = pos[v]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

            node_x = [pos[n][0] for n in G.nodes()]
            node_y = [pos[n][1] for n in G.nodes()]

            fig.add_trace(
                go.Scatter(
                    x=edge_x,
                    y=edge_y,
                    mode="lines",
                    line=dict(color="gray"),
                    showlegend=False,
                ),
                row=i // 2 + 1,
                col=i % 2 + 1,
            )

            fig.add_trace(
                go.Scatter(
                    x=node_x,
                    y=node_y,
                    mode="markers+text",
                    text=[
                        f"{n} - {data.get('description', '')}"
                        for n, data in G.nodes(data=True)
                    ],
                    marker=dict(color="blue", size=10),
                    textposition="top center",
                    showlegend=False,
                ),
                row=i // 2 + 1,
                col=i % 2 + 1,
            )

        fig.update_layout(
            height=700,
            width=1400,
            margin=dict(l=20, r=20, t=100, b=40),
            title_text="ICD-10 versions",
        )
        fig.update_xaxes(showticklabels=False).update_yaxes(showticklabels=False)
        return fig

    return (plot_trees,)


@app.cell
def _(get_trees_from, plot_trees, upload):
    trees, target_node = get_trees_from(upload)

    plot_trees(trees, target_node)
    return (trees,)


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Matching Strategy

        According to the rules of the WHO<a name="cite_ref-1"></a>[<sup>[1]</sup>](#cite_note-1), the modified ICD should keep categories and subcategories of 3 and 4 characheters un-changed.
        However, this is not respected and the countries are doing as they please. This is why the ICD-10 codes are not matching between different versions in these levels.

        Our matching strategy should cover:

        1. **Structural matching**: the nodes should be in the same place in the tree
        2. **Code matching**: the nodes should have the same code (label)
        3. **Semantic matching**: the nodes should have similar descriptions or meanings (some times the codes are not changed but the description is)

        <a name="cite_note-1"></a>1. [Jetté, N., Quan, H., Hemmelgarn, B., Drosler, S., Maass, C., Moskal, L., Paoin, W., Sundararajan, V., Gao, S., Jakob, R., Üstün, B., Ghali, W. A., & Investigators,  for the I. (2010). The Development, Evolution, and Modifications of ICD-10: Challenges to the International Comparability of Morbidity Data. Medical Care, 48(12), 1105. https://doi.org/10.1097/MLR.0b013e3181ef9d3e](#cite_ref-1)

        """
    )
    return


@app.cell
def _(trees):
    bra = trees["cid-10-bra"]
    who = trees["icd-10-who"]
    ger = trees["icd-10-gm"]
    usa = trees["icd-10-cm"]
    return bra, ger, usa, who


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Monomorphism and Isomorphism

        Insights:

        * G1 (first graph) should be the bigger one
        *
        """
    )
    return


@app.cell
def _(DiGraphMatcher):
    def monomorphisms(G1, G2):
        print("Monomorphisms:")
        return list(DiGraphMatcher(G1, G2).subgraph_monomorphisms_iter())

    def isomorphisms(G1, G2):
        print("Isomorphisms:")
        return list(DiGraphMatcher(G1, G2).subgraph_isomorphisms_iter())

    return isomorphisms, monomorphisms


@app.cell
def _(bra, isomorphisms, monomorphisms, who):
    # from the image, we can see that BRA and WHO are a match
    print(monomorphisms(bra, who))
    print(isomorphisms(bra, who))

    return


@app.cell
def _(ger, isomorphisms, monomorphisms, usa, who):
    # but they all have until S361 in common
    print("WHO and USA:")
    print(monomorphisms(who, usa))
    print(isomorphisms(who, usa))
    print(monomorphisms(usa, who))
    print(isomorphisms(usa, who))

    print("\n\nWHO and GER:")
    print(monomorphisms(who, ger))
    print(isomorphisms(who, ger))
    print(monomorphisms(ger, who))
    print(isomorphisms(ger, who))

    return


@app.cell
def _(mo):
    mo.md(
        """
        ## Motifs (grandioso-networkx)

        Not working out of the box but with some changes we got some results.

        * `is_node_structural_match`: match node ID (code) and structure (degree); needs to check the length of the code so it matches with WHO rules
        * `is_node_attr_match`: needs to be overwritten because it checks if the attributes are the same
        * `is_edge_attr_match`: ditto
        """
    )
    return


@app.cell
def _(find_motifs, itertools, trees):
    all_version_pairs = list(itertools.combinations(trees.keys(), 2))
    is_edge_attr_match = lambda motif_edge_id, host_edge_id, motif, host: True
    is_node_attr_match = (
        lambda motif_node_id, host_node_id, motif, host: host_node_id == motif_node_id
    )
    is_node_structural_match = (
        lambda motif_node_id, host_node_id, motif, host: host.degree(host_node_id)
        >= motif.degree(motif_node_id)
        and len(host_node_id) == len(motif_node_id)
    )
    motif_kwargs = {
        "is_node_attr_match": is_node_attr_match,
        "is_edge_attr_match": is_edge_attr_match,
        "is_node_structural_match": is_node_structural_match,
    }

    for pair in all_version_pairs:
        version1, version2 = pair
        G1 = trees[version1]
        G2 = trees[version2]
        if len(G1.nodes) > len(G2.nodes):
            host = G1
            motif = G2
            label1 = version1
            label2 = version2
        else:
            label1 = version2
            label2 = version1
            host = G2
            motif = G1
        result = find_motifs(motif, host, **motif_kwargs)
        print(f"{label1} and {label2}: {len(result)}")
    return (motif_kwargs,)


@app.cell
def _(bra, find_motifs_iter, motif_kwargs, usa):
    list(find_motifs_iter(bra, usa, **motif_kwargs))
    return


@app.cell
def _(bra, find_motifs, motif_kwargs, usa):
    # find_motifs: Get a list of mappings from motif node IDs to host graph IDs.

    list(find_motifs(bra, usa, **motif_kwargs))
    return


@app.cell
def _(find_motifs, ger, motif_kwargs, usa):
    list(find_motifs(usa, ger, **motif_kwargs))
    return


if __name__ == "__main__":
    app.run()
