import marimo

__generated_with = "0.16.4"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import plotly.express as px
    import polars as pl

    from oberbaum.icd_graph.embeddings import get_connection
    return get_connection, mo, pl, px


@app.cell
def _(get_connection):
    con = get_connection()
    return (con,)


@app.cell
def _():
    model_name = "jinaai/jina-embeddings-v3"
    return (model_name,)


@app.cell
def _(mo):
    mo.md(r"""# Validation""")
    return


@app.cell
def _():
    OMOP_NAMING_MAPPING = {
        "icd-10-who": "ICD10",
        "icd-10-cm": "ICD10CM",
        "icd-10-gm": "ICD10GM",
    }

    COLOR_BY_VERSION = {
        OMOP_NAMING_MAPPING.get("icd-10-who"): "deepskyblue",
        OMOP_NAMING_MAPPING.get("icd-10-cm"): "red",
        OMOP_NAMING_MAPPING.get("icd-10-gm"): "gold",
        "cid-10-bra": "green",
    }
    return COLOR_BY_VERSION, OMOP_NAMING_MAPPING


@app.cell
def _(pl):
    df_omop = pl.read_csv(
        "data/mappings/omop_mappings_select_cr_concept_id_1_c1_vocabulary_id_c1_concept_cod_202507061258.csv",
        new_columns=["concept_id", "vocabulary_id", "concept_code", "concept_name", "relationship_id", "concept_id_2", "vocabulary_id_2", "concept_code_2", "concept_name_2"],
    )
    df_omop = df_omop.with_columns(pl.col("concept_code").str.replace(".", "", literal=True))
    df_omop
    return (df_omop,)


@app.cell
def _(COLOR_BY_VERSION, df_omop, pl, px):
    _grouped_df_descriptions = df_omop.select(pl.col("vocabulary_id"), pl.col("concept_code").str.len_chars().alias("code_length"))
    _fig = px.box(
        _grouped_df_descriptions,
        y="code_length",
        x="vocabulary_id",
        color="vocabulary_id",
        color_discrete_map=COLOR_BY_VERSION,
        title="Code lenght by versions found in OMOP vocabularies"
    )
    _fig
    return


@app.cell
def _(df_omop, pl):
    df_omop.filter(pl.col("concept_code").str.len_chars() == 5).group_by("vocabulary_id", "concept_code").agg(pl.col("vocabulary_id").len().alias("count")).filter(pl.col("count") > 2)
    return


@app.cell
def _(df_omop, pl):
    df_omop.filter(pl.col("concept_code_2") == 10685111000119102)
    return


@app.cell
def _(con, model_name, pl):
    df_matches = con.execute("SELECT * FROM matches;").pl().filter(pl.col("model").eq(model_name))
    df_matches
    return (df_matches,)


@app.cell
def _(mo):
    mo.md(r"""## Validation with the number of vocabularies found""")
    return


@app.cell
def _(OMOP_NAMING_MAPPING, df_omop, pl):
    def was_two_vocab_found(vocabulary, icd_code, vocabulary_2="icd-10-who", show_results_table=False):
        result = df_omop.filter(
            pl.col("vocabulary_id").is_in([
                OMOP_NAMING_MAPPING.get(vocabulary_2),
                OMOP_NAMING_MAPPING.get(vocabulary)
            ]) & pl.col("concept_code").eq(icd_code)
        )
        if show_results_table:
            print(result)
        return result.select(pl.col("vocabulary_id").n_unique()).item() == 2
    return (was_two_vocab_found,)


@app.cell
def _(OMOP_NAMING_MAPPING, mapping_df, pl):
    def found_in_mapping_table(vocabulary, icd_code, vocabulary_2="icd-10-who", show_results_table=False):
        result = mapping_df.filter(pl.col("vocabulary_id").eq(OMOP_NAMING_MAPPING.get(vocabulary)), pl.col("concept_code").eq(icd_code))
        if show_results_table:
            print(result)
        return len(result) > 0
    return (found_in_mapping_table,)


@app.cell
def _(was_two_vocab_found):
    was_two_vocab_found("icd-10-gm", "Z98890", show_results_table=True)
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    ## Mappings table

    Examples:

    * T463X2 (4 concept codes)
    """
    )
    return


@app.cell
def _(df_omop, pl):
    source_df = df_omop.filter(pl.col("vocabulary_id").is_in(["ICD10CM", "ICD10GM"]))
    target_df = df_omop.filter(pl.col("vocabulary_id").eq("ICD10"))

    mapping_df = source_df.join(target_df, on="concept_code_2", suffix="_icd10who")  # how = inner; merge on snomed code
    mapping_df
    return (mapping_df,)


@app.cell
def _(mapping_df, pl):
    mapping_df.filter(pl.col("concept_code_2").eq(79974007))
    return


@app.cell
def _(found_in_mapping_table, was_two_vocab_found):
    def is_a_match(vocabulary, icd_code, vocabulary_2="icd-10-who", show_results_table=False, strategy="vocabs"):
        if strategy == "vocabs":
            return was_two_vocab_found(vocabulary, icd_code, vocabulary_2="icd-10-who", show_results_table=False)
        else:
            return found_in_mapping_table(vocabulary, icd_code, vocabulary_2="icd-10-who", show_results_table=False)
    return (is_a_match,)


@app.cell
def _(is_a_match):
    examples_gm_cm = [
        ("C88", True, True),  # 3-char
        ("J101", True, True),  # 4-char
        ("M4693", True, True),  # 5-char
        ("Z98890", False, True),  # 6-char
        ("S99129G", False, True),  # 7-char
        ("1", False, False),  # chapter
        ("A00-A09", False, False),  # block
    ]

    print("Validation tests from icd-10-gm...")
    for icd_code, expected_gm, _ in examples_gm_cm:
        result = is_a_match("icd-10-gm", icd_code, strategy="table")
        assert result is expected_gm, f"Expected {expected_gm} for {icd_code}, but got {result}"
    print("OK")

    print("Validation tests from icd-10-cm...")
    for icd_code, _, expected_cm in examples_gm_cm:
        result = is_a_match("icd-10-cm", icd_code, strategy="table")
        assert result is expected_cm, f"Expected {expected_cm} for {icd_code}, but got {result}"
    print("OK")
    return


@app.cell
def _(mo):
    mo.md(r"""## Check mapping for code and description""")
    return


