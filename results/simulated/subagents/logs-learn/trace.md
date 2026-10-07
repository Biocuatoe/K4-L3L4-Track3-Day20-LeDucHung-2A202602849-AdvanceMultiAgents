# SIMULATED / DEMONSTRATION DATA - not produced by a real API run (Groq free-tier quota prevented the real experiment).

## subagents / logs-learn (learn)

### Tool-call sequence (abridged, simulated)
1. task(explorer): gather docstrings/inputs
2. task(implementer): apply changes (brief lists rules)
3. task(reviewer): independent check
4. ls workspace
5. read_file workspace/app.log (head)
6. write_file workspace/parse_logs.py
7. execute `python workspace/parse_logs.py`
8. write_file workspace/errors.json
9. execute validation snippet
10. ... (abridged; 29 tool calls in total in the scenario)

### Final message (simulated)
Implementer received a thin brief (no mention of repeat collapsing) so the duplicated-line semantics were lost.

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
