import csv


def match_codes(a_graph, another_graph):
    result = []
    summary = {}

    if len(a_graph._graph.nodes) > len(another_graph._graph.nodes):
        bigger_graph = a_graph
        smaller_graph = another_graph
    else:
        bigger_graph = another_graph
        smaller_graph = a_graph

    summary["smaller_graph"] = (
        f"{smaller_graph.version_name} ({len(smaller_graph._graph.nodes)})"
    )
    summary["bigger_graph"] = (
        f"{smaller_graph.version_name} ({len(bigger_graph._graph.nodes)})"
    )

    for s_node, s_data in smaller_graph._graph.nodes(data=True):
        potential_b_node = bigger_graph._graph.nodes.get(s_node, {})
        is_match = False
        match_type = None
        try:
            if potential_b_node:
                if s_data["name"] == potential_b_node["name"]:  # code's comparison
                    similar_description = semantically_similar(
                        s_data["description"], potential_b_node["description"]
                    )
                    match_type = "exact_code"
                    is_match = True
                    if similar_description:  # TODO will become one
                        match_type = "match_code_and_description"
                        is_match = True
                    summary[match_type] = summary.get(match_type, 0) + 1
            else:
                summary["no_match"] = summary.get(match_type, 0) + 1
        except KeyError:  # if the node is not found in the bigger graph
            summary["not_found"] = summary.get(match_type, 0) + 1

        result.append(
            {
                f"{smaller_graph.version_name}__code": s_data.get("name"),
                f"{bigger_graph.version_name}__code": potential_b_node.get("name"),
                "is_match": is_match,
                "match_type": match_type,
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


def semantically_similar(label_a, label_b, threshold=0.8):
    """
    Check if two labels are semantically similar.
    """
    # TODO
    return len(label_a) == len(label_b)
