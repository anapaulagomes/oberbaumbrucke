import marimo

__generated_with = "0.14.9"
app = marimo.App(width="full")


@app.cell
def _():
    from itertools import cycle

    import marimo as mo
    import plotly.express as px
    import plotly.graph_objects as go
    import polars as pl
    from plotly.subplots import make_subplots
    return go, make_subplots, pl, px


@app.cell
def _():
    COLOR_BY_VERSION = {
        "icd-10-who": "deepskyblue",
        "icd-10-cm": "red",
        "icd-10-gm": "gold",
        "cid-10-bra-2008": "green",
    }
    return (COLOR_BY_VERSION,)


@app.cell
def _(pl):
    df = pl.read_csv("artifacts/results/*.csv")
    df
    return (df,)


@app.cell
def _(df):
    df.describe()
    return


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
        title="Histogram of the ICD-10 title/description scores",
        color_discrete_map=COLOR_BY_VERSION,
        histnorm="percent",
    )
    _fig
    return


@app.cell
def _(COLOR_BY_MODEL, COLOR_BY_VERSION, df, go, make_subplots, models, pl):
    versions = list(COLOR_BY_VERSION.keys())

    _fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=versions,
        vertical_spacing=0.08,
        shared_xaxes=True
    )

    for i, version in enumerate(versions):
        version_data = df.filter(pl.col("from_version").eq(version))
        row = (i // 2) + 1
        column = (i % 2) + 1

        for model in models:
            model_data = version_data.filter(pl.col("model").eq(model))
            _fig.add_trace(
                go.Box(
                    x=model_data["title_score"].to_list(),
                    name=model,
                    legendgroup=model,  # group legend items
                    showlegend=(i == 0),  # only show legend for first subplot
                    marker_color=COLOR_BY_MODEL[model],
                    boxmean=True
                ),
                row=row, col=column
            )

    _fig.update_layout(
        height=800,
        title_text="Model Scores by Version",
        legend=dict(
            orientation="h",
            xanchor="center",
            x=0.5,
        )
    )
    _fig.update_xaxes(title_text="Score", row=4, col=1)
    _fig.update_yaxes(title_text="ICD-10 version", showticklabels=False)
    # _fig.write_image("artifacts/box_plot_model_scores_all_versions.png")
    _fig
    return (versions,)


@app.cell
def _(df, px, versions):
    _fig = px.bar(
        df.group_by(["match_type", "from_version", "model"]).len(),
        x="match_type", y="len", barmode="group",
        facet_row="model", facet_col="from_version",
        category_orders={"from_version": versions, "match_type": ["match_code", "match_code_and_description", "uphill_match", "not_found"]}
    )
    _fig
    return


@app.cell
def _(COLOR_BY_MODEL, df, go, make_subplots, models, pl, versions):
    _fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=versions,
        vertical_spacing=0.08,
        shared_xaxes=True
    )

    for i, version in enumerate(versions):
        version_data = df.filter(pl.col("from_version").eq(version))
        row = (i // 2) + 1
        column = (i % 2) + 1

        for model in models:
            model_data = version_data.filter(pl.col("model").eq(model))
            _fig.add_trace(
                go.Box(
                    x=model_data["title_score"].to_list(),
                    name=model,
                    legendgroup=model,  # group legend items
                    showlegend=(i == 0),  # only show legend for first subplot
                    marker_color=COLOR_BY_MODEL[model],
                    boxmean=True
                ),
                row=row, col=column
            )

    _fig.update_layout(
        height=800,
        title_text="Model Scores by Version",
        legend=dict(
            orientation="h",
            xanchor="center",
            x=0.5,
        )
    )
    _fig.update_xaxes(title_text="Score", row=4, col=1)
    _fig.update_yaxes(title_text="ICD-10 version", showticklabels=False)
    # _fig.write_image("artifacts/box_plot_model_scores_all_versions.png")
    _fig
    return


@app.cell
def _(df, pl, px):
    _fig = px.scatter(
        df.group_by(["match_type", "from_version", "model"]).agg([
            pl.col("title_score").mean().alias("avg_title_score"),
            pl.col("model").len().alias("count")
        ]),
        x="count",
        y="avg_title_score",
        color='match_type',
        facet_col="from_version",
        # hover_data=["model"]
    )
    _fig.update_xaxes(matches=None)
    _fig.show()

    return


if __name__ == "__main__":
    app.run()
