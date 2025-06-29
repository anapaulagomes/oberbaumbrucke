from dataclasses import dataclass, field

import duckdb

from oberbaum.cli import get_graph
from oberbaum.icd_graph.match import set_embeddings_from_descriptions

conn = duckdb.connect("icd10_embeddings.db")

# Semantic Textual Similarity
@dataclass
class STSModel:
    name: str
    args: dict = field(default_factory=dict)


MODELS = [
    STSModel(name="BAAI/bge-m3"),
    STSModel(name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
    STSModel(name="sentence-transformers/LaBSE"),
    STSModel(name="sentence-transformers/distiluse-base-multilingual-cased-v1"),
    STSModel(name="jinaai/jina-embeddings-v3",args={"trust_remote_code": True})
]


def all_graphs():
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
                print(f"Embeddings for {graph.version_name} with model {model.name} already stored.")
                continue
            else:
                codes_with_embeddings = set_embeddings_from_descriptions(graph, model.name, model.args, only_embeddings=True)
                print(f"Storing embeddings for {graph.version_name} with model {model.name}.")
                conn.register("df_view", codes_with_embeddings)
                conn.execute(f"""
                    INSERT INTO icd_embeddings (version, icd_code, title, embedding, model)
                    SELECT version, code, title, embeddings, '{model.name}' AS model FROM df_view
                """)


def create_table_if_not_exists(con):
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
    create_table_if_not_exists(con)
    result = con.execute(
        "SELECT EXISTS(SELECT * FROM icd_embeddings WHERE version=? AND model=?)",
        [version, model],
    ).fetchone()
    if result:
        return result[0]
    return False


store_embeddings(conn)
