#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <ICD-10 target code>"
  exit 1
fi

oberbaum graph subgraph icd-10-who data/icd102019enMeta "$@"
oberbaum graph subgraph icd-10-gm data/icd10gm2025/Klassifikationsdateien "$@"
oberbaum graph subgraph cid-10-bra data/CID10CSV "$@"
oberbaum graph subgraph icd-10-cm data/icd10cm-table-index-April-2025 "$@"
