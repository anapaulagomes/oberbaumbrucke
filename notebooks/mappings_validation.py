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
def _(con, pl):
    df_matches = con.execute("SELECT * FROM matches;").pl().with_columns(
        pl.col("from_icd_code").str.len_chars().alias("code_length")
    )
    df_matches.head()
    return (df_matches,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Validation of our approach with OMOP vocabularies

    Notes:

    * ICD-10-GM/ICD-10-CM: chapters are not included in the OMOP voca, only from 3-7 length.
    * ICD-10-CM: the XML file didn't contain all 7-char codes available.
    """
    )
    return


@app.cell
def _():
    OMOP_NAMING_MAPPING = {
        "icd-10-who": "ICD10",
        "icd-10-cm": "ICD10CM",
        "icd-10-gm": "ICD10GM",
    }
    return (OMOP_NAMING_MAPPING,)


@app.cell
def _(pl):
    df_omop = pl.read_csv(
        "data/mappings/omop_mappings_select_cr_concept_id_1_c1_vocabulary_id_c1_concept_cod_202507061258.csv",
        new_columns=["concept_id", "vocabulary_id", "concept_code", "concept_name", "relationship_id", "concept_id_2", "vocabulary_id_2", "concept_code_2", "concept_name_2"],
    )
    df_omop = df_omop.with_columns(pl.col("concept_code").str.replace(".", "", literal=True))

    _source_df = df_omop.filter(pl.col("vocabulary_id").is_in(["ICD10CM", "ICD10GM"]))
    _target_df = df_omop.filter(pl.col("vocabulary_id").eq("ICD10"))

    mapping_df = _source_df.join(_target_df, on="concept_code_2", suffix="_icd10who")  # how = inner; merge on snomed code
    mapping_df
    return (mapping_df,)


@app.cell
def _(mapping_df, pl, px):
    _grouped_df = mapping_df.with_columns(
        pl.col("concept_code").str.len_chars().alias("code_length")
    ).group_by(["code_length", "vocabulary_id"]).len(name="count")

    _fig = px.bar(
        _grouped_df,
        x="code_length",
        y="count",
        color="vocabulary_id",
        title="ICD-10-GM Code length OMOP vocab",
        log_y=True
    )
    _fig
    return


@app.function
def get_sensitivity(true_positive, false_negative):
    """ Sensitivity = TP / (FN + TP)"""
    try:
        return true_positive/(false_negative + true_positive)
    except ZeroDivisionError:
        return None


@app.function
def get_specificity(true_negative, false_positive):
    """Specificity = TN / (FP + TN)"""
    try:
        return true_negative/(false_positive + true_negative)
    except ZeroDivisionError:
        return None


@app.function
def get_f1_score(specificity, sensitivity):
    """F1 Score = 2 * (Specificity * sensitivity) / (Specificity + sensitivity)"""
    try:
        return 2 * (specificity * sensitivity) / (specificity + sensitivity)
    except TypeError:
        return None


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Test validation with matches using ICD-10-GM""")
    return


@app.cell
def _(df_matches, pl):
    _version = "icd-10-gm"
    _model_name = "jinaai/jina-embeddings-v3"
    _threshold = 0.80

    gm_df = df_matches.filter(
        pl.col("from_version").eq(_version),
        pl.col("to_version").eq("icd-10-who"),
        pl.col("model").eq(_model_name),
        pl.col("threshold").eq(_threshold),
    )
    gm_df
    return (gm_df,)


@app.cell
def _(mo):
    mo.md(r"""### Per char length""")
    return


