import marimo

__generated_with = "0.16.4"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import plotly.express as px
    import polars as pl

    from oberbaum.config import get_results_dir
    return get_results_dir, mo, pl, px


@app.cell
def _(get_results_dir):
    from dotenv import load_dotenv

    load_dotenv()
    results_dir = get_results_dir("artifacts")
    results_dir
    return (results_dir,)


@app.cell
def _():
    import plotly.io as pio

    tableau20_hex = [
        '#1F77B4', '#AEC7E8', '#FF7F0E', '#FFBB78', '#2CA02C', '#98DF8A',
        '#D62728', '#FF9896', '#9467BD', '#C5B0D5', '#8C564B', '#C49C94',
        '#E377C2', '#F7B6D2', '#7F7F7F', '#C7C7C7', '#BCBD22', '#DBDB8D',
        '#17BECF', '#9EDAE5'
    ]

    pio.templates['plotly'].layout.colorway = tableau20_hex
    pio.templates.default = 'plotly'
    return


@app.cell
def _(pl, results_dir):
    df_matches = pl.read_csv(f"{results_dir}/*.csv").with_columns(
        pl.col("from_icd_code").str.len_chars().alias("code_length")
    )
    return (df_matches,)


@app.cell
def _(df_matches):
    df_matches
    return


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
def _(pl, px):
    def plot_matches_by_levels(df, version):
        _grouped_df = df.with_columns(
            pl.col("from_icd_code").str.len_chars().alias("code_length")
        ).group_by(["code_length", "is_match"]).len(name="count")

        _fig = px.bar(
            _grouped_df,
            x="code_length",
            y="count",
            color="is_match",
            title=f"{version} matches per level",
            log_y=True
        )
        return _fig
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
        "icd-10-gm": [3, 4, 5, 6, 7],
        "cid-10-bra": [3, 4, 5, 6]
    }
    return (evaluated_code_chars,)


@app.cell
def _(df_matches, evaluated_code_chars, pl):
    def filter_matches_by(version):
        return df_matches.filter(
            pl.col("from_version").eq(version),
            pl.col("to_version").eq("icd-10-who"),
            pl.col("code_length").is_in(evaluated_code_chars[version])
        )
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
def _(px):
    def plot_sens_spec_f1_score(metrics_df, version):
        sorted = metrics_df.sort("threshold")
        thresholds = sorted["threshold"].unique().to_list()
        _fig_thresh = px.line(
            sorted,
            x='threshold',
            y=['sensitivity', 'specificity', 'f1_score'],
            facet_col="model",
            width=1600,
            height=800,
            facet_col_wrap=3
        )
        _fig_thresh.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))  # remove col= sign
        _fig_thresh.update_yaxes(showticklabels=True, showgrid=True, gridwidth=1, gridcolor='lightgrey')
        _fig_thresh.update_xaxes(showticklabels=True, showgrid=True, gridwidth=1, gridcolor='lightgrey')
        _fig_thresh.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',  # remove plotly blue background
            xaxis={"tickmode": "array", "tickvals": thresholds},
            legend={"yanchor": "top", "y": 0.29, "xanchor": "right", "x": 0.89}
        )
        return _fig_thresh
    return (plot_sens_spec_f1_score,)


@app.cell
def _(df_matches, pl):
    code_len_count = df_matches.filter(pl.col("from_version").eq("icd-10-who"), pl.col("threshold").eq(0.5), pl.col("model").eq("jinaai/jina-embeddings-v3")).select(pl.col("code_length").value_counts()).unnest("code_length").to_dict()
    who_count_per_code_len = {cl: ct for cl, ct in zip(code_len_count['code_length'], code_len_count['count'])}
    return (who_count_per_code_len,)


@app.cell
def _(filter_omop_vocabulary_by, pl):
    filter_omop_vocabulary_by("icd-10-cm").with_columns(
        pl.col("concept_code_icd10who").str.len_chars().alias("code_length")
    )
    return


