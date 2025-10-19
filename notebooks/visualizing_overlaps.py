import marimo

__generated_with = "0.14.9"
app = marimo.App(width="medium")


@app.cell
def _():
    import re
    from pathlib import Path

    import marimo as mo
    import networkx as nx
    import numpy as np
    import plotly.express as px
    import plotly.graph_objects as go
    import polars as pl
    import venn
    from matplotlib_venn import venn2
    from polars.testing import assert_series_equal

    from oberbaum.cli import get_graph
    from oberbaum.icd_graph.graph_overlap import merge_graphs
    return (
        Path,
        assert_series_equal,
        get_graph,
        go,
        merge_graphs,
        mo,
        np,
        nx,
        pl,
        px,
        re,
        venn,
    )


@app.cell
def _(Path, assert_series_equal, pl, re):
    # dir: mcosi / overlap-results-cid-10-bra-icd-10-who-1-10072025165804.json
    all_dfs = []
    for a_file in Path("notebooks/mcosi/").glob("*.json"):
        versions_and_chapter = a_file.name.replace("overlap-results-", "").replace(".json", "")
        matches = re.search(r"(?P<from>\w+-10-\w+(-2008)?)-(?P<to>\w+-10-\w+)-(?P<chapter>\d+)-\d{14}", a_file.name)
        _df = pl.read_json(a_file)
        if not matches:
            continue
        _df = _df.with_columns(chapter=pl.lit(int(matches.groupdict()["chapter"])))
        assert_series_equal(_df["nodes_subtree1"], _df["nodes_subtree2"], check_names=False)
        _df = _df.rename({"nodes_subtree1": "nodes_subtree"})
        _df.drop_in_place("nodes_subtree2")
        all_dfs.append(_df)

    df = pl.concat(all_dfs)
    df
    return (df,)


@app.cell
def _():
    return


@app.cell
def _(get_graph):
    graphs_name = [
        "icd-10-who",
        "icd-10-gm",
        "icd-10-cm",
        "cid-10-bra",
    ]
    graphs = {}
    for graph in graphs_name:
        graphs[graph] = get_graph(graph, gml_filepath=f"{graph}.gml")
    return graphs, graphs_name


@app.cell
def _(graphs):
    who_graph = graphs["icd-10-who"]
    gm_graph = graphs["icd-10-gm"]
    us_graph = graphs["icd-10-cm"]
    bra_graph = graphs["cid-10-bra"]
    who_graph
    return bra_graph, gm_graph, us_graph, who_graph


@app.cell
def _(nx, who_graph):
    nx.shortest_path(who_graph._graph, "root", "M050")
    return


@app.cell
def _(nx):
    def root_to_node(version, graph, node):
        tmp = {
            "version": version,
            "chapter": "",
            "block": "null",
            "3-char": "null",
            "4-char": "null",
            "5-char": "null"
        }
        path = nx.shortest_path(graph, "root", node)
        match len(path):
            case 2:
                tmp["chapter"] = int(path[1])
            case 3:
                tmp["chapter"] = int(path[1])
                tmp["block"] = path[2]
            case 4:
                tmp["chapter"] = int(path[1])
                tmp["block"] = path[2]
                tmp["3-char"] = path[3]
            case 5:
                tmp["chapter"] = int(path[1])
                tmp["block"] = path[2]
                tmp["3-char"] = path[3]
                tmp["4-char"] = path[4]
            case 6:
                tmp["chapter"] = int(path[1])
                tmp["block"] = path[2]
                tmp["3-char"] = path[3]
                tmp["4-char"] = path[4]
                tmp["5-char"] = path[5]
            case _:
                print("Unexpected case")
                print(path)
        return tmp

    return (root_to_node,)


@app.cell
def _():
    all_levels = []
    return (all_levels,)


@app.cell
def _(df, pl, root_to_node, who_graph):
    def format_overlap_data(from_version):
        _all_levels = []
        for row in df.filter(pl.col("from").eq(from_version)).iter_rows(named=True):
            levels = []
            for _node in row["nodes_subtree"]:
                levels.append(root_to_node("overlap", who_graph._graph, _node))
            _all_levels.extend(levels)

        print(_all_levels[1], len(_all_levels))
        return _all_levels
    return (format_overlap_data,)


@app.cell
def _(root_to_node):
    def format_only_graph_data(graph):
        _all_levels = []
        for _node in graph._graph.nodes():
            if _node == "root":
                continue
            tmp = root_to_node(graph.version_name, graph._graph, _node)
            if tmp not in _all_levels:
                _all_levels.append(tmp)
        print(len(_all_levels))
        return _all_levels

    return (format_only_graph_data,)


