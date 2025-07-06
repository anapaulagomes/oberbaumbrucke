import marimo

__generated_with = "0.14.9"
app = marimo.App(width="full")


@app.cell
def _():
    import duckdb
    import marimo as mo
    import plotly.express as px
    import polars as pl

    from oberbaum.icd_graph.embeddings import get_connection
    return get_connection, pl, px


@app.cell
def _(get_connection):
    con = get_connection()
    return (con,)


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
        # "cid-10-bra-2008": "green",
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
    _fig = px.box(_grouped_df_descriptions, y="code_length", x="vocabulary_id", color="vocabulary_id", color_discrete_map=COLOR_BY_VERSION)
    _fig
    return


@app.cell
def _(df_omop, pl):
    # df_omop.filter(pl.col("concept_code_2") == 79974007)
    # df_omop.group_by("concept_code_2").agg(pl.col("vocabulary_id"), pl.col("concept_code"))
    # df_omop.filter(pl.col("vocabulary_id").eq(OMOP_NAMING_MAPPING.get("icd-10-who")), pl.col("concept_code").eq("J10"))
    # df_omop.filter(pl.col("vocabulary_id").eq(OMOP_NAMING_MAPPING.get("icd-10-cm")), pl.col("concept_code").eq("J10"))

    df_omop.filter(pl.col("concept_code").str.len_chars() == 5).group_by("vocabulary_id", "concept_code").agg(pl.col("vocabulary_id").len().alias("count")).filter(pl.col("count") > 2)
    return


@app.cell
def _(OMOP_NAMING_MAPPING, df_omop, pl):
    def is_a_match(vocabulary, icd_code, vocabulary_2="icd-10-who", show_results_table=False):
        # print(OMOP_NAMING_MAPPING.get(vocabulary_2), OMOP_NAMING_MAPPING.get(vocabulary), icd_code)
        result = df_omop.filter(
            pl.col("vocabulary_id").is_in([
                OMOP_NAMING_MAPPING.get(vocabulary_2),
                OMOP_NAMING_MAPPING.get(vocabulary)
            ]) & pl.col("concept_code").eq(icd_code)
        )
        if show_results_table:
            print(result)
        return result.select(pl.col("vocabulary_id").n_unique()).item() == 2

    return (is_a_match,)


@app.cell
def _(is_a_match):
    examples = [
        ("C88", True),  # 3-char
        ("J101", True),  # 4-char
        ("M4693", True),  # 5-char
        ("Z98890", False),  # 6-char
        ("S99129G", False),  # 7-char
        ("1", False),  # chapter
        ("A00-A09", False),  # block
    ]

    for _version in ["icd-10-gm", "icd-10-cm"]:
        for icd_code, expected in examples:
            result = is_a_match(_version, icd_code)
            assert result is expected, f"Expected {expected} for {icd_code}, but got {result}"

    return


@app.cell
def _(df_omop, pl):
    df_omop.filter(pl.col("concept_code_2") == 10685111000119102)
    return


@app.cell
def _(con):
    one_match = con.execute("SELECT * FROM matches;").fetchone()
    one_match
    return


@app.cell
def _(con):
    df_matches = con.execute("SELECT * FROM matches;").pl()
    df_matches
    return (df_matches,)


@app.cell
def _(OMOP_NAMING_MAPPING, df_matches, is_a_match, pl):
    def get_results_from_matches(match_type='match_code_and_description'):
        results = {}
        for version in OMOP_NAMING_MAPPING:
            results[version] = []

            for match in df_matches.filter(pl.col("from_version").eq(version), pl.col("match_type").eq(match_type)).iter_rows(named=True):
                results[match['from_version']].append(is_a_match(match['from_version'], match['from_icd_code']) and is_a_match(match['from_version'], match['to_icd_code']))
        return results

    return (get_results_from_matches,)


@app.function
def print_match_validation_results(results):
    for version_name, list_of_results in results.items():
        total = len(list_of_results)
        did_match = list_of_results.count(True)
        try:
            perc_did_match = (did_match*100)/total
        except ZeroDivisionError:
            print(f"perc_did_match ZeroDivisionError: {did_match}/{total}")
            perc_did_match = 0.0
        did_not_match = list_of_results.count(False)
        try:
            perc_did_not_match = (did_not_match*100)/total
        except ZeroDivisionError:
            print(f"perc_did_match ZeroDivisionError: {did_not_match}/{total}")
            perc_did_not_match = 0.0
        print(f"{version_name}: {did_match} ({perc_did_match:.2f} %) matched, {did_not_match} ({perc_did_not_match:.2f} %) did not match out of {total} total checks.")


@app.cell
def _(get_results_from_matches):
    results_match_code_and_description = get_results_from_matches(match_type='match_code_and_description')
    print_match_validation_results(results_match_code_and_description)
    return


@app.cell
def _(get_results_from_matches):
    results_not_found = get_results_from_matches(match_type='not_found')
    print_match_validation_results(results_not_found)
    return


if __name__ == "__main__":
    app.run()