@app.cell
def _(
    df_matches,
    evaluated_code_chars,
    filter_omop_vocabulary_by,
    pl,
    who_count_per_code_len,
):
    def comparison(version, threshold=0.5, model_name="jinaai/jina-embeddings-v3", only_validated=True):
        _omop_filtered = filter_omop_vocabulary_by(version)
        _matches = df_matches.filter(
            pl.col("from_version").eq(version),
            pl.col("to_version").eq("icd-10-who"),
            pl.col("threshold").eq(threshold),
            pl.col("model").eq(model_name),
        )
        if only_validated:
            _matches = _matches.filter(pl.col("code_length").is_in(evaluated_code_chars[version]))
        _matches = _matches.sort("code_length")

        _results_df = {
            "code_length": [],
            "correct_matches": [],
            "total_to_version": [],  # who
            "total_from_version": [],
        }

        for code_length, _filtered in _matches.group_by("code_length"):
            _correct_matches = 0

            for _row in _filtered.iter_rows(named=True):
                _found = _omop_filtered.filter(
                    pl.col("concept_code").eq(_row["from_icd_code"]),
                )
                _found = not _found.is_empty()
                if _found and _row["is_match"]:
                    _correct_matches += 1

            _total_who = who_count_per_code_len.get(code_length[0], 0)
            _total_version = len(_filtered.filter(pl.col("from_version").eq(version)).unique())
            _results_df["code_length"].append(code_length[0])
            _results_df["correct_matches"].append(_correct_matches)
            _results_df["total_to_version"].append(_total_who)
            _results_df["total_from_version"].append(_total_version)

        return pl.DataFrame(_results_df)
    return (comparison,)


@app.cell
def _(mo):
    mo.md(r"""### ICD-10-GM""")
    return


@app.cell
def _(comparison):
    df_comparison_gm = comparison("icd-10-gm")
    df_comparison_gm
    return (df_comparison_gm,)


@app.cell
def _(px):
    def plot_comparison(df_comparison, version):
        _fig = px.bar(df_comparison, x="code_length", y=["total_from_version", "total_to_version", "correct_matches"], log_y=True, barmode="group")
        _fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            legend={"yanchor": "top", "y": 0.99, "xanchor": "right", "x": 0.99}
        )
        _fig.update_yaxes(zeroline=True, showgrid=True, gridwidth=1, gridcolor='lightgrey')
        _fig.update_xaxes(zeroline=True, linewidth=1, linecolor='lightgrey')
        _labels = {"total_from_version": version, "total_to_version": "icd-10-who", "correct_matches": "Validated matches"}
        _fig.for_each_trace(lambda t: t.update(name = _labels[t.name]))
        return _fig
    return (plot_comparison,)


@app.cell
def _(df_comparison_gm, plot_comparison):
    plot_comparison(df_comparison_gm, "icd-10-gm")
    return


@app.cell
def _(comparison, plot_comparison):
    _fig = plot_comparison(comparison("icd-10-gm", only_validated=False), "icd-10-gm")
    _fig.write_image("comparison_code_len_icd-10-gm.pdf")
    _fig
    return


@app.cell
def _(calculate_metrics_by):
    metrics_gm = calculate_metrics_by("icd-10-gm")
    return (metrics_gm,)


@app.cell
def _(metrics_gm):
    metrics_gm.head()
    return


@app.cell
def _(mo):
    mo.md("""**Sensitivity, Specificity, and F1-score** by Thresholds and Models - icd-10-gm""")
    return


@app.cell
def _(metrics_gm, plot_sens_spec_f1_score):
    _fig = plot_sens_spec_f1_score(metrics_gm, "icd-10-gm")
    # _fig.write_image("sensitivity_specificitity_f1_icd-10-gm.pdf")
    _fig
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
def _(pl):
    def best_model_per_threshold(metrics_df):
        return metrics_df.group_by(pl.col("threshold")).agg(pl.col("model").filter(pl.col("true_positive") == pl.col("true_positive").max()))
    return (best_model_per_threshold,)


@app.cell
def _(best_metrics_per_model_threshold, metrics_gm):
    best_metrics_per_model_threshold(metrics_gm)
    return


@app.cell
def _(best_model_per_threshold, metrics_gm):
    best_model_per_threshold(metrics_gm)
    return


@app.cell
def _(mo):
    mo.md(r"""### ICD-10-CM""")
    return


@app.cell
def _(calculate_metrics_by):
    metrics_cm = calculate_metrics_by("icd-10-cm")
    return (metrics_cm,)


@app.cell
def _(metrics_cm):
    metrics_cm.head()
    return


