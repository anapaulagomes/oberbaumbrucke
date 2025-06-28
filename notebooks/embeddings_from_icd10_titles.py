

import marimo

__generated_with = "0.13.0"
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
    from oberbaum.icd_graph.match import (
        semantically_similar,
        set_embeddings_from_descriptions,
    )
    return SentenceTransformer, duckdb, get_graph, mo, pl, px, umap, util


@app.cell
def _(duckdb):
    conn = duckdb.connect("icd10_embeddings.db")
    return (conn,)


app._unparsable_cell(
    r"""
    * sequence length vs mean title length
    * language training sample vs score
    * dimension vs score
    * how to visualize the embeddings?
    """,
    name="_"
)


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
def _(example_model, util):
    example = [
        "Disorders of refraction and accommodation",  # WHO and USA
        "Akkommodationsstörungen und Refraktionsfehler",  # German
        "Transtornos da refração e da acomodação",  # Portugues
        "Vices de réfraction et troubles de l'accommodation",  # French
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
        title="H52: Disorders of refraction and accommodation",
    )
    _fig.update_yaxes(side="left")
    # _fig.write_image("icd10_example_h52_jina.pdf")  # TODO
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
        "cid-10-bra-2008", gml_filepath="cid-10-bra-2008.gml"
    )
    return B, G, U, W


@app.cell
def _(B):
    B.get("A507")
    return


@app.cell
def _(G):
    G.get("A507")
    return


@app.cell
def _(W):
    W.get("A507")
    return


@app.cell
def _(U):
    U.get(
        "A507"
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
def _(pl, px, text_data):
    _df_descriptions = pl.DataFrame(text_data)
    _grouped_df_descriptions = (
        _df_descriptions.group_by("version")
        .agg((pl.col("title").str.len_chars()).mean().alias("title_length_mean"))
        .sort("title_length_mean")
    )
    _fig = px.bar(_grouped_df_descriptions, y="title_length_mean", x="version")
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
def _():
    COLOR_BY_VERSION = {
        "icd-10-who": "deepskyblue",
        "cid-10-bra": "green",
        "icd-10-gm": "gold",
        "icd-10-cm": "red",
    }
    return (COLOR_BY_VERSION,)


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
    # TODO add note about abreviations in the Brazilian coding V25.4, V26.4, V27.4
    return


@app.cell
def _():
    # embeddings_scatter_plot(reduce_embeddings(bra_codes_with_embeddings))
    return


@app.cell
def _(conn, icd_embeddings, mo):
    _models = mo.sql(
        f"""
        SELECT distinct(model) FROM icd_embeddings ORDER BY model;
        """,
        engine=conn
    )
    return


@app.cell
def _(conn):
    def get_embedding(version1, version2, icd_code, model="jinaai/jina-embeddings-v3", limit=3, dimensions=1024):
        return conn.execute(f"""
            SELECT
            array_cosine_similarity(embedding::float[{dimensions}], (SELECT embedding FROM icd_embeddings WHERE model = $model AND version = $version2 AND icd_code = $icd_code)::float[{dimensions}]) AS similarity
            FROM icd_embeddings WHERE model = $model AND version = $version1 AND icd_code = $icd_code
            ORDER BY similarity DESC LIMIT $limit;
            """,
            {"model": model, "version1": version1, "version2": version2, "icd_code": icd_code, "limit": limit}
        ).fetchone()[0]

    return (get_embedding,)


@app.cell
def _(get_embedding):
    models = {
        "BAAI/bge-m3": 1024,
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 384,
        "sentence-transformers/LaBSE": 768,
        "sentence-transformers/distiluse-base-multilingual-cased-v1": 512,
        "jinaai/jina-embeddings-v3": 1024,
    }

    def score_for_code(code):
        print(f" @ {code}")
        for model, dimensions in models.items():
            print(f"--- {model} ({dimensions})")
            print(get_embedding("icd-10-who", "icd-10-gm", code, model, dimensions=dimensions))
            print(get_embedding("icd-10-who", "cid-10-bra", code, model, dimensions=dimensions))
            print(get_embedding("icd-10-who", "icd-10-cm", code, model, dimensions=dimensions))


    score_for_code("A507")
    score_for_code("H520")
    return


@app.cell
def _(conn, icd_embeddings, mo):
    _df = mo.sql(
        f"""
        SELECT version, icd_code FROM icd_embeddings WHERE icd_code LIKE 'H520' LIMIT 100
        """,
        engine=conn
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
