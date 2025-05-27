import marimo

__generated_with = "0.13.0"
app = marimo.App()


@app.cell
def _():
    import plotly.express as px
    import polars as pl

    return pl, px


@app.cell
def load_data(pl):
    df = pl.concat(
        [
            pl.read_csv("artifacts/icd-10-who___icd-10-cm__bge-m3_0.75.csv"),
            pl.read_csv(
                "artifacts/icd-10-who___icd-10-cm__paraphrase-multilingual-MiniLM-L12-v2_0.75.csv"
            ),
            pl.read_csv(
                "artifacts/icd-10-who___icd-10-cm__distiluse-base-multilingual-cased-v2_0.75.csv"
            ),
        ]
    )

    df
    return (df,)


@app.cell
def basic_info(df):
    df.shape
    return


@app.cell
def _(df):
    df.describe()[["statistic", "description_score"]]
    return


@app.cell
def _(df, pl, px):
    _counts = df.group_by("is_match").agg(pl.len().alias("count")).sort("count")

    px.bar(_counts, x="is_match", y="count", title="Is a match?", color="is_match")
    return


@app.cell
def _(df, px):
    # _counts = df.group_by("match_type").agg(pl.len().alias("count")).sort("count")

    px.bar(df, x="match_type", title="Match type", color="model")
    return


@app.cell
def distribution_description_score(df, px):
    _fig = px.histogram(
        df,
        x="description_score",
        nbins=30,
        title="Distribution of description_score",
        labels={"description_score": "Description Score"},
    )
    _fig.update_layout(bargap=0.1)
    _fig.show()
    return


if __name__ == "__main__":
    app.run()