@app.cell
def _(best_metrics_per_model_threshold, metrics_cm):
    best_metrics_per_model_threshold(metrics_cm)
    return


@app.cell
def _(metrics_cm, plot_sens_spec_f1_score):
    _fig = plot_sens_spec_f1_score(metrics_cm, "icd-10-cm")
    _fig.write_image("sensitivity_specificitity_f1_icd-10-cm.pdf")
    _fig
    return


@app.cell
def _(best_model_per_threshold, metrics_cm):
    best_model_per_threshold(metrics_cm)
    return


@app.cell
def _(comparison):
    df_comparison_cm = comparison("icd-10-cm")
    df_comparison_cm
    return (df_comparison_cm,)


@app.cell
def _(df_comparison_cm, plot_comparison):
    plot_comparison(df_comparison_cm, "icd-10-cm")
    return


@app.cell
def _(comparison, plot_comparison):
    _fig = plot_comparison(comparison("icd-10-cm", only_validated=False), "icd-10-cm")
    # _fig.write_image("comparison_code_len_icd-10-cm.pdf")
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Validation with country mappings

    ## CID-10-BRA

    Negative Predictive Value (NPV)

    \[
    \text{Precision}_{\text{neg}} = \frac{TP_{\text{neg}}}{TP_{\text{neg}} + FP_{\text{neg}}}
    \]

    * **True Positive neg**: excluded by our approach and present in the excluded list
    * **False Positive neg**: included by our approach and present in the excluded list
    """
    )
    return


@app.cell
def _(pl):
    bra_df = pl.read_csv("data/mappings/cid-10-bra-removed.csv")
    bra_df
    return (bra_df,)


@app.cell
def _(bra_df):
    bra_codes = bra_df["code"].to_list()
    return (bra_codes,)


@app.cell
def _(mo):
    mo.md(
        r"""
    These matches are from the experiment of creating a graph from the removed nodes with the removed list provided by Ministry of Health of Brazil.
    Since the list provides the list of codes that were allegdly removed from the original version (ICD-10-WHO), it is expected that it has full adherence with the WHO version.
    """
    )
    return


@app.cell
def _(pl):
    bra_matches = pl.read_csv("/home/gomes-ferreiraa/scratch/oberbaumbrucke/results-bra/*.csv").with_columns(
        pl.col("from_icd_code").str.len_chars().alias("code_length")
    )
    bra_matches
    return (bra_matches,)


@app.cell
def _(bra_matches, pl):
    bra_matches.filter(
        pl.col("from_title").ne("--- FOR VALIDATION PURPOSES ONLY ---"),
        pl.col("code_length").is_in([3, 4, 5]),  # do not include chapters or blocks
    )
    return


@app.cell
def _(bra_codes, bra_matches, pl):
    npv = {
        "model": [],
        "threshold": [],
        "version": [],
        "value": []
    }

    for (_model, _threshold), _filtered in bra_matches.group_by(["model", "threshold"]):
        _filter_by_model_threshold = _filtered.filter(
            pl.col("from_icd_code").is_in(bra_codes)
        )
        _true_positive_neg = _filter_by_model_threshold.filter(
            pl.col("is_match").eq(False),
        ).select(pl.len())
        _false_positive_neg = _filter_by_model_threshold.filter(
            pl.col("is_match").eq(True)
        ).select(pl.len())
        print(_model, _threshold, _filter_by_model_threshold.filter(pl.col("is_match").eq(True)).shape)

        _value = get_sensitivity(_true_positive_neg, _false_positive_neg)
        npv["model"].append(_model)
        npv["threshold"].append(_threshold)
        npv["version"].append("cid-10-bra")
        npv["value"].append(_value.item())
    metrics_br = pl.DataFrame(npv)
    metrics_br
    return (metrics_br,)


@app.cell
def _(bra_codes, bra_matches, pl):
    bra_matches.filter(
        pl.col("from_icd_code").is_in(bra_codes)
    )
    return


@app.cell
def _(metrics_br, px):
    _fig_thresh = px.line(
        metrics_br.sort("threshold"),
        x='threshold',
        y='value',
        title='Sensitivity by Thresholds and Models - CID-10-BRA',
        facet_col="model",
        width=1800,
        height=400
    )
    _fig_thresh
    return


if __name__ == "__main__":
    app.run()
