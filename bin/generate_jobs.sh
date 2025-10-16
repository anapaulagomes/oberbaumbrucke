#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <ICD-10 versions separated by space: icd-10-who icd-10-cm icd-10-gm cid-10-bra>"
  exit 1
fi

for version in "$@"; do
    for chapter in {1..22}; do
      for threshold in 0.75 0.8 0.85 0.9 0.95; do
          echo "$version $chapter $threshold";
      done
    done
done
