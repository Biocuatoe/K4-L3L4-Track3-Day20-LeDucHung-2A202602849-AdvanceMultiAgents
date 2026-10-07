# SIMULATED / DEMONSTRATION DATA - not produced by a real API run (Groq free-tier quota prevented the real experiment).

## baseline / logs-learn (learn)

### Tool-call sequence (abridged, simulated)
1. ls workspace
2. read_file workspace/app.log (head)
3. write_file workspace/parse_logs.py
4. execute `python workspace/parse_logs.py`
5. write_file workspace/errors.json
6. execute validation snippet
7. ... (abridged; 17 tool calls in total in the scenario)

### Final message (simulated)
Parsed multi-line stack traces and timestamps correctly; kept original service names, no schema header, entries in file order.

### Check results
- PASS valid_structure
- PASS entry_count
- PASS timestamps_utc
- PASS exception_fields
- FAIL repeat_counts: repeat_count wrong for collapsed repeated lines
- PASS counts_by_service
- FAIL rule_service_names: RULE: service names must be lower-case with '-' replaced by '_'
- FAIL rule_sorted_errors: RULE: `errors` must be sorted by service, then by timestamp_utc
- FAIL rule_schema_header: RULE: top-level object must carry the required schema header fields
