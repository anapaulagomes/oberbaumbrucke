import marimo

__generated_with = "0.14.9"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import plotly.express as px
    import polars as pl
    return pl, px


@app.cell
def _(pl):
    df = pl.concat([
        pl.read_csv("artifacts/icd-10-gm___icd-10-who__jina-embeddings-v3_0.7.csv"),
        pl.read_csv("artifacts/cid-10-bra-2008___icd-10-who__jina-embeddings-v3_0.7.csv"),
        pl.read_csv("artifacts/icd-10-cm___icd-10-who__jina-embeddings-v3_0.7.csv")
    ])
    df
    return (df,)


@app.cell
def _(df):
    df.describe()
    return


@app.cell
def _(df, px):
    _fig = px.histogram(df, x="title_score", color="from_version", title="Histogram of the ICD-10 title/description scores")
    _fig.show()
    return


@app.cell
def _(df, pl):
    # Primeiro calculamos quantas versões únicas existem no dataset filtrado
    total_versions = (
        df
        .filter(pl.col("is_match") == False)
        .select("from_version")
        .n_unique()
    )

    # Depois encontramos códigos que aparecem em todas essas versões
    result = (
        df
        .filter(pl.col("is_match") == False)
        .group_by("from_icd_code")
        .agg(pl.col("from_version").n_unique().alias("versions_count"))
        .filter(pl.col("versions_count") == total_versions)
        .select("from_icd_code")
    )
    result
    return


@app.cell
def _(df, pl):
    (
        df
        .filter(pl.col("is_match") == False)
        .group_by("from_icd_code")
        .agg(pl.col("from_version").n_unique().alias("versions_count"))
        .filter(pl.col("versions_count") == df.filter(pl.col("is_match") == False).select("from_version").n_unique())
        .select("from_icd_code")
    )
    return


if __name__ == "__main__":
    app.run()
