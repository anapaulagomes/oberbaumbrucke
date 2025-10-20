import marimo

__generated_with = "0.16.4"
app = marimo.App()


@app.cell
def _():
    import plotly.express as px
    import polars as pl

    from oberbaum.config import get_results_dir
    return get_results_dir, pl, px


@app.cell
def _():
    from dotenv import load_dotenv

    load_dotenv()
    return


@app.cell
def load_data(get_results_dir, pl):
    results_dir = get_results_dir("artifacts")
    df = pl.concat(
        [
            pl.read_csv(f"{results_dir}/icd-10-cm___icd-10-who__bge-m3_0.75.csv"),
            pl.read_csv(
                f"{results_dir}/icd-10-cm___icd-10-who__paraphrase-multilingual-MiniLM-L12-v2_0.75.csv"
            ),
            pl.read_csv(
                f"{results_dir}/icd-10-cm___icd-10-who__distiluse-base-multilingual-cased-v1_0.75.csv"
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
    df.describe()[["statistic", "title_score"]]
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
def distribution_title_score(df, px):
    _fig = px.histogram(
        df,
        x="title_score",
        nbins=30,
        title="Distribution of title_score",
        labels={"title_score": "Title Score"},
    )
    _fig.update_layout(bargap=0.1)
    _fig.show()
    return


if __name__ == "__main__":
    app.run()
