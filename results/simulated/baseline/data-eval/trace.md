# SIMULATED / DEMONSTRATION DATA - not produced by a real API run (Groq free-tier quota prevented the real experiment).

## baseline / data-eval (eval)

### Tool-call sequence (abridged, simulated)
1. ls workspace
2. read_file workspace/<input> (head)
3. write_file workspace/analyze.py
4. execute `python workspace/analyze.py`
5. write_file workspace/answer.json
6. write_file workspace/clean.csv
7. execute validation snippet
8. ... (abridged; 14 tool calls in total in the scenario)

### Final message (simulated)
Cents conversion done this time (noise vs. data-learn) but meta block and clean.csv layout missed.

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
