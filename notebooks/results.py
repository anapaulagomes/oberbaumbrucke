import marimo

__generated_with = "0.17.2"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import plotly.express as px
    import plotly.graph_objects as go
    import polars as pl
    from plotly.subplots import make_subplots

    from oberbaum.config import get_results_dir
    return get_results_dir, go, make_subplots, pl, px


@app.cell
def _(get_results_dir):
    from dotenv import load_dotenv

    load_dotenv()
    results_dir = get_results_dir("artifacts")
    results_dir
    return (results_dir,)


@app.cell
def _():
    import plotly.io as pio

    tableau20_hex = [
        '#1F77B4', '#AEC7E8', '#FF7F0E', '#FFBB78', '#2CA02C', '#98DF8A',
        '#D62728', '#FF9896', '#9467BD', '#C5B0D5', '#8C564B', '#C49C94',
        '#E377C2', '#F7B6D2', '#7F7F7F', '#C7C7C7', '#BCBD22', '#DBDB8D',
        '#17BECF', '#9EDAE5'
    ]

    pio.templates['plotly'].layout.colorway = tableau20_hex
    pio.templates.default = 'plotly'
    return


@app.cell
def _():
    COLOR_BY_VERSION = {
        "icd-10-who": "deepskyblue",
        "icd-10-cm": "red",
        "icd-10-gm": "gold",
        "cid-10-bra": "green",
    }
    return


@app.cell
def _():
    MODEL_NAME = 'jinaai/jina-embeddings-v3'
    THRESHOLD = 0.5
    return MODEL_NAME, THRESHOLD


@app.cell
def _(THRESHOLD, pl, results_dir):
    df = pl.read_csv(f"{results_dir}/*.csv").filter(pl.col("threshold").eq(THRESHOLD))
    df
    return (df,)


@app.cell
def _(MODEL_NAME, df, pl):
    df_filtered = df.filter(pl.col("model").eq(MODEL_NAME))
    return (df_filtered,)


@app.cell
def _(df):
    df.describe()
    return


@app.cell
def _(df):
    match_types = df["match_type"].unique()
    return


@app.cell
def _():
    versions = ["icd-10-who", "icd-10-gm", "icd-10-cm", "cid-10-bra"]
    return (versions,)


@app.cell
def _(df, px):
    models = df["model"].unique()
    _colors = px.colors.qualitative.T10[:len(models)]
    COLOR_BY_MODEL = dict(zip(models, _colors))
    COLOR_BY_MODEL
    return COLOR_BY_MODEL, models


@app.cell
def _(df_filtered, pl, px):
    _fig = px.histogram(
        df_filtered.filter(pl.col("from_version").ne("icd-10-who")),
        x="title_score",
        color="from_version",
        log_y=True,
        facet_col="from_version",
    )

    _fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    _fig.update_xaxes(title='')

    _fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))  # remove col= sign
    _fig.add_annotation(
        showarrow=False,
        xanchor='center',
        xref='paper',
        x=0.5,
        yref='paper',
        y=-0.1,
        text='Cosine similarity',
        font={"size": 20}
    )

    _fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        font_size=16,
        height=600,
        width=1800,
        barmode='overlay'
    )
    # _fig.write_image("histogram_distances.png")
    _fig.write_image("histogram_cosine_similarities.pdf")
    _fig
    return


@app.cell
def _(THRESHOLD, df_filtered, pl, px, versions):
    _grouped_df = df_filtered.filter(pl.col("threshold").eq(THRESHOLD)).group_by(["match_type", "from_version"]).len(name="count")
    _fig = px.bar(
        _grouped_df,
        x="match_type",
        y="count",
        text="count",
        facet_col="from_version",
        facet_row_spacing=0.06,
        category_orders={"from_version": versions, "match_type": ["match_code", "match_code_and_description", "uphill_match", "not_found"]}
    )

    _fig.update_xaxes(zeroline=True, linewidth=1, linecolor='lightgrey', tickangle=45, tickfont={"size": 16}, title='')
    _fig.update_yaxes(showticklabels=True, showgrid=True, gridwidth=1, gridcolor='lightgrey', tickfont={"size": 16})
    _fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))  # remove col= sign

    _fig.add_annotation(
        showarrow=False,
        xanchor='center',
        xref='paper',
        x=0.5,
        yref='paper',
        y=-0.25,
        text='Match type',
        font={"size": 20}
    )

    _fig.update_layout(
        height=1000,
        width=1800,
        margin=dict(r=250),
        plot_bgcolor='rgba(0,0,0,0)',
        font_size=16,
    )
    _fig.write_image("results_per_match_type.pdf")
    _fig
    return


