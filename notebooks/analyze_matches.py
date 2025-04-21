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
    df = pl.read_csv("cid-10-bra___icd-10-who.csv")
    df.head()
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
    _counts = df.group_by("is_match").agg(pl.count()).sort("count")

    px.bar(_counts, x="is_match", y="count", title="Is a match?", color="is_match")
    return


@app.cell
def _(df, pl, px):
    _counts = df.group_by("match_type").agg(pl.count()).sort("count")

    px.bar(_counts, x="match_type", y="count", title="Match type", color="match_type")
    return


@app.cell
def distribution_description_score(df, px):
    pdf = df.select("description_score")

    fig = px.histogram(
        pdf,
        x="description_score",
        nbins=30,
        title="Distribution of description_score",
        labels={"description_score": "Description Score"},
    )
    fig.update_layout(bargap=0.1)
    fig.show()
    return


if __name__ == "__main__":
    app.run()
