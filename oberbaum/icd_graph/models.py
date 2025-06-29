from dataclasses import dataclass, field


@dataclass
class STSModel:
    """Semantic Textual Similarity (STS) model representation."""

    name: str
    dimensions: int
    args: dict = field(default_factory=dict)


MODELS = [
    STSModel(name="BAAI/bge-m3", dimensions=1024),
    STSModel(
        name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        dimensions=384,
    ),
    STSModel(name="sentence-transformers/LaBSE", dimensions=768),
    STSModel(
        name="sentence-transformers/distiluse-base-multilingual-cased-v1",
        dimensions=512,
    ),
    STSModel(
        name="jinaai/jina-embeddings-v3",
        dimensions=1024,
        args={"trust_remote_code": True},
    ),
]


def get_model_object(model_name: str) -> STSModel:
    """Retrieve a model by its name."""
    for model in MODELS:
        if model.name == model_name:
            return model
    raise ValueError(f"Model {model_name} not found.")
