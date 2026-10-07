# SIMULATED / DEMONSTRATION DATA - not produced by a real API run (Groq free-tier quota prevented the real experiment).

## skills-auto / data-learn (learn)

### Tool-call sequence (abridged, simulated)
1. read_file skills/auto/acme-data-output-conventions/SKILL.md
2. read_file skills/auto/spec-first-debugging/SKILL.md
3. ls workspace
4. read_file workspace/<input> (head)
5. write_file workspace/analyze.py
6. execute `python workspace/analyze.py`
7. write_file workspace/answer.json
8. write_file workspace/clean.csv
9. execute validation snippet
10. ... (abridged; 18 tool calls in total in the scenario)

### Final message (simulated)
Cents and meta block applied; clean.csv header order slightly wrong.

### Check results
- PASS north_q1_revenue
- PASS north_q1_orders
- PASS top_region
- PASS missing_amount_orders
- PASS duplicate_rows_removed
- PASS rule_money_in_cents
- PASS rule_meta_block
- FAIL rule_clean_csv: RULE: workspace/clean.csv has the required header order and one row per distinct order
