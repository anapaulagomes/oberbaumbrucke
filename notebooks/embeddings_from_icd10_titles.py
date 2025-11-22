import marimo

__generated_with = "0.17.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import duckdb
    import marimo as mo
    import plotly.express as px
    import polars as pl
    import umap.umap_ as umap
    from sentence_transformers import SentenceTransformer, util

    from oberbaum.cli import get_graph
    from oberbaum.icd_graph.embeddings import (
        get_connection,
        get_embedding,
        similar_icd_codes,
    )
    from oberbaum.icd_graph.models import MODELS
    return (
        MODELS,
        SentenceTransformer,
        get_connection,
        get_embedding,
        get_graph,
        mo,
        pl,
        px,
        similar_icd_codes,
        umap,
        util,
    )


@app.cell
def _(get_connection):
    conn = get_connection()
    return


@app.cell
def _():
    COLOR_BY_VERSION = {
        "icd-10-who": "deepskyblue",
        "cid-10-bra": "green",
        "icd-10-gm": "gold",
        "icd-10-cm": "red",
    }
    return (COLOR_BY_VERSION,)


@app.cell
def _(mo):
    mo.md("""# ICD-10 labels to embeddings""")
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Example of embeddings

    > H52 Disorders of refraction and accommodation

    `
    example = [
        "Disorders of refraction and accommodation",  # WHO and USA
        "Akkommodationsstörungen und Refraktionsfehler", # German
        "Transtornos da refração e da acomodação",  # Portuguese
        "Vices de réfraction et troubles de l'accommodation",  # French
    ]

    Goals:

    * sequence length vs mean title length
    * language training sample vs score
    * dimension vs score
    * how to visualize the embeddings?
    `
    """
    )
    return


@app.cell
def _(SentenceTransformer):
    example_model = SentenceTransformer(
        "jinaai/jina-embeddings-v3", trust_remote_code=True
    )
    return (example_model,)


@app.cell
def _():
    return


@app.cell
def _(example_model, util):
    example = [
        "Other mosquito-borne viral fevers",  # WHO
        "Zika virus disease",# USA
        "Sonstige durch Moskitos [Stechmücken] übertragene Viruskrankheiten",  # German
        "Doenca pelo Zika virus",  # Portugues
        # "Vices de réfraction et troubles de l'accommodation",  # French
    ]
    _embeddings = example_model.encode(example, convert_to_tensor=True)
    example_results = {"sentence_1": [], "sentence_2": [], "score": []}
    for oid, _ in enumerate(example):
        for iid, _ in enumerate(example):
            _hits = util.semantic_search(
                _embeddings[iid],
                _embeddings[oid],
                score_function=util.cos_sim,
                top_k=1,
            )
            example_results["sentence_1"].append(example[oid])
            example_results["sentence_2"].append(example[iid])
            example_results["score"].append(_hits[0][0]["score"])
    return (example_results,)


@app.cell
def _():
    import plotly.io as pio
    pio.kaleido.scope.mathjax = None
    return


@app.cell
def _(example_results, pl, px):
    example_matrix = pl.DataFrame(example_results).pivot(
        values="score", index="sentence_2", on="sentence_1"
    )
    example_y = example_matrix["sentence_2"]
    example_matrix = example_matrix.drop("sentence_2")
    _fig = px.imshow(
        example_matrix,
        y=example_y,
        color_continuous_scale="rdpu",
        text_auto=True,
    )
    _fig.update_yaxes(side="left")
    _fig.write_image("icd10_example_A925_jina.pdf")
    _fig.show()
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Loading the graphs

    Attributes:

    * `name`: label e.g. A507
    * `title`: short title, e.g. "Chronic bronchitis, unspecified"
    """
    )
    return