@app.cell
def _(OMOP_NAMING_MAPPING, df_matches, is_a_match, pl):
    def get_results_from_matches(match_type='match_code_and_description', threshold=0.7):
        results = {}
        for version in OMOP_NAMING_MAPPING:
            results[version] = []
            _filtered = df_matches.filter(pl.col("from_version").eq(version), pl.col("match_type").eq(match_type), pl.col("threshold").eq(threshold))
            for match in _filtered.iter_rows(named=True):
                results[match['from_version']].append(
                    is_a_match(match['from_version'], match['from_icd_code']) and is_a_match(match['from_version'], match['to_icd_code'])
                )
        return results
    return (get_results_from_matches,)


@app.function
def match_validation_results(results):
    final_result = {}
    for version_name, list_of_results in results.items():
        total = len(list_of_results)
        did_match = list_of_results.count(True)  # true positive / true negative
        final_result.setdefault(version_name, {})
        final_result[version_name]["true"] = did_match
        try:
            perc_did_match = (did_match*100)/total
        except ZeroDivisionError:
            print(f"perc_did_match ZeroDivisionError: {did_match}/{total}")
            perc_did_match = 0.0
        did_not_match = list_of_results.count(False)  # false positive / false negative
        final_result[version_name]["false"] = did_not_match
        try:
            perc_did_not_match = (did_not_match*100)/total
        except ZeroDivisionError:
            print(f"perc_did_match ZeroDivisionError: {did_not_match}/{total}")
            perc_did_not_match = 0.0
        print(f"{version_name}: {did_match} ({perc_did_match:.2f} %) matched, {did_not_match} ({perc_did_not_match:.2f} %) did not match out of {total} total checks.")
    return final_result


@app.cell
def _(df_matches, get_results_from_matches):
    def calculate_validation_results(match_type):
        validation_results = {}
        for threshold in df_matches["threshold"].unique():
            print(threshold)
            results_match_code_and_description = get_results_from_matches(match_type=match_type, threshold=threshold)
            positive = match_validation_results(results_match_code_and_description)
            validation_results[threshold] = {
                "results_match_code_and_description": results_match_code_and_description,
                "positive": positive
            }
        return validation_results
    return (calculate_validation_results,)


@app.cell
def _(calculate_validation_results):
    positive_results = calculate_validation_results('match_code_and_description')
    return


@app.cell
def _(calculate_validation_results):
    negative_results = calculate_validation_results('not_found')
    return


@app.cell
def _(mo):
    mo.md(
        r"""

    * True Positive (TP): matched by our approach, should be in the found list
    * False Positive (FP): matched by our approached, but it was in the not found list
    * True Negative (TN): not matched by our approach and it was in the excluded list
    * False Negative (FN): not matched by our approach but should be in the found list

    """
    )
    return


@app.cell
def _(negative, positive):
    # positive = {
    #   "icd-10-who": {
    #     "true": 0,
    #     "false": 62530
    #   },
    #   "icd-10-cm": {
    #     "true": 47543,
    #     "false": 1627
    #   },
    #   "icd-10-gm": {
    #     "true": 44299,
    #     "false": 1632
    #   }
    # }

    # negative = {
    #   "icd-10-who": {
    #     "true": 0,
    #     "false": 0
    #   },
    #   "icd-10-cm": {
    #     "true": 0,
    #     "false": 96720
    #   },
    #   "icd-10-gm": {
    #     "true": 0,
    #     "false": 3490
    #   }
    # }

    def calculate_sensitivity(version_name):
        try:
            return positive[version_name]["true"]/(positive[version_name]["true"]+negative[version_name]["false"])
        except ZeroDivisionError:
            print(f"ZeroDivisionError: {version_name}")


    def calculate_specificity(version_name):
        try:
            return positive[version_name]["false"]/(positive[version_name]["false"]+negative[version_name]["true"])
        except ZeroDivisionError:
            print(f"ZeroDivisionError: {version_name}")

    def calculate_f_score(version_name):
        try:
            return (2*positive[version_name]["true"])/((2*positive[version_name]["true"])+negative[version_name]["true"]+negative[version_name]["false"])
        except ZeroDivisionError:
            print(f"ZeroDivisionError: {version_name}")
    return calculate_f_score, calculate_sensitivity, calculate_specificity


@app.cell
def _(
    calculate_f_score,
    calculate_sensitivity,
    calculate_specificity,
    positive,
):
    for version_name in positive.keys():
        sensitivity = calculate_sensitivity(version_name)
        specificity = calculate_specificity(version_name)
        f_score = calculate_f_score(version_name)
        print(f'[{version_name}] Sensitivity: {sensitivity} Specificity: {specificity} f-score: {f_score}')
    return


if __name__ == "__main__":
    app.run()
