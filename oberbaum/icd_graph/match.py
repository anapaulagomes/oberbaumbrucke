import csv
from datetime import datetime

from oberbaum.icd_graph.embeddings import (
    get_semantic_score_for_same_code,
    similar_icd_codes,
)
from oberbaum.icd_graph.models import get_model_object

# from rich.progress import track


def match_codes(from_graph, to_graph, model_name, threshold=0.7):
    """
    Compare two graphs and find matches based on the code and description.
    :param threshold: threshold for semantic similarity.
    :param model: model object.
    :param from_graph: a graph in which we want to find matches.
    :param to_graph: a graph with the match options available.
    :return:
    """
    model = get_model_object(model_name)
    result = []
    summary = {
        from_graph.version_name: f"Nodes: {len(from_graph._graph.nodes)}",
        to_graph.version_name: f"Nodes: {len(to_graph._graph.nodes)}",
    }

    # for a_graph_node, a_graph_data in track(
    #     from_graph._graph.nodes(data=True), description="Comparing versions..."
    # ):
    for a_graph_node, a_graph_data in from_graph._graph.nodes(data=True):
        is_match = False
        score = None

        if a_graph_node == "root":
            continue

        found_node = to_graph.get(a_graph_node) or {}
        if found_node:
            # same as comparing the names
            match_stage = "match_code"

            score = get_semantic_score_for_same_code(
                from_graph.version_name,
                to_graph.version_name,
                a_graph_data["name"],
                model.name,
                model.dimensions,
            )
            if score and score >= threshold:
                match_stage = "match_code_and_description"
                is_match = True

                # TODO
                # topological match
                # match_stage = "perfect_match"
        else:
            # TODO uphill mapping
            potential_codes = similar_icd_codes(
                from_graph.version_name,
                to_graph.version_name,
                a_graph_data["name"],
                model.name,
                model.dimensions,
            )
            print(a_graph_data["name"], a_graph_data["title"], potential_codes)
            # TODO get siblings of the node
            # found_node
            # TODO intersection of the codes; if found, get the parent node in the other graph: to_graph

            # import ipdb;
            # ipdb.set_trace()

            # if the node is not found in the other graph
            match_stage = "not_found"
        summary[match_stage] = summary.get(match_stage, 0) + 1

        result.append(
            {
                "from_version": from_graph.version_name,
                "to_version": to_graph.version_name,
                "from_icd_code": a_graph_data.get("name", None),
                "to_icd_code": found_node.get("name"),
                "is_match": is_match,
                "match_type": match_stage,
                "title_score": score,
                "from_title": a_graph_data.get("title"),
                "to_title": found_node.get("title"),
                "model": model.name,
                "threshold": threshold,
                "created_at": str(datetime.now()),
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
