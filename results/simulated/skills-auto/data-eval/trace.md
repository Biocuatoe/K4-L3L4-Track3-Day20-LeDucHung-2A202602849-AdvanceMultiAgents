# SIMULATED / DEMONSTRATION DATA - not produced by a real API run (Groq free-tier quota prevented the real experiment).

## skills-auto / data-eval (eval)

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
10. ... (abridged; 17 tool calls in total in the scenario)

### Final message (simulated)
Cents, meta and clean.csv layout from the skill; the new eval-only formatting rule was not covered.

### Check results
- PASS march_revenue_utc
- PASS march_orders_utc
- PASS top_category
- FAIL missing_total_orders: wrong count of orders with an empty total
- PASS duplicate_events_removed
- PASS rule_money_in_cents
- PASS rule_meta_block
- PASS rule_clean_csv
- FAIL rule_sorted_keys_format: RULE: key-order / number-format rule for answer.json not met
