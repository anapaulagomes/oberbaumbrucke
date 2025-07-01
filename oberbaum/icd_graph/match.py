import csv
from datetime import datetime

from rich.progress import track

from oberbaum.icd_graph.embeddings import get_semantic_score_for_same_code
from oberbaum.icd_graph.models import get_model_object


def match_codes(from_graph, to_graph, model_name, threshold=0.7):
    """
    Compare two graphs and find matches based on the code and description.
    :param threshold: threshold for semantic similarity.
    :param model_name: model object.
    :param from_graph: a graph in which we want to find matches.
    :param to_graph: a graph with the match options available.
    :return:
    """
    model = get_model_object(model_name)
    result = {}
    summary = {
        from_graph.version_name: f"Nodes: {len(from_graph._graph.nodes) - 1}",  # -1 to exclude the root node
        to_graph.version_name: f"Nodes: {len(to_graph._graph.nodes) - 1}",
    }
    not_found_nodes = []

    for a_graph_node, a_graph_data in track(
        from_graph._graph.nodes(data=True), description="Comparing versions..."
    ):
        is_match = False

        if a_graph_node == "root":
            continue

        found_node = to_graph.get(a_graph_node) or {}
        notes = ""
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

            if (a_graph_data.get("title") and found_node.get("title")) and not score:
                print(
                    f"Score not found: {a_graph_data.get('title')} - {found_node.get('title')}"
                )

            result[a_graph_node] = {
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
                "notes": notes,
            }
            summary[match_stage] = summary.get(match_stage, 0) + 1
        else:
            not_found_nodes.append(a_graph_node)

    # attempt to match not found nodes using uphill mapping strategy
    uphill_results = {}
    for node_not_found in not_found_nodes:
        match_stage = None
        predecessors = from_graph._graph.predecessors(node_not_found)
        for level, predecessor in enumerate(predecessors, start=1):
            if result.get(predecessor):
                match_stage = "uphill_match"
                copied_result = result.get(predecessor).copy()
                copied_result.update(
                    {
                        "from_icd_code": node_not_found,  # uphill match
                        "is_match": True,
                        "match_type": match_stage,
                        "created_at": str(datetime.now()),
                        "notes": "Uphill match found at level " + str(level),
                    }
                )
                uphill_results[node_not_found] = (
                    copied_result  # make sure that we don't have uphill chain
                )
                break
        if not uphill_results.get(node_not_found):  # no uphill match found
            match_stage = "not_found"
            result[node_not_found] = {
                "from_version": from_graph.version_name,
                "to_version": to_graph.version_name,
                "from_icd_code": node_not_found,
                "to_icd_code": None,
                "is_match": False,
                "match_type": match_stage,
                "title_score": None,
                "from_title": from_graph.get(node_not_found).get("title"),
                "to_title": None,
                "model": model.name,
                "threshold": threshold,
                "created_at": str(datetime.now()),
                "notes": None,
            }
        summary[match_stage] = summary.get(match_stage, 0) + 1
    result.update(uphill_results)

    return summary, list(result.values())


def export_matches(matches, output):
    if not matches:
        print("No matches found.")
        return
    with open(output, "w", newline="") as csvfile:
        fieldnames = matches[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(matches)