@app.cell
def _(OMOP_NAMING_MAPPING, get_youndes_j, gm_df, mapping_df, pl):
    _filtered = mapping_df.filter(
        pl.col("vocabulary_id").eq(OMOP_NAMING_MAPPING["icd-10-gm"]),
        pl.col("vocabulary_id_icd10who").eq(OMOP_NAMING_MAPPING["icd-10-who"])
    )
    # True positive: is_match = true + found
    # True negative: is_match = false + not found
    # False positive: is_match = true + not found
    # False negative: is_match = false + found
    for char_len in range(3, 8):
        _results = {
            "true_positive": 0,
            "true_negative": 0,
            "false_positive": 0,
            "false_negative": 0,
        }
        for _row in gm_df.filter(pl.col("code_length").eq(char_len)).iter_rows(named=True):
            _found = _filtered.filter(
                pl.col("concept_code").eq(_row["from_icd_code"])
            )
            _not_found = _found.is_empty()
            if _not_found:
                if _row["is_match"]:
                    _results["false_positive"] += 1
                else:
                    _results["true_negative"] += 1
            else:  # found
                if _row["is_match"]:
                    _results["true_positive"] += 1
                else:
                    _results["false_negative"] += 1
        _sensitivity = get_sensitivity(_results["true_positive"], _results["false_negative"])
        _specificity = get_specificity(_results["true_negative"], _results["false_positive"])
        _f1_score = get_f1_score(_specificity, _sensitivity)
        _youdens_j = get_youndes_j(_specificity, _sensitivity)
        print(f'Sensitivity: {_sensitivity} Specificity: {_specificity} Youden\'s J statistic: {_youdens_j} F1 score: {_f1_score}')
    return


@app.cell
def _(mo):
    mo.md(r"""### All matches""")
    return


