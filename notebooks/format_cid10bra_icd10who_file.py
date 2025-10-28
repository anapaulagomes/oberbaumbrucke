import marimo

__generated_with = "0.16.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    from openpyxl import load_workbook
    return load_workbook, pl


@app.cell
def _(load_workbook):
    workbook = load_workbook('data/mappings/CID10-v2019-lista-codigos.xlsx')
    return (workbook,)


@app.cell
def _(workbook):
    workbook.sheetnames
    return


@app.cell
def _(workbook):
    def get_codes_in_bold(sheet_index, col, row):
        for _row in workbook.worksheets[sheet_index].iter_rows(max_col=col, min_row=row):
            if _row[0].font and _row[0].font.bold:
                yield _row[0].value.replace(".", "").strip()

    return (get_codes_in_bold,)


@app.cell
def _(workbook):
    def get_codes(sheet_index, col, row):
        for _row in workbook.worksheets[sheet_index].iter_rows(max_col=col, min_row=row):
            if _row[0].value:
                yield _row[0].value.replace(".", "").strip()

    return (get_codes,)


@app.cell
def _(get_codes_in_bold):
    added = list(get_codes_in_bold(0, 1, 4))
    return (added,)


@app.cell
def _(get_codes):
    removed = list(get_codes(3, 1, 3))
    return (removed,)


@app.cell
def _(added, pl, removed):
    df = pl.DataFrame({"code": added, "change_type": ["added"] * len(added) })
    df = df.vstack(pl.DataFrame({"code": removed, "change_type": ["removed"] * len(removed) }))
    df
    return (df,)


@app.cell
def _(df):
    df.write_csv("data/mappings/cid-10-bra-added-removed.csv")
    return


if __name__ == "__main__":
    app.run()
