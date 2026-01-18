import marimo

__generated_with = "0.17.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import plotly.express as px
    import plotly.graph_objects as go
    import polars as pl

    from oberbaum.config import get_results_dir
    return get_results_dir, go, mo, pl, px


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
        pl.col("from_icd_code").str.len_chars().alias("code_length"),
    ).with_columns(
        pl.when(pl.col("code_length").is_in([1, 2]))
            .then(pl.lit("chapter"))
        .when(pl.col("from_icd_code").str.contains(r"[A-Z]\d{2}-[A-Z]\d{2}"))  # A00-A09
            .then(pl.lit("block"))
        .otherwise(pl.col("code_length")).alias("code_type")
    )
    df_matches
    return (df_matches,)


@app.cell
def _():
    code_type_order = ["chapter", "block", "3", "4",  "5", "6", "7"]
    return (code_type_order,)


@app.cell
def _(df_matches, pl):
    who_codes = df_matches.filter(pl.col("from_version").eq("icd-10-who"))["from_icd_code"].unique().to_list()
    who_codes
    return (who_codes,)


@app.cell
def _(df_matches, pl):
    _code_len_count = df_matches.filter(
        pl.col("from_version").eq("icd-10-who"),
        pl.col("threshold").eq(0.5),
        pl.col("model").eq("jinaai/jina-embeddings-v3")  # all thresholds and models will have the same numbers
    ).select(pl.col("code_type").value_counts()).unnest("code_type").to_dict()

    who_count_per_code_len = {cl: ct for cl, ct in zip(_code_len_count['code_type'], _code_len_count['count'])}
    return (who_count_per_code_len,)


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
def _(pl, who_codes):
    df_omop = pl.read_csv(
        "data/mappings/omop_mappings_select_cr_concept_id_1_c1_vocabulary_id_c1_concept_cod_202507061258.csv",
        new_columns=["concept_id", "vocabulary_id", "concept_code", "concept_name", "relationship_id", "concept_id_2", "vocabulary_id_2", "concept_code_2", "concept_name_2"],
    )
    df_omop = df_omop.with_columns(pl.col("concept_code").str.replace(".", "", literal=True))

    _source_df = df_omop.filter(pl.col("vocabulary_id").is_in(["ICD10CM", "ICD10GM"]))
    _target_df = df_omop.filter(pl.col("vocabulary_id").eq("ICD10"))

    mapping_df = _source_df.join(
        _target_df, on="concept_code_2", suffix="_icd10who"  # how = inner; merge on snomed code
    )
    mapping_df = mapping_df.filter(pl.col("concept_code_icd10who").is_in(who_codes))
    mapping_df
    return (mapping_df,)


@app.cell
def _(mapping_df, who_codes):
    # icd-10-who from SNOMED CT has 15470 codes vs 12506 from WHO files
    len(who_codes), len(mapping_df["concept_code_icd10who"].unique())
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
    mo.md(r"""## Validation""")
    return


