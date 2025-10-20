import marimo

__generated_with = "0.16.4"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import plotly.express as px
    import plotly.graph_objects as go
    import polars as pl
    from plotly.subplots import make_subplots

    from oberbaum.config import get_results_dir
    return get_results_dir, go, make_subplots, mo, pl, px


@app.cell
def _(get_results_dir):
    from dotenv import load_dotenv

    load_dotenv()
    results_dir = get_results_dir("artifacts")
    results_dir
    return (results_dir,)


@app.cell
def _():
    COLOR_BY_VERSION = {
        "icd-10-who": "deepskyblue",
        "icd-10-cm": "red",
        "icd-10-gm": "gold",
        "cid-10-bra": "green",
    }
    return (COLOR_BY_VERSION,)


@app.cell
def _(pl, results_dir):
    df_all_thresholds = pl.read_csv(f"{results_dir}/*.csv")
    df_all_thresholds
    return (df_all_thresholds,)


@app.cell
def _(df_all_thresholds, pl):
    df = df_all_thresholds.filter(pl.col("threshold").eq(0.95))
    return (df,)


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
def _(COLOR_BY_VERSION, df, pl, px):
    _fig = px.histogram(
        df.filter(pl.col("from_version").ne("icd-10-who")),
        x="title_score",
        color="from_version",
        # title="Histogram of the ICD-10 title/description scores",
        color_discrete_map=COLOR_BY_VERSION,
        histnorm="percent",
        opacity=0.6
    )
    # _fig.update_xaxes(showgrid=True)
    # _fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='black')
    _fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    _fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',  # remove plotly blue background
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5  # position (centered)
        ),
        barmode='overlay'
    )
    # _fig.write_image("histogram_distances.png")
    # _fig.write_image("histogram_distances.pdf")
    # _fig.write_image("histogram_distances.svg")
    _fig
    return


@app.cell
def _(df):
    df.group_by(["match_type", "from_version", "model"]).len(name="count")
    return


@app.cell
def _(df, px, versions):
    _grouped_df = df.group_by(["match_type", "from_version", "model"]).len(name="count")
    _grouped_df["model"].unique()
    _fig = px.bar(
        _grouped_df,
        x="match_type", y="count", barmode="group",
        facet_row="model", facet_col="from_version",
        category_orders={"from_version": versions, "match_type": ["match_code", "match_code_and_description", "uphill_match", "not_found"]}
    )
    new_annotations = []
    for ann in _fig.layout.annotations:
        if ann.xanchor != 'left': #< 0.5:  # Keep left-side annotations (likely column titles)
            # print(ann, ann.x)
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
        height=800,
        width=1800,
        margin=dict(r=250),
        annotations=new_annotations
    )
    _fig.update_yaxes(showticklabels=True, showgrid=True, gridwidth=1, gridcolor='lightgrey')
    _fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))  # remove col= sign
    _fig.write_image("results_per_match_type.pdf")
    _fig.write_image("results_per_match_type.png")
    _fig.write_image("results_per_match_type.svg")
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
        # title_text="Model Scores by Version",
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
    _fig.write_image("box_plot_model_scores_all_versions.png")
    _fig.write_image("box_plot_model_scores_all_versions.pdf")
    _fig.write_image("box_plot_model_scores_all_versions.svg")
    _fig
    return


@app.cell
def _(df):
    df.columns
    return


@app.cell
def _(mo):
    match_type_dropdown = mo.ui.dropdown(
        label="Select a match type",
        options=["match_code_and_description", "not_found"],
        value="not_found",
    )
    match_type_dropdown
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
            "from_version": "From Version",
            "count": "Count",
            "match_type": "Match Type"
        },
    )

    _fig.update_layout(
        height=500,
        width=1000,
        coloraxis_colorbar=dict(title="Count"),
    )
    # _fig.write_image("match_types.pdf")
    # _fig.write_image("match_types.png")
    # _fig.write_image("match_types.svg")
    _fig
    return


if __name__ == "__main__":
    app.run()
