# SIMULATED / DEMONSTRATION DATA - not produced by a real API run (Groq free-tier quota prevented the real experiment).

## subagents / data-eval (eval)

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
11. ... (abridged; 24 tool calls in total in the scenario)

### Final message (simulated)
No gain over baseline; delegation cost only.

### Check results
- PASS march_revenue_utc
- PASS march_orders_utc
- PASS top_category
- FAIL missing_total_orders: wrong count of orders with an empty total
- PASS duplicate_events_removed
- PASS rule_money_in_cents
- FAIL rule_meta_block: RULE: answer.json has an object `meta` with the required keys
- FAIL rule_clean_csv: RULE: workspace/clean.csv has the required header order and one row per distinct order
- FAIL rule_sorted_keys_format: RULE: key-order / number-format rule for answer.json not met
