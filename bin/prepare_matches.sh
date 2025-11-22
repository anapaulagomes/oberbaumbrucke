# create graph files
uv run --active oberbaum graph create icd-10-who data/icd102019enMeta --export
uv run --active oberbaum graph create icd-10-gm data/icd10gm2025/Klassifikationsdateien --export
uv run --active oberbaum graph create cid-10-bra data/CID-10-2025 --export
uv run --active oberbaum graph create icd-10-cm data/icd10cm-table-index-April-2025 --export

# store embeddings
uv run --active oberbaum db create
uv run --active oberbaum graph embeddings --force
