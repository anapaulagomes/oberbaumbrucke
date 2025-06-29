import duckdb
import polars as pl
from rich.progress import Progress, SpinnerColumn, TextColumn
from sentence_transformers import SentenceTransformer

from oberbaum.icd_graph.models import MODELS

conn = duckdb.connect("icd10_embeddings.db")


def all_graphs():
    from oberbaum.cli import get_graph

    graphs = [
        "icd-10-who",
        "icd-10-gm",
        "icd-10-cm",
        "cid-10-bra-2008",
    ]
    for graph in graphs:
        yield get_graph(graph, gml_filepath=f"{graph}.gml")


def store_embeddings(con):
    for graph in all_graphs():
        for model in MODELS:
            if is_embeddings_version_stored(con, graph.version_name, model.name):
                print(
                    f"Embeddings for {graph.version_name} with model {model.name} already stored."
                )
                continue
            else:
                codes_with_embeddings = set_embeddings_from_descriptions(
                    graph, model.name, model.args, only_embeddings=True
                )
                print(
                    f"Storing embeddings for {graph.version_name} with model {model.name}."
                )
                conn.register("df_view", codes_with_embeddings)
                conn.execute(f"""
                    INSERT INTO icd_embeddings (version, icd_code, title, embedding, model)
                    SELECT version, code, title, embeddings, '{model.name}' AS model FROM df_view
                """)


def create_embeddings_table_if_not_exists(con):
    con.from_query(
        """
        CREATE SEQUENCE IF NOT EXISTS id_sequence START 1;
        CREATE TABLE IF NOT EXISTS icd_embeddings(
             id INTEGER DEFAULT nextval('id_sequence'),
             version VARCHAR,
             icd_code VARCHAR,
             title VARCHAR,
             embedding FLOAT[],
             model VARCHAR
        );
        """
    )


def create_matching_table_if_not_exists(con):
    con.from_query(
        """
        CREATE SEQUENCE IF NOT EXISTS id_matching_sequence START 1;
        CREATE TABLE IF NOT EXISTS icd_embeddings(
             id INTEGER DEFAULT nextval('id_matching_sequence'),
             from_version VARCHAR,
             to_version VARCHAR,
             from_icd_code VARCHAR,
             to_icd_code VARCHAR,
             match_type VARCHAR,
             title_score FLOAT,
             from_title VARCHAR,
             to_title VARCHAR,
             model VARCHAR,
             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
             threshold FLOAT
        );
        """
    )


def is_embeddings_version_stored(con, version, model):
    create_embeddings_table_if_not_exists(con)
    result = con.execute(
        "SELECT EXISTS(SELECT * FROM icd_embeddings WHERE version=? AND model=?)",
        [version, model],
    ).fetchone()
    if result:
        return result[0]
    return False


def get_embedding(version, icd_code, model):
    result = conn.execute(
        """
        SELECT
        embedding
        FROM icd_embeddings WHERE model = $model AND version = $version AND icd_code = $icd_code;
        """,
        {"model": model, "version": version, "icd_code": icd_code},
    ).fetchone()
    if result:
        return result[0]
    return


def similar_icd_codes(
    from_version, target_version, icd_code, model, dimensions=1024, limit=5
):
    sql = f"""
    SELECT icd_code, title, score
    FROM (
        SELECT *, array_cosine_similarity(embedding::float[{dimensions}], ($icd_code_embedding)::float[{dimensions}]) AS score
        FROM icd_embeddings WHERE model = $model AND version = $target_version
    ) sq
    WHERE score IS NOT NULL
    ORDER BY score DESC LIMIT $limit;
    """
    icd_code_embedding = get_embedding(from_version, icd_code, model)
    result = conn.execute(
        sql,
        {
            "model": model,
            "target_version": target_version,
            "icd_code_embedding": icd_code_embedding,
            "limit": limit,
        },
    ).fetchall()
    return result


def get_semantic_score_for_same_code(
    from_version, to_version, icd_code, model, dimensions=1024
):
    result = conn.execute(
        f"""
        SELECT
        array_cosine_similarity(
            embedding::float[{dimensions}], (
            SELECT embedding
            FROM icd_embeddings
            WHERE model = $model AND version = $from_version AND icd_code = $icd_code)::float[{dimensions}]
            ) AS similarity
        FROM icd_embeddings WHERE model = $model AND version = $to_version AND icd_code = $icd_code
        ORDER BY similarity DESC;
        """,
        {
            "model": model,
            "from_version": from_version,
            "to_version": to_version,
            "icd_code": icd_code,
        },
    ).fetchone()
    if result:
        return result[0]
    return


def encode_icd_descriptions(sentences, model):
    return model.encode(sentences, convert_to_tensor=True)


def set_embeddings_from_descriptions(
    graph, model_name, model_args=None, only_embeddings=False
):  # FIXME rename encode, get embeddings
    """Get the embeddings for all descriptions in the graph."""
    if model_args is None:
        model_args = {}

    model = SentenceTransformer(model_name, **model_args)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        descriptions = []
        codes = []
        codes_with_embeddings = list(graph.get_codes(data=True))

        progress.add_task(description="Preparing nodes...", total=None)
        for node, data in codes_with_embeddings:
            descriptions.append(data.get("title", "") or data.get("description", ""))
            codes.append(data.get("name", node))

        progress.add_task(description="Getting embeddings...", total=None)
        tensor_embeddings = encode_icd_descriptions(descriptions, model)
        embeddings = [emb.tolist() for emb in tensor_embeddings]

        progress.add_task(description="Storing embeddings...", total=None)
        for index, (node, data) in enumerate(codes_with_embeddings):
            data["embeddings"] = embeddings[index]

        if only_embeddings:
            return pl.DataFrame(
                {
                    "embeddings": embeddings,
                    "title": descriptions,
                    "version": graph.version_name,
                    "code": codes,
                }
            )  # FIXME improve naming
        return graph, codes_with_embeddings