@app.cell
def _(
    all_levels,
    format_only_graph_data,
    format_overlap_data,
    gm_graph,
    who_graph,
):
    all_levels.extend(format_overlap_data("icd-10-gm"))
    all_levels.extend(format_only_graph_data(who_graph))
    all_levels.extend(format_only_graph_data(gm_graph))
    return


@app.cell
def _(all_levels, pl):
    df_gm = pl.DataFrame(all_levels, schema_overrides={"version": pl.Categorical})
    df_gm
    return (df_gm,)


@app.cell
def _(df_gm):
    # df_overlap_grouped = df_gm.group_by(["version", "chapter", "block", "3-char", "4-char"]).agg(pl.col("5-char").len()).sort("chapter")
    # df_overlap_grouped
    df_gm.dtypes
    return


@app.cell
def _(df_gm, pl):
    # def overlapped_individuals(from_version):
    # a_list = []
    # for row in df.filter(pl.col("from").eq(from_version)).iter_rows(named=True):
    #     for _node in row["nodes_subtree"]:
    overlap_df = df_gm.filter(pl.col("version") == "overlap")
    overlap_combinations = overlap_df.select([
        "chapter", "block", "3-char", "4-char", "5-char"
    ]).unique()
    others_who_df = df_gm.filter(pl.col("version") == "icd-10-who").join(
        overlap_combinations,
        on=["chapter", "block", "3-char", "4-char", "5-char"],
        how="anti"  # anti-join excludes matching rows
    )
    others_gm_df = df_gm.filter(pl.col("version") == "icd-10-gm").join(
        overlap_combinations,
        on=["chapter", "block", "3-char", "4-char", "5-char"],
        how="anti"  # anti-join excludes matching rows
    )
    return others_gm_df, others_who_df, overlap_combinations


@app.cell
def _(overlap_combinations):
    overlap_combinations
    return


@app.cell
def _(others_gm_df):
    others_gm_df
    return


@app.cell
def _(others_who_df):
    others_who_df
    return


@app.cell
def _(others_gm_df, others_who_df, overlap_combinations):
    ind_overlaps = overlap_combinations.to_numpy().flatten()
    ind_who = [ind for ind in others_who_df.to_numpy().flatten() if ind not in ind_overlaps]
    ind_gm = [ind for ind in others_gm_df.to_numpy().flatten() if ind not in ind_overlaps]
    return ind_gm, ind_overlaps, ind_who


@app.cell
def _(mo):
    mo.md(r"""## Sunburst""")
    return


@app.cell
def _():
    color_mapping = {'overlap':'grey', 'icd-10-gm':'gold', 'icd-10-who':'lightblue', 'cid-10-bra': 'green', 'icd-10-cm':'red'}
    return (color_mapping,)


@app.cell
def _(color_mapping, df_gm, ind_gm, ind_overlaps, ind_who, np, px):
    _fig = px.sunburst(df_gm, path=['chapter', 'block', '3-char', '4-char', '5-char'])
    _figure_data = _fig["data"][0]
    _mask = np.char.find(_figure_data.ids.astype(str), "null") == -1
    _figure_data.ids = _figure_data.ids[_mask]
    _figure_data.values = _figure_data.values[_mask]
    _figure_data.labels = _figure_data.labels[_mask]
    _figure_data.parents = _figure_data.parents[_mask]

    marker_colors = []
    chapters_str = [str(ch) for ch in range(1, 23)]
    for cat in _fig.data[-1].labels:
        if cat in ind_overlaps or cat in chapters_str:
            marker_colors.append(color_mapping["overlap"])
        elif cat in ind_gm:
            marker_colors.append(color_mapping["icd-10-gm"])
        elif cat in ind_who:
            marker_colors.append(color_mapping["icd-10-who"])
    _fig.update_traces(marker_colors=marker_colors)
    _fig.write_html("who_gm_comparison_grouped_colored_only_overlap_and_ger.html")
    _fig.write_image("who_gm_comparison_grouped_colored_only_overlap_and_ger.png")
    return


@app.cell
def _(mo):
    mo.md(r"""## Venn diagram""")
    return


@app.cell
def _(bra_graph, gm_graph, us_graph, who_graph):
    colors_rgb = {
        # 'overlap': [0.5, 0.5, 0.5, 0.5],           # grey
        'icd-10-who': [0.68, 0.85, 0.9, 0.4],     # lightblue
        'icd-10-gm': [1.0, 0.84, 0.0, 0.6],       # gold
        'icd-10-cm': [1.0, 0.0, 0.0, 0.5],         # red
        'icd-10-bra-2008': [0.0, 0.5, 0.0, 0.3],   # green
    }

    who_nodes = set(who_graph.all_nodes())
    gm_nodes = set(gm_graph.all_nodes())
    us_nodes = set(us_graph.all_nodes())
    bra_nodes = set(bra_graph.all_nodes())
    return bra_nodes, colors_rgb, gm_nodes, us_nodes, who_nodes