@app.cell
def _(OMOP_NAMING_MAPPING, get_youndes_j, gm_df, mapping_df, pl):
    _filtered = mapping_df.filter(
        pl.col("vocabulary_id").eq(OMOP_NAMING_MAPPING["icd-10-gm"]),
        pl.col("vocabulary_id_icd10who").eq(OMOP_NAMING_MAPPING["icd-10-who"])
    )
    # True positive: is_match = true + found
    # True negative: is_match = false + not found
    # False positive: is_match = true + not found
    # False negative: is_match = false + found
    _results = {
        "true_positive": 0,
        "true_negative": 0,
        "false_positive": 0,
        "false_negative": 0,
    }
    for _row in gm_df.iter_rows(named=True):
        _found = _filtered.filter(
            pl.col("concept_code").eq(_row["from_icd_code"])
        )
        _not_found = _found.is_empty()
        if _not_found:
            if _row["is_match"]:
                _results["false_positive"] += 1
            else:
                _results["true_negative"] += 1
        else:  # found
            if _row["is_match"]:
                _results["true_positive"] += 1
            else:
                _results["false_negative"] += 1
    _sensitivity = get_sensitivity(_results["true_positive"], _results["false_negative"])
    _specificity = get_specificity(_results["true_negative"], _results["false_positive"])
    _f1_score = get_f1_score(_specificity, _sensitivity)
    _youdens_j = get_youndes_j(_specificity, _sensitivity)

    print(f'Sensitivity: {_sensitivity} Specificity: {_specificity} Youden\'s J statistic: {_youdens_j} F1 score: {_f1_score}')
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r""" """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Validation""")
    return


@app.cell
def _():
    evaluated_code_chars = {
        "icd-10-cm": [3, 4, 5, 6],
        "icd-10-gm": [3, 4, 5, 6, 7]
    }
    return (evaluated_code_chars,)


@app.cell
def _(df_matches, evaluated_code_chars, pl):
    def filter_matches_by(version):
        return df_matches.filter(
            pl.col("from_version").eq(version),
            pl.col("to_version").eq("icd-10-who"),
        ).filter(pl.col("code_length").is_in(evaluated_code_chars[version]))
    return (filter_matches_by,)


@app.cell
def _(OMOP_NAMING_MAPPING, mapping_df, pl):
    def filter_omop_vocabulary_by(version):
        return mapping_df.filter(
            pl.col("vocabulary_id").eq(OMOP_NAMING_MAPPING[version]),
            pl.col("vocabulary_id_icd10who").eq(OMOP_NAMING_MAPPING["icd-10-who"])
        )
    return (filter_omop_vocabulary_by,)


@app.cell
def _(filter_matches_by):
    for (_m, _t), _df in filter_matches_by("icd-10-gm").group_by(["model", "threshold"]):
        print(_m, _t, _df.shape)
    return


@app.cell
def _(filter_matches_by, filter_omop_vocabulary_by, pl):
    def calculate_metrics_by(version):
        _omop_filtered = filter_omop_vocabulary_by(version)
        _matches = filter_matches_by(version)

        _results_df = {
            "model": [],
            "threshold": [],
            "true_positive": [],
            "true_negative": [],
            "false_positive": [],
            "false_negative": [],
            "sensitivity": [],
            "specificity": [],
            "f1_score": [],
        }


        for (_model, _threshold), _filtered in _matches.group_by(["model", "threshold"]):
            _results = {
                "true_positive": 0,
                "true_negative": 0,
                "false_positive": 0,
                "false_negative": 0,
            }

            for _row in _filtered.iter_rows(named=True):
                _found = _omop_filtered.filter(
                    pl.col("concept_code").eq(_row["from_icd_code"])
                )
                _not_found = _found.is_empty()
                if _not_found:
                    if _row["is_match"]:
                        _results["false_positive"] += 1
                    else:
                        _results["true_negative"] += 1
                else:  # found
                    if _row["is_match"]:
                        _results["true_positive"] += 1
                    else:
                        _results["false_negative"] += 1
            _sensitivity = get_sensitivity(_results["true_positive"], _results["false_negative"])
            _specificity = get_specificity(_results["true_negative"], _results["false_positive"])
            _f1_score = get_f1_score(_specificity, _sensitivity)
            _results_df["model"].append(_model)
            _results_df["threshold"].append(_threshold)
            _results_df["true_positive"].append(_results["true_positive"])
            _results_df["true_negative"].append(_results["true_negative"])
            _results_df["false_positive"].append(_results["false_positive"])
            _results_df["false_negative"].append(_results["false_negative"])
            _results_df["sensitivity"].append(_sensitivity)
            _results_df["specificity"].append(_specificity)
            _results_df["f1_score"].append(_f1_score)

        return pl.DataFrame(_results_df)
    return (calculate_metrics_by,)


@app.cell
def _(calculate_metrics_by):
    metrics_gm = calculate_metrics_by("icd-10-gm")
    return (metrics_gm,)


@app.cell
def _(metrics_gm):
    metrics_gm
    return


@app.cell
def _(pl):
    def best_metrics_per_model_threshold(metrics_df):
        return (
            metrics_df.group_by(["model"])
            .agg([
                pl.col("threshold").filter(pl.col("sensitivity") == pl.col("sensitivity").max()).first().alias("best_threshold_sensitivity"),
                pl.col("sensitivity").max().alias("best_sensitivity"),
                pl.col("threshold").filter(pl.col("specificity") == pl.col("specificity").max()).first().alias("best_threshold_specificity"),
                pl.col("specificity").max().alias("best_specificity"),
                pl.col("threshold").filter(pl.col("f1_score") == pl.col("f1_score").max()).first().alias("best_threshold_f1"),
                pl.col("f1_score").max().alias("best_f1_score")
            ])
        )
    return (best_metrics_per_model_threshold,)


@app.cell
def _(best_metrics_per_model_threshold, metrics_gm):
    best_metrics_per_model_threshold(metrics_gm)
    return


@app.cell
def _():
    # metrics_cm = calculate_metrics_by("icd-10-cm")
    return


@app.cell
def _():
    # best_metrics_per_model_threshold(metrics_cm)
    return


@app.cell
def _(metrics_gm, px):
    _fig_thresh = px.scatter(
        metrics_gm,
        x='threshold',
        y=['false_positive', 'true_positive'], # Plot both rates
        title='TPR and FPR at every threshold',
        log_y=True,
        width=700,
        height=500
    )

    _fig_thresh.update_yaxes(title='Number of codes', rangemode='tozero')

    _fig_thresh.show()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
