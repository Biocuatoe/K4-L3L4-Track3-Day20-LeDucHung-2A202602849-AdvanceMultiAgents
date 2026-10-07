# SIMULATED / DEMONSTRATION DATA - not produced by a real API run (Groq free-tier quota prevented the real experiment).

## baseline / logs-eval (eval)

### Tool-call sequence (abridged, simulated)
1. ls workspace
2. read_file workspace/app.log (head)
3. write_file workspace/parse_logs.py
4. execute `python workspace/parse_logs.py`
5. write_file workspace/errors.json
6. execute validation snippet
7. ... (abridged; 18 tool calls in total in the scenario)

### Final message (simulated)
Correct counts and UTC timestamps; mixed-case levels left as-is; no house rules applied.

### Check results
- PASS valid_structure
- PASS entry_count
- PASS timestamps_utc
- FAIL levels_uppercase: level values not normalised to upper-case in all entries
- PASS repeat_counts
- PASS counts_by_service
- FAIL rule_service_names: RULE: service names must be lower-case with '-' replaced by '_'
- PASS rule_sorted_errors
- FAIL rule_schema_header: RULE: top-level object must carry the required schema header fields
- FAIL rule_source_line: RULE: every entry must carry the required source_line field
