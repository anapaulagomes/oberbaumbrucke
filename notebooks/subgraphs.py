import marimo

__generated_with = "0.13.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import networkx as nx
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    return go, make_subplots, mo, nx


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
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
