import csv

from rich.progress import Progress, SpinnerColumn, TextColumn, track
from sentence_transformers import SentenceTransformer, util


def encode_icd_descriptions(sentences, model):
    return model.encode(sentences, convert_to_tensor=True)


def semantically_similar(a_graph_embeddings, another_graph_embeddings, threshold=0.7):
    """
    Check if two labels are semantically similar.
    """
    score = None
    hits = util.semantic_search(  # TODO use top_k = 1
        another_graph_embeddings, a_graph_embeddings, score_function=util.dot_score
    )
    for hit in hits:
        # output: [{'corpus_id': 0, 'score': 0.47366422414779663}]
        score = hit[0]["score"]
        if score > threshold:
            return True, score
    return False, score


def match_codes(a_graph, another_graph, model_name):
    """
    Compare two graphs and find matches based on the code and description.
    :param model_name: model name following HuggingFace / SentenceTransformer convention.
    :param a_graph: a graph in which we want to find matches.
    :param another_graph: a graph with the match options available.
    :return:
    """
    model = SentenceTransformer(model_name)
    result = []
    summary = {
        a_graph.version_name: len(a_graph._graph.nodes),
        another_graph.version_name: len(another_graph._graph.nodes),
    }

    a_graph = set_embeddings_from_descriptions(a_graph, model)
    another_graph = set_embeddings_from_descriptions(another_graph, model)

    for a_graph_node, a_graph_data in track(
        a_graph._graph.nodes(data=True), description="Comparing versions..."
    ):
        is_match = False
        score = None
        found_node = {}
        if a_graph_node == a_graph._root_node:
            continue

        try:
            found_node = another_graph._graph.nodes[a_graph_node]
        except KeyError:  # if the node is not found in the other graph
            match_stage = "not_found"
        else:
            if found_node:
                if a_graph_data["name"] == found_node["name"]:  # code's comparison
                    is_similar_description, score = semantically_similar(
                        a_graph_data["embeddings"], found_node["embeddings"]
                    )
                    match_stage = "exact_code"
                    if is_similar_description:
                        match_stage = "match_code_and_description"
                        is_match = True
                else:
                    match_stage = "different_code"
            else:
                match_stage = "missing_data"
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
            }
        )

    return summary, result


def set_embeddings_from_descriptions(graph, model):
    """Get the embeddings for all descriptions in the graph."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        descriptions = []

        progress.add_task(description="Preparing nodes...", total=None)
        for node, data in graph._graph.nodes(data=True):
            descriptions.append(data.get("description", ""))

        progress.add_task(description="Getting embeddings...", total=None)
        embeddings = encode_icd_descriptions(descriptions, model)

        progress.add_task(description="Storing embeddings...", total=None)
        for index, (node, data) in enumerate(graph._graph.nodes(data=True)):
            data["embeddings"] = embeddings[index]
        return graph


def export_matches(matches, output):
    if not matches:
        print("No matches found.")
        return
    with open(output, "w", newline="") as csvfile:
        fieldnames = matches[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(matches)