@app.cell
def _(df, px, versions):
    _grouped_df = df.group_by(["match_type", "from_version", "model"]).len(name="count")
    _grouped_df["model"].unique()
    _fig = px.bar(
        _grouped_df,
        x="match_type", y="count", barmode="group",
        facet_row="model", facet_col="from_version",
        facet_row_spacing=0.06,
        category_orders={"from_version": versions, "match_type": ["match_code", "match_code_and_description", "uphill_match", "not_found"]}
    )
    new_annotations = []
    for ann in _fig.layout.annotations:
        if ann.xanchor != 'left': #< 0.5:  # Keep left-side annotations (likely column titles)
            new_annotations.append(ann)

    # add properly positioned row titles
    for i, row_title in enumerate(_grouped_df["model"].unique()):
        new_annotations.append(
            dict(
                text=row_title.rsplit("/")[-1],
                x=1.0,
                y=1 - (i * 0.2) - 0.1,
                xref='paper',
                yref='paper',
                textangle=0,
                showarrow=False,
                font=dict(size=12)
            )
        )

    _fig.update_layout(
        height=1000,
        width=1800,
        margin=dict(r=250),
        annotations=new_annotations,
        plot_bgcolor='rgba(0,0,0,0)',

    )
    _fig.update_xaxes(zeroline=True, linewidth=1, linecolor='lightgrey')
    _fig.update_yaxes(showticklabels=True, showgrid=True, gridwidth=1, gridcolor='lightgrey')
    _fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))  # remove col= sign
    _fig.write_image("results_per_match_type.pdf")
    # _fig.write_image("results_per_match_type.png")
    _fig
    return


@app.cell
def _(COLOR_BY_MODEL, df, go, make_subplots, models, pl):
    _fig = make_subplots(
        rows=1, cols=4,
        subplot_titles=["icd-10-who", "icd-10-gm", "icd-10-cm", "cid-10-bra"],
        vertical_spacing=0.08,
        shared_xaxes=True
    )

    def plot_version(version, row=1, column=None, showlegend=False):
        version_data = df.filter(pl.col("from_version").eq(version))
        for model in models:
            model_data = version_data.filter(pl.col("model").eq(model))
            _fig.add_trace(
                go.Box(
                    x=model_data["title_score"].to_list(),
                    name=model,
                    legendgroup=model,  # group legend items
                    showlegend=column == 1,  # only show legend for first subplot
                    marker_color=COLOR_BY_MODEL[model],
                    boxmean=True
                ),
                row=row, col=column
            )

    plot_version("icd-10-who", column=1)
    plot_version("icd-10-gm", column=2)
    plot_version("icd-10-cm", column=3)
    plot_version("cid-10-bra", column=4)

    _fig.update_layout(
        height=800,
        width=1600,
        legend=dict(
            orientation="h",
            xanchor="center",
            x=0.5,
        ),
        paper_bgcolor='rgba(0,0,0,0)',  # remove plotly blue background
        plot_bgcolor='rgba(0,0,0,0)',
    )
    _fig.update_xaxes(range=[0, 1], title="Cosine similarity distance")
    _fig.update_yaxes(showticklabels=False)
    # _fig.write_image("box_plot_model_scores_all_versions.png")
    _fig.write_image("box_plot_model_scores_all_versions.pdf")
    # _fig.write_image("box_plot_model_scores_all_versions.svg")
    _fig
    return


@app.cell
def _(df, pl, px):
    _summary = (
        df.filter(pl.col("from_version").ne("icd-10-who"))
        .group_by(["from_version", "model"])
        .agg([
            pl.len().alias("total_count_per_version"),
            (pl.col("match_type").eq("match_code_and_description")).sum().alias("match_code_and_desc_count")
        ])
        .with_columns(
            (
                pl.col("match_code_and_desc_count") / pl.col("total_count_per_version")
            ).alias("percent")
        )
    )
    _fig = px.density_heatmap(
        _summary,
        x="model",
        y="from_version",
        z="percent",
        text_auto=True,
        color_continuous_scale="Blues",
        labels={
            "model": "Model",
            "from_version": "From Version",
        },
    )

    _fig.update_layout(
        height=500,
        width=1000,
        coloraxis_colorbar=dict(title="%"),
    )
    _fig.update_traces(texttemplate='%{z:.2f}')
    _fig.write_image("match_code_description_0.5_normalized.pdf")
    # _fig.write_image("match_code_description_0.5_normalized.png")
    _fig
    return


@app.cell
def _(df, pl, px):
    _summary = (
        df.filter(pl.col("match_type").is_in(["match_code_and_description"]), pl.col("from_version").ne("icd-10-who"))
        .group_by(["from_version", "model", "match_type"])
        .agg(pl.len().alias("count"))
    )
    _fig = px.density_heatmap(
        _summary,
        x="model",
        y="from_version",
        z="count",
        facet_col="match_type",
        text_auto=True,
        color_continuous_scale="Blues",
        labels={
            "model": "Model",
            "from_version": "From version",
            "count": "Count",
            "match_type": "Match Type"
        },
    )

    _fig.update_layout(
        height=500,
        width=1000,
        coloraxis_colorbar=dict(title="Count"),
    )
    _fig.write_image("models_heatmap.pdf")
    _fig
    return


if __name__ == "__main__":
    app.run()