@app.cell
def _(colors_rgb, gm_graph, gm_nodes, venn, who_graph, who_nodes):
    _fig, _ = venn.venn2(
        venn.get_labels([who_nodes, gm_nodes], fill=['number']),
        names=[who_graph.version_name, gm_graph.version_name],
        colors=colors_rgb.values()
    )
    _fig
    return


@app.cell
def _(
    bra_graph,
    bra_nodes,
    colors_rgb,
    gm_graph,
    gm_nodes,
    us_graph,
    us_nodes,
    venn,
    who_graph,
    who_nodes,
):
    _fig, _ = venn.venn4(
        venn.get_labels([who_nodes, gm_nodes, us_nodes, bra_nodes], fill=['number']),
        names=[who_graph.version_name, gm_graph.version_name, us_graph.version_name, bra_graph.version_name],
        colors=colors_rgb.values()
    )
    _fig
    return


@app.cell
def _(mo):
    mo.md(r"""## Bar charts""")
    return


@app.cell
def _(graphs_name):
    graphs_name
    return


@app.cell
def _(df, pl):
    sum_overlap_per_version = df.group_by(["from"]).agg(pl.col("score").sum()).to_dict()
    sum_overlap_per_version["total_codes"] = []
    sum_overlap_per_version["from"]
    return (sum_overlap_per_version,)


@app.cell
def _(graphs, sum_overlap_per_version):
    for version_name in sum_overlap_per_version["from"]:
        sum_overlap_per_version["total_codes"].append(len(list(graphs[version_name].all_nodes())))

    sum_overlap_per_version
    return


@app.cell
def _(graphs):
    who_total_codes = len(list(graphs["icd-10-who"].all_nodes()))
    who_total_codes
    return (who_total_codes,)


@app.cell
def _(color_mapping, go, sum_overlap_per_version, who_total_codes):
    _fig = go.Figure(data=[
        go.Bar(
            name='Codes',
            x=sum_overlap_per_version["from"],
            y=sum_overlap_per_version["total_codes"],
            marker=dict(color=[color_mapping.get(version) for version in sum_overlap_per_version["from"]])
        ),
        go.Bar(
            name='Overlap',
            x=sum_overlap_per_version["from"],
            y=sum_overlap_per_version["score"],
            marker=dict(color='lightgrey'))
    ])

    _fig.update_layout(
        barmode='group',
        paper_bgcolor='rgba(0,0,0,0)',  # remove plotly blue background
        plot_bgcolor='rgba(0,0,0,0)',
        shapes=[
            dict(
                type='line',
                xref='paper',
                yref='y',
                x0=0,
                x1=1,
                y0=who_total_codes,
                y1=who_total_codes,
                line=dict(
                    color='black',
                    width=2,
                    dash='dash'
                )
            )
        ],
        annotations=[
            dict(
                x=1,
                y=who_total_codes,
                xref='paper',
                yref='y',
                text='WHO total codes',
                showarrow=False,
                xanchor='left',
                yanchor='bottom',
                font=dict(color='black')
            )
        ]
    )
    _fig.write_image("topological_overlap_between_versions.png")
    _fig
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Graphs

    The visualization for graphs is done through `viz.py` but in here we prepare the merged graph for visualization.
    """
    )
    return


@app.cell
def _(df, merge_graphs, nx, pl):
    def create_overlap_graph(from_version, from_graph, to_graph):
        overlapped_nodes = df.filter(pl.col("from").eq(from_version)).explode("nodes_subtree")["nodes_subtree"].unique().to_list()
        merged = merge_graphs(from_graph, to_graph, overlapped_nodes)
        nx.write_gml(merged, f"overlap_graph_who_{from_version}.gml")
        return merged
    return (create_overlap_graph,)


@app.cell
def _(create_overlap_graph, gm_graph, who_graph):
    create_overlap_graph("icd-10-gm", gm_graph, who_graph)
    return


@app.cell
def _(create_overlap_graph, gm_graph, who_graph):
    create_overlap_graph("icd-10-cm", gm_graph, who_graph)
    return


@app.cell
def _(create_overlap_graph, gm_graph, who_graph):
    create_overlap_graph("cid-10-bra", gm_graph, who_graph)
    return


if __name__ == "__main__":
    app.run()
