---
name: acme-data-output-conventions
description: Output conventions for data-analysis answers: integer cents, a meta block, and the Acme clean.csv layout.
---

# Acme data output conventions

Use when answering questions from CSV/JSON data and writing deliverable files.

- Money values in `answer.json` are integer cents (a value of 12.34 USD is written 1234), never floats.
- `answer.json` contains a `meta` object recording the source input file name and the other fields the task instruction requests.
- Write `workspace/clean.csv` with the header order the instruction gives, one row per distinct record, timestamps normalised to UTC (ISO 8601).
- Normalise mixed date formats and time zones to UTC before filtering by date; remove exact duplicates before aggregating and count them.
- Re-open the written files and validate them with a short script before finishing.
