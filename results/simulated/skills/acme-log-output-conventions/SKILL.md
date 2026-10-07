---
name: acme-log-output-conventions
description: Output conventions for log-triage JSON: normalised service names, sorted errors, and the schema header.
---

# Acme log output conventions

Use when turning log files into `errors.json`.

- Service names are lower-case with `-` replaced by `_` (for example `my-service` becomes `my_service`).
- The `errors` list is sorted by service, then by `timestamp_utc`, ascending.
- The top-level object carries `"schema_version": 2` and `"generated_by": "log-triage"`.
- Convert every timestamp to UTC; treat multi-line stack traces as one entry and collapse consecutive identical lines into one entry with a repeat count.
- Validate by loading the JSON again and checking ordering programmatically.
