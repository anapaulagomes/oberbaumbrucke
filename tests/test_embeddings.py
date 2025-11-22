import polars as pl
from sentence_transformers import SentenceTransformer

from oberbaum.cli import get_graph
from oberbaum.embeddings import get_embedding_from_titles
from oberbaum.models import STSModel


class TestGetEmbeddingFromTitles:
    def test_embedding_from_titles(self, subtests):
        model_metadata = STSModel(name="BAAI/bge-m3", dimensions=1024)
        model = SentenceTransformer(model_metadata.name, **model_metadata.args)
        versions = [
            ("cid-10-bra", "tests/fixtures/subgraph-cid-10-bra-B180.gml"),
            (
                "icd-10-who",
                "tests/fixtures/subgraph-icd-10-who-C570-include-children.gml",
            ),
            ("icd-10-gm", "tests/fixtures/subgraph-icd-10-gm-O47-include-children.gml"),
            ("icd-10-cm", "tests/fixtures/subgraph-icd-10-cm-W5522.gml"),
        ]

        for version_name, gml_filepath in versions:
            with subtests.test(version_name=version_name):
                graph = get_graph(version_name, gml_filepath=gml_filepath)
                codes_with_embeddings = get_embedding_from_titles(graph, model)

                for node, data in graph.all_nodes(data=True):
                    result = codes_with_embeddings.filter(pl.col("code").eq(node))
                    assert result.shape[0] == 1
                    assert result["version"].item() == graph.version_name
                    assert result["title"].item() == data["title"]

                    embeddings = result["embeddings"].item()
                    assert embeddings.shape[0] == model_metadata.dimensions
                    assert isinstance(embeddings.dtype, pl.Float64)
