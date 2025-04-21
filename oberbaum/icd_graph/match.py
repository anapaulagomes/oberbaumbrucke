import csv

from rich.progress import Progress, SpinnerColumn, TextColumn, track
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("BAAI/bge-m3")


def encode_icd_descriptions(sentences):
    return model.encode(sentences, convert_to_tensor=True)


def semantically_similar(a_graph_embeddings, another_graph_embeddings, threshold=0.7):
    """
    Check if two labels are semantically similar.
    """
    score = None
    hits = util.semantic_search(
        another_graph_embeddings, a_graph_embeddings, score_function=util.dot_score
    )
    for hit in hits:
        # output: [{'corpus_id': 0, 'score': 0.47366422414779663}]
        score = hit[0]["score"]
        if score > threshold:
            return True, score
    return False, score


def match_codes(a_graph, another_graph):
    """
    Compare two graphs and find matches based on the code and description.
    :param a_graph: a graph in which we want to find matches.
    :param another_graph: a graph with the match options available.
    :return:
    """
    result = []
    summary = {
        a_graph.version_name: len(a_graph._graph.nodes),
        another_graph.version_name: len(another_graph._graph.nodes),
    }

    a_graph = set_embeddings_from_descriptions(a_graph)
    another_graph = set_embeddings_from_descriptions(another_graph)

    for a_graph_node, a_graph_data in track(
        a_graph._graph.nodes(data=True), description="Comparing versions..."
    ):
        found_node = another_graph._graph.nodes.get(a_graph_node, {})
        is_match = False
        match_type = None
        score = None
        try:
            if found_node:
                if a_graph_data["name"] == found_node["name"]:  # code's comparison
                    is_similar_description, score = semantically_similar(
                        a_graph_data["embeddings"], found_node["embeddings"]
                    )
                    match_type = "exact_code"
                    if is_similar_description:
                        match_type = "match_code_and_description"
                        is_match = True
                else:
                    match_type = "different_code"
                summary[match_type] = summary.get(match_type, 0) + 1
            else:
                summary["missing_data"] = summary.get(match_type, 0) + 1
        except KeyError:  # if the node is not found in the bigger graph
            summary["not_found"] = summary.get(match_type, 0) + 1

        result.append(
            {
                f"{a_graph.version_name}__code": a_graph_data.get("name"),
                f"{another_graph.version_name}__code": found_node.get("name"),
                "is_match": is_match,
                "match_type": match_type,
                "description_score": score,
            }
        )

    return summary, result


def set_embeddings_from_descriptions(graph):
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
        embeddings = encode_icd_descriptions(descriptions)

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