@app.cell
def _(df_matches, pl):
    def filter_matches_by(version, targeted_groups=None):
        if targeted_groups:
            return df_matches.filter(
                pl.col("from_version").eq(version),
                pl.col("to_version").eq("icd-10-who"),
                pl.col("code_type").is_in(targeted_groups)
            )
        return df_matches.filter(
            pl.col("from_version").eq(version),
            pl.col("to_version").eq("icd-10-who"),
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
def _(filter_omop_vocabulary_by):
    omop_gm = filter_omop_vocabulary_by("icd-10-gm")
    return (omop_gm,)


@app.cell
def _(filter_matches_by):
    matches_gm = filter_matches_by("icd-10-gm")
    return (matches_gm,)


@app.cell
def _(filter_omop_vocabulary_by):
    omop_cm = filter_omop_vocabulary_by("icd-10-cm")
    return (omop_cm,)


@app.cell
def _(filter_matches_by):
    matches_cm = filter_matches_by("icd-10-cm")
    return (matches_cm,)


@app.cell
def _(pl):
    def calculate_metrics_by(version, matches, omop_mapping):
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


        for (_model, _threshold), _filtered in matches.group_by(["model", "threshold"]):
            _results = {
                "true_positive": 0,
                "true_negative": 0,
                "false_positive": 0,
                "false_negative": 0,
            }

            for _row in _filtered.iter_rows(named=True):
                _found = omop_mapping.filter(
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
def _(df_matches):
    models = df_matches["model"].unique().sort()
    models
    return (models,)


@app.cell
def _(models, px):
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
            facet_col_wrap=3,
            category_orders={"model": models}
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
def _(pl, who_count_per_code_len):
    def comparison(version, matches, omop_mapping, threshold=0.5, model_name="jinaai/jina-embeddings-v3"):
        _matches = matches.filter(
            pl.col("threshold").eq(threshold),
            pl.col("model").eq(model_name),
        )

        _results_df = {
            "code_type": [],
            "correct_matches": [],
            "total_to_version": [],  # who
            "total_from_version": [],
            "uphill": []
        }

        for code_type, _filtered in _matches.group_by("code_type"):
            _correct_matches = 0
            _uphill = 0

            for _row in _filtered.iter_rows(named=True):
                _found = omop_mapping.filter(
                    pl.col("concept_code").eq(_row["from_icd_code"])
                )
                _found = not _found.is_empty()
                if _found and _row["is_match"]:
                    _correct_matches += 1
                    if _row["match_type"] == "uphill_match":
                        _uphill += 1

            _total_who = who_count_per_code_len.get(code_type[0], 0)
            _total_version = len(_filtered.filter(pl.col("from_version").eq(version)).unique())
            _results_df["code_type"].append(code_type[0])
            _results_df["total_from_version"].append(_total_version)
            _results_df["total_to_version"].append(_total_who)
            _results_df["correct_matches"].append(_correct_matches)
            _results_df["uphill"].append(_uphill)
        return pl.DataFrame(_results_df)
    return (comparison,)


@app.cell
def _(mo):
    mo.md(r"""### ICD-10-GM""")
    return


@app.cell
def _(comparison, matches_gm, omop_gm):
    df_comparison_gm = comparison("icd-10-gm", matches_gm, omop_gm)
    df_comparison_gm
    return (df_comparison_gm,)


@app.cell
def _(code_type_order, px):
    def plot_comparison(df_comparison, version):
        _fig = px.bar(
            df_comparison,
            x="code_type",
            y=["total_from_version", "total_to_version", "correct_matches"],
            log_y=True,
            barmode="group",
            category_orders={'code_type': code_type_order}
        )
        _fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            legend={"yanchor": "top", "y": 0.85, "xanchor": "right", "x": 0.25}
        )
        _fig.update_yaxes(zeroline=True, showgrid=True, gridwidth=1, gridcolor='lightgrey')
        _fig.update_xaxes(zeroline=True, linewidth=1, linecolor='lightgrey')
        _labels = {"total_from_version": version, "total_to_version": "icd-10-who", "correct_matches": "validated matches"}
        _fig.for_each_trace(lambda t: t.update(name = _labels[t.name]))
        return _fig
    return


@app.cell
def _(code_type_order, go, pl):
    def plot_comparison_with_texture(df_comparison, version):
        df_comparison = df_comparison.with_columns(
            match_base=pl.col("correct_matches") - pl.col("uphill")
        )

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df_comparison["code_type"],
            y=df_comparison["total_from_version"],
            name=str(version),
            offsetgroup=0,  #position of the group
            # marker_color='#636EFA' # Plotly Blue
        ))

        fig.add_trace(go.Bar(
            x=df_comparison["code_type"],
            y=df_comparison["total_to_version"],
            name="icd-10-who",
            offsetgroup=1,
            # marker_color='#EF553B' # Plotly Red
        ))

        fig.add_trace(go.Bar(
            x=df_comparison["code_type"],
            y=df_comparison["match_base"],
            name="validated matches",
            offsetgroup=2,
            # marker_color='#00CC96' # Plotly Green
        ))

        fig.add_trace(go.Bar(
            x=df_comparison["code_type"],
            y=df_comparison["uphill"],
            name="validated matches w/ uphill",
            offsetgroup=2, # Same group as match_base
            base=df_comparison["match_base"], # Stacks this bar on top of the base
            # marker_color='#00CC96', # Same color as the base
            marker_pattern_shape="/",
            showlegend=True
        ))
        fig.update_layout(
            font_size=25,
            width=1400,
            height=800,
            yaxis_type="log",
            barmode="group",
            plot_bgcolor='rgba(0,0,0,0)',
            legend={"yanchor": "top", "y": 0.9, "xanchor": "right", "x": 0.28}
        )
        fig.for_each_annotation(lambda a: a.update(text=a.text.upper()))  # remove col= sign

        fig.update_yaxes(zeroline=True, showgrid=True, gridwidth=1, gridcolor='lightgrey', title='Nr. of codes')
        fig.update_xaxes(zeroline=True, linewidth=1, linecolor='lightgrey', categoryorder='array', categoryarray=code_type_order)

        return fig
    return (plot_comparison_with_texture,)


