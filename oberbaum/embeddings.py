import os

import duckdb
import polars as pl
from dotenv import load_dotenv
from rich.progress import Progress, SpinnerColumn, TextColumn
from sentence_transformers import SentenceTransformer

from oberbaum.models import MODELS

load_dotenv()

EMBEDDINGS_DB = os.getenv("EMBEDDINGS_DB")


def get_connection(writeable=False, db_name=None):
    return duckdb.connect(db_name or EMBEDDINGS_DB, read_only=not writeable)


def store_embeddings(graph, force=False):
    con = get_connection(writeable=True)
    for model in MODELS:
        if not force and is_embeddings_version_stored(
            con, graph.version_name, model.name
        ):
            print(
                f"Embeddings for {graph.version_name} with model {model.name} already stored."
            )
            continue
        else:
            codes_with_embeddings = get_embedding_from_descriptions(
                graph, model.name, model.args, only_embeddings=True
            )
            print(
                f"Storing embeddings for {graph.version_name} with model {model.name}."
            )
            con.register("df_view", codes_with_embeddings)
            con.execute(f"""
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
    con = get_connection()
    result = con.execute(
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
    SELECT icd_code, title, score, version
    FROM (
        SELECT *, array_cosine_similarity(embedding::float[{dimensions}], ($icd_code_embedding)::float[{dimensions}]) AS score
        FROM icd_embeddings WHERE model = $model AND version = $target_version
    ) sq
    WHERE score IS NOT NULL
    ORDER BY score DESC LIMIT $limit;
    """
    icd_code_embedding = get_embedding(from_version, icd_code, model)
    con = get_connection()
    result = con.execute(
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
    con = get_connection()
    result = con.execute(
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


def get_embedding_from_descriptions(
    graph, model_name, model_args=None, only_embeddings=False
):
    """Get the embeddings for all titles in the graph."""
    if model_args is None:
        model_args = {}

    model = SentenceTransformer(model_name, **model_args)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        titles = []
        codes = []

        progress.add_task(description="Preparing nodes...", total=None)
        for node, data in graph.all_nodes(data=True):
            node_title = data["title"]
            titles.append(node_title)
            codes.append(node)  # like A01

        progress.add_task(description="Getting embeddings...", total=None)
        tensor_embeddings = encode_icd_descriptions(titles, model)
        embeddings = [emb.tolist() for emb in tensor_embeddings]

        progress.add_task(description="Storing embeddings...", total=None)
        for index, (node, data) in enumerate(graph.all_nodes(data=True)):
            data["embeddings"] = embeddings[index]

        if only_embeddings:
            return pl.DataFrame(
                {
                    "embeddings": embeddings,
                    "title": titles,
                    "version": graph.version_name,
                    "code": codes,
                }
            )
        return graph, graph.all_nodes(data=True)


def import_csvs_to_duckdb(csv_pattern: str):
    """Import CSV files from the experiments ran in get_embedding_from_descriptions.

    Usage:
        import_csvs_to_duckdb("artifacts/*.csv")
    """
    con = get_connection(writeable=True)
    table_exists = (
        con.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'matches';"
        ).fetchone()[0]
        > 0
    )

    if table_exists:
        print("Table 'matches' already exists. Skipping import.")
        con.close()
        return

    df = pl.read_csv(csv_pattern)
    con.register("df_view", df)
    con.execute("CREATE TABLE matches AS SELECT * FROM df_view")
    con.close()
    print("Table created and data imported successfully.")


def fetch_matches(
    from_version: str,
    to_version: str,
    node_from_version: str,
    node_to_version: str,
    model: str,
):
    """Fetch matches from the database."""
    con = get_connection()
    result = con.execute(
        """
        SELECT match_type FROM matches
        WHERE from_version = $from_version AND to_version = $to_version
        AND from_icd_code = $from_icd_code AND to_icd_code = $to_icd_code
        AND model = $model;
        """,
        {
            "from_version": from_version,
            "to_version": to_version,
            "model": model,
            "from_icd_code": node_from_version,
            "to_icd_code": node_to_version,
        },
    ).fetchone()
    con.close()
    return result


def fetch_all_matches(
    from_version: str,
    to_version: str,
    model: str,
):
    """Fetch matches from the database."""
    con = get_connection()
    df = con.execute(
        """
        SELECT * FROM matches
        WHERE from_version = $from_version AND to_version = $to_version
        AND model = $model;
        """,
        {
            "from_version": from_version,
            "to_version": to_version,
            "model": model,
        },
    ).pl()
    return df
