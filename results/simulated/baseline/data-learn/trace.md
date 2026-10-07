# SIMULATED / DEMONSTRATION DATA - not produced by a real API run (Groq free-tier quota prevented the real experiment).

## baseline / data-learn (learn)

### Tool-call sequence (abridged, simulated)
1. ls workspace
2. read_file workspace/<input> (head)
3. write_file workspace/analyze.py
4. execute `python workspace/analyze.py`
5. write_file workspace/answer.json
6. write_file workspace/clean.csv
7. execute validation snippet
8. ... (abridged; 15 tool calls in total in the scenario)

### Final message (simulated)
Answered with decimal dollars, wrote a clean.csv without the Acme layout; miscounted empty amounts (treated '0' strings differently).

### Check results
- PASS north_q1_revenue
- PASS north_q1_orders
- PASS top_region
- FAIL missing_amount_orders: wrong count of orders with an empty amount
- PASS duplicate_rows_removed
- FAIL rule_money_in_cents: RULE: money values in answer.json are integer cents
- FAIL rule_meta_block: RULE: answer.json has an object `meta` with the required keys
- FAIL rule_clean_csv: RULE: workspace/clean.csv has the required header order and one row per distinct order
