import marimo

__generated_with = "0.13.0"
app = marimo.App(width="medium")


@app.cell
def _():
    from sentence_transformers import SentenceTransformer, util

    return SentenceTransformer, util


@app.cell
def _(SentenceTransformer):
    model = SentenceTransformer("rufimelo/Legal-BERTimbau-sts-large-ma-v3")
    # sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    # BAAI/bge-m3
    # rufimelo/Legal-BERTimbau-sts-large-ma-v3 performance ok but slow (pt-br <> eng)
    # sentence-transformers/LaBSE
    return (model,)


@app.function
def encode_icd_descriptions(sentences, model):
    return model.encode(sentences, convert_to_tensor=True)


@app.cell
def _(model):
    another_graph_embeddings = encode_icd_descriptions(
        ["Capítulo II - Neoplasias [tumores]"], model
    )
    a_graph_embeddings = encode_icd_descriptions(["Neoplasms"], model)
    return a_graph_embeddings, another_graph_embeddings


@app.cell
def _(a_graph_embeddings, another_graph_embeddings, util):
    hits = util.semantic_search(  # TODO use top_k = 1
        another_graph_embeddings,
        a_graph_embeddings,
        # score_function=util.dot_score,
        top_k=1,
    )
    for hit in hits:
        # output: [{'corpus_id': 0, 'score': 0.47366422414779663}] 0-1 score
        # [{'corpus_id': 0, 'score': 5.1750688552856445}] 1.035013771057129 0-5 score
        # print(hit) # convert 0-5 scores to 0-1 scores
        score = hit[0]["score"]  # / 5.0
        print(hit, score)
    return


if __name__ == "__main__":
    app.run()
