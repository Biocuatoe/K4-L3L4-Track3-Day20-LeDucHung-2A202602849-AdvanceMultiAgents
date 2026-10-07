# SIMULATED / DEMONSTRATION DATA - not produced by a real API run (Groq free-tier quota prevented the real experiment).

## skills-auto / logs-eval (eval)

### Tool-call sequence (abridged, simulated)
1. read_file skills/auto/acme-log-output-conventions/SKILL.md
2. ls workspace
3. read_file workspace/app.log (head)
4. write_file workspace/parse_logs.py
5. execute `python workspace/parse_logs.py`
6. write_file workspace/errors.json
7. execute validation snippet
8. ... (abridged; 20 tool calls in total in the scenario)

### Final message (simulated)
Read only the log-output skill (skipped the general one); the three learned rules applied; new source_line rule not covered.

### Check results
- PASS valid_structure
- PASS entry_count
- PASS timestamps_utc
- FAIL levels_uppercase: level values not normalised to upper-case in all entries
- PASS repeat_counts
- PASS counts_by_service
- PASS rule_service_names
- PASS rule_sorted_errors
- PASS rule_schema_header
- FAIL rule_source_line: RULE: every entry must carry the required source_line field
