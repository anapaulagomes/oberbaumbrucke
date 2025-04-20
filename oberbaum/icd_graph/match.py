import csv

from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("BAAI/bge-m3")


# TODO add it to the graph?
def encode_icd_descriptions(sentences):
    return model.encode(sentences, convert_to_tensor=True)


def semantically_similar(label_a, label_b, threshold=0.8):
    """
    Check if two labels are semantically similar.
    """
    score = None
    if all([label_a, label_b]) is False:
        return False, score
    a_graph_embeddings = encode_icd_descriptions(
        label_a
    )  # this might be slow # TODO warn the user
    another_graph_embeddings = encode_icd_descriptions(label_b)
    hits = util.semantic_search(
        another_graph_embeddings, a_graph_embeddings, score_function=util.dot_score
    )
    for hit in hits:
        # [{'corpus_id': 0, 'score': 0.47366422414779663}]
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
        a_graph.version_name: (f"{a_graph.version_name} ({len(a_graph._graph.nodes)})"),
        another_graph.version_name: (
            f"{another_graph.version_name} ({len(another_graph._graph.nodes)})"
        ),
    }

    for s_node, s_data in a_graph._graph.nodes(data=True):
        potential_b_node = another_graph._graph.nodes.get(s_node, {})
        is_match = False
        match_type = None
        notes = ""
        try:
            if potential_b_node:
                if s_data["name"] == potential_b_node["name"]:  # code's comparison
                    is_similar_description, score = semantically_similar(
                        s_data["description"], potential_b_node["description"]
                    )
                    match_type = "exact_code"
                    is_match = True
                    notes = score
                    # TODO match only codes?
                    if is_similar_description:
                        match_type = "match_code_and_description"
                        is_match = True
                    summary[match_type] = summary.get(match_type, 0) + 1
            else:
                summary["no_match"] = summary.get(match_type, 0) + 1
        except KeyError:  # if the node is not found in the bigger graph
            summary["not_found"] = summary.get(match_type, 0) + 1

        result.append(
            {
                f"{a_graph.version_name}__code": s_data.get("name"),
                f"{another_graph.version_name}__code": potential_b_node.get("name"),
                "is_match": is_match,
                "match_type": match_type,
                "notes": notes,
            }
        )

    return summary, result


def export_matches(matches, output):
    if not matches:
        print("No matches found.")
        return
    with open(output, "w", newline="") as csvfile:
        fieldnames = matches[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(matches)
