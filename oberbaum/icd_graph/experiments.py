import re
from pathlib import Path

import polars as pl


def from_logs_to_df(logs_dir):
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