@app.cell
def _(get_graph):
    W = get_graph("icd-10-who", gml_filepath="icd-10-who.gml")
    G = get_graph("icd-10-gm", gml_filepath="icd-10-gm.gml")
    U = get_graph("icd-10-cm", gml_filepath="icd-10-cm.gml")
    B = get_graph(
        "cid-10-bra", gml_filepath="cid-10-bra.gml"
    )
    return B, G, U, W


@app.cell
def _(B):
    B.get("A925")
    return


@app.cell
def _(G):
    G.get("A925")
    return


@app.cell
def _(W):
    W.get("A925")
    return


@app.cell
def _(U):
    U.get(
        "A925"
    )  # TODO check naming in WHO guidelines
    return


@app.cell
def _(U):
    U.version_name
    return


@app.cell
def _(B, G, U, W):
    text_data = []  # code, title, version

    def assign_descriptions(A, text_data):
        for node, data in A._graph.nodes(data=True):
            if node == "root":
                continue
            text_data.append(
                {
                    "code": node,
                    "title": data.get("title", ""),
                    "version": A.version_name,
                }
            )

    assign_descriptions(W, text_data)
    assign_descriptions(B, text_data)
    assign_descriptions(U, text_data)
    assign_descriptions(G, text_data)
    return (text_data,)


@app.cell
def _(COLOR_BY_VERSION, pl, px, text_data):
    _df_descriptions = pl.DataFrame(text_data)
    _grouped_df_descriptions = (
        _df_descriptions.select(pl.col("version"), pl.col("title").str.len_chars().alias("title_length"))
    )
    _fig = px.box(_grouped_df_descriptions, y="title_length", x="version", color="version", color_discrete_map=COLOR_BY_VERSION)
    # _fig.add_hline(y=_grouped_df_descriptions['title_length_mean'].max())
    _fig.show()
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Get embeddings from all codes

    Questions:

    * sequence length vs mean title length
    * language training sample vs score
    * dimension vs score
    * how to visualize the embeddings?
    """
    )
    return


@app.cell
def _(pl, umap):
    def reduce_embeddings(df_embeddings):
        umap_model = umap.UMAP(
            n_components=2, random_state=2024, verbose=False, n_jobs=1
        )
        projection = umap_model.fit_transform(X=df_embeddings["embeddings"])
        return df_embeddings.with_columns(
            [pl.Series("u0", projection[:, 0]), pl.Series("u1", projection[:, 1])]
        )
    return


@app.cell
def _(COLOR_BY_VERSION, px):
    def embeddings_scatter_plot(df_embeddings_umap):
        _fig = px.scatter(
            df_embeddings_umap,
            x="u0",
            y="u1",
            hover_data=["code", "title", "version"],
            color="version",
            color_discrete_map=COLOR_BY_VERSION,
        )
        return _fig.show()
    return


@app.cell
def _():
    # embeddings_scatter_plot(reduce_embeddings(bra_codes_with_embeddings))
    return


@app.cell
def _(get_embedding):
    get_embedding("icd-10-who", "A05", model="jinaai/jina-embeddings-v3")
    return


@app.cell
def _(get_embedding):
    get_embedding("icd-10-cm", "Y80", model="jinaai/jina-embeddings-v3") is None
    return


@app.cell
def _(similar_icd_codes):
    def check(code, model="jinaai/jina-embeddings-v3", dimensions=1024, limit=5):
        print(similar_icd_codes("icd-10-who", "icd-10-gm", code, model, dimensions, limit))
        print(similar_icd_codes("icd-10-who", "icd-10-cm", code, model, dimensions, limit))
        print(similar_icd_codes("icd-10-who", "cid-10-bra", code, model, dimensions, limit))

    # check("X53")  # bom exemplo
    check("X50")  # bom exemplo
    return (check,)


@app.cell
def _(MODELS, check):
    # check("X53")  # bom exemplo
    code = "A38"
    for model in MODELS:
        print(model.name, model.dimensions)
        check(code, model.name, model.dimensions)
    return


if __name__ == "__main__":
    app.run()
