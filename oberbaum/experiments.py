import csv
import re
from datetime import datetime
from pathlib import Path

import polars as pl
from rich.progress import track

from oberbaum.embeddings import get_semantic_score_for_same_code
from oberbaum.models import get_model_object


def from_slurm_logs_to_df(logs_dir):
    """Convert logs to a dataframe for later threshold analysis."""
    data = []
    version_pattern = r"(icd-10-who|icd-10-gm|icd-10-cm|cid-10-bra): Nodes: \d+"

    for log_file in Path(logs_dir).glob("*.out"):
        content = log_file.read_text()
        model_sections = re.split(r"Using model: ", content)

        for model_section in model_sections:
            if not model_section.strip() or "Fetching all models..." in model_section:
                continue

            model_and_threshold_match = re.search(
                r"(\S+) with \n?threshold: (\S+)", model_section
            )
            if not model_and_threshold_match:
                continue

            model = model_and_threshold_match.group(1)
            threshold = model_and_threshold_match.group(2)

            summaries = re.split(r"Match Summary:", model_section)

            for summary in summaries[1:]:
                versions = re.findall(version_pattern, summary)
                if len(versions) == 1:
                    from_version, to_version = versions[0], versions[0]
                else:  # assume len == 2
                    from_version, to_version = versions

                match_code_match = re.search(r"match_code: (\d+)", summary)
                match_code_and_description_match = re.search(
                    r"match_code_and_description: (\d+)", summary
                )
                uphill_match_match = re.search(r"uphill_match: (\d+)", summary)
                not_found_match = re.search(r"not_found: (\d+)", summary)
                results_file_match = re.search(
                    r"Matches exported to\s+([\s\S]+?\.csv)\n", summary
                )
                if results_file_match:
                    results_file = results_file_match.group(1).replace("\n", "")
                else:
                    results_file = None

                data.append(
                    {
                        "model": model,
                        "threshold": threshold,
                        "from_version": from_version,
                        "to_version": to_version,
                        "match_code": int(match_code_match.group(1))
                        if match_code_match
                        else 0,
                        "match_code_and_description": int(
                            match_code_and_description_match.group(1)
                        )
                        if match_code_and_description_match
                        else 0,
                        "uphill_match": int(uphill_match_match.group(1))
                        if uphill_match_match
                        else 0,
                        "not_found": int(not_found_match.group(1))
                        if not_found_match
                        else 0,
                        "results_file": results_file,
                        "log_file": log_file.name,
                    }
                )

    return pl.DataFrame(data)


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
