# SIMULATED / DEMONSTRATION DATA - not produced by a real API run (Groq free-tier quota prevented the real experiment).

## subagents / data-learn (learn)

### Tool-call sequence (abridged, simulated)
1. task(explorer): gather docstrings/inputs
2. task(implementer): apply changes (brief lists rules)
3. task(reviewer): independent check
4. ls workspace
5. read_file workspace/<input> (head)
6. write_file workspace/analyze.py
7. execute `python workspace/analyze.py`
8. write_file workspace/answer.json
9. write_file workspace/clean.csv
10. execute validation snippet
11. ... (abridged; 26 tool calls in total in the scenario)

### Final message (simulated)
Explorer's checklist fixed the empty-amount count; house rules still absent.

### Check results
- PASS north_q1_revenue
- PASS north_q1_orders
- PASS top_region
- PASS missing_amount_orders
- PASS duplicate_rows_removed
- FAIL rule_money_in_cents: RULE: money values in answer.json are integer cents
- FAIL rule_meta_block: RULE: answer.json has an object `meta` with the required keys
- FAIL rule_clean_csv: RULE: workspace/clean.csv has the required header order and one row per distinct order
