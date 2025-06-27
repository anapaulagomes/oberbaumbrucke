import csv
from datetime import datetime

import polars as pl
from rich.progress import Progress, SpinnerColumn, TextColumn, track
from sentence_transformers import SentenceTransformer, util


def encode_icd_descriptions(sentences, model):
    return model.encode(sentences)


def semantically_similar(a_graph_embeddings, another_graph_embeddings, threshold=0.7):
    """
    Check if two labels are semantically similar.
    """
    score = None
    hits = util.semantic_search(
        another_graph_embeddings,
        a_graph_embeddings,
        score_function=util.cos_sim,
        top_k=1,
    )
    for hit in hits:
        # output: [{'corpus_id': 0, 'score': 0.47366422414779663}]
        score = hit[0]["score"]
        if score > threshold:
            return True, score
    return False, score


def match_codes(a_graph, another_graph, model_name, threshold=0.7):
    """
    Compare two graphs and find matches based on the code and description.
    :param threshold: threshold for semantic similarity.
    :param model_name: model name following HuggingFace / SentenceTransformer convention.
    :param a_graph: a graph in which we want to find matches.
    :param another_graph: a graph with the match options available.
    :return:
    """
    model = SentenceTransformer(model_name)
    result = []

    a_graph, a_graph_codes_with_embeddings = set_embeddings_from_descriptions(
        a_graph, model
    )
    another_graph, another_graph_codes_with_embeddings = (
        set_embeddings_from_descriptions(another_graph, model)
    )

    a_graph_codes = {node: data for node, data in a_graph_codes_with_embeddings}
    another_graph_codes = {
        node: data for node, data in another_graph_codes_with_embeddings
    }

    summary = {
        a_graph.version_name: f"Nodes: {len(a_graph._graph.nodes)} / Codes: {len(a_graph_codes)}",
        another_graph.version_name: f"Nodes: {len(another_graph._graph.nodes)} / Codes: {len(another_graph_codes)}",
    }

    for a_graph_node, a_graph_data in track(
        a_graph_codes.items(), description="Comparing versions..."
    ):
        is_match = False
        score = None

        found_node = another_graph_codes.get(a_graph_node, {})
        if found_node:  # if both are codes
            if a_graph_data["name"] == found_node["name"]:  # code's comparison
                is_similar_description, score = semantically_similar(
                    a_graph_data["embeddings"], found_node["embeddings"], threshold
                )
                match_stage = "match_code"
                if is_similar_description:
                    match_stage = "match_code_and_description"
                    is_match = True
            else:
                match_stage = "different_code"
        else:
            # if the node is not found in the other graph - as a code
            match_stage = "not_found"
        summary[match_stage] = summary.get(match_stage, 0) + 1

        result.append(
            {
                f"{a_graph.version_name}__code": a_graph_data.get("name"),
                f"{another_graph.version_name}__code": found_node.get("name"),
                "is_match": is_match,
                "match_type": match_stage,
                "description_score": score,
                f"{a_graph.version_name}__description": a_graph_data.get("description"),
                f"{another_graph.version_name}__description": found_node.get(
                    "description"
                ),
                "model": model_name,
                "threshold": threshold,
                "created_at": str(datetime.now()),
            }
        )

    return summary, result


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
        embeddings = encode_icd_descriptions(descriptions, model)

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


def export_matches(matches, output):
    if not matches:
        print("No matches found.")
        return
    with open(output, "w", newline="") as csvfile:
        fieldnames = matches[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(matches)