@app.cell
def _(df_comparison_gm, plot_comparison_with_texture):
    _fig = plot_comparison_with_texture(df_comparison_gm, "icd-10-gm")
    _fig.write_image("comparison_code_type_icd-10-gm.pdf")
    _fig
    return


@app.cell
def _(calculate_metrics_by, matches_gm, omop_gm):
    metrics_gm = calculate_metrics_by("icd-10-gm", matches_gm, omop_gm)
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
    _fig.write_image("sensitivity_specificitity_f1_icd-10-gm.pdf")
    _fig
    return


@app.cell
def _(calculate_metrics_by, matches_gm, omop_gm, pl):
    _version = "icd-10-gm"
    _matches_by_targeted_groups_gm = matches_gm.filter(pl.col("code_type").is_in(["3", "4"]))
    metrics_gm_3_and_4 = calculate_metrics_by(_version, _matches_by_targeted_groups_gm, omop_gm)
    metrics_gm_3_and_4
    return


@app.cell
def _(metrics_cm_3_and_4, plot_sens_spec_f1_score):
    _version = "icd-10-gm"

    _fig = plot_sens_spec_f1_score(metrics_cm_3_and_4, _version)
    _fig.write_image("sensitivity_specificitity_f1_icd-10-gm-3-and-4.pdf")
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
def _(calculate_metrics_by, matches_cm, omop_cm):
    metrics_cm = calculate_metrics_by("icd-10-cm", matches_cm, omop_cm)
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
def _(metrics_gm):
    metrics_gm
    return


@app.cell
def _(metrics_cm):
    metrics_cm
    return


@app.cell
def _(metrics_cm_3_and_4):
    metrics_cm_3_and_4
    return


@app.cell
def _(best_metrics_per_model_threshold, metrics_cm_3_and_4):
    best_metrics_per_model_threshold(metrics_cm_3_and_4)
    return


@app.cell
def _(best_model_per_threshold, metrics_cm_3_and_4):
    best_model_per_threshold(metrics_cm_3_and_4)
    return


@app.cell
def _(metrics_cm, plot_sens_spec_f1_score):
    _fig = plot_sens_spec_f1_score(metrics_cm, "icd-10-cm")
    _fig.write_image("sensitivity_specificitity_f1_icd-10-cm.pdf")
    _fig
    return


@app.cell
def _(calculate_metrics_by, matches_cm, omop_cm, pl):
    _version = "icd-10-cm"
    _matches_by_targeted_groups_cm = matches_cm.filter(pl.col("code_type").is_in(["3", "4"]))
    metrics_cm_3_and_4 = calculate_metrics_by(_version, _matches_by_targeted_groups_cm, omop_cm)
    metrics_cm_3_and_4
    return (metrics_cm_3_and_4,)


@app.cell
def _(metrics_cm_3_and_4, plot_sens_spec_f1_score):
    _version = "icd-10-cm"
    _fig = plot_sens_spec_f1_score(metrics_cm_3_and_4, _version)
    _fig.write_image("sensitivity_specificitity_f1_icd-10-cm-3-and-4.pdf")
    _fig
    return


@app.cell
def _(best_model_per_threshold, metrics_cm):
    best_model_per_threshold(metrics_cm)
    return


@app.cell
def _(comparison, matches_cm, omop_cm):
    df_comparison_cm = comparison("icd-10-cm", matches_cm, omop_cm)
    df_comparison_cm
    return (df_comparison_cm,)


@app.cell
def _(df_comparison_cm, plot_comparison_with_texture):
    _fig = plot_comparison_with_texture(df_comparison_cm, "icd-10-cm")
    _fig.write_image("comparison_code_type_icd-10-cm.pdf")
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
