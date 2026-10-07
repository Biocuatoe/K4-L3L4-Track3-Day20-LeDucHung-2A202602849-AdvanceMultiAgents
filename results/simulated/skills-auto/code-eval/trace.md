# SIMULATED / DEMONSTRATION DATA - not produced by a real API run (Groq free-tier quota prevented the real experiment).

## skills-auto / code-eval (eval)

### Tool-call sequence (abridged, simulated)
1. read_file skills/auto/acme-python-conventions/SKILL.md
2. read_file skills/auto/spec-first-debugging/SKILL.md
3. ls workspace
4. read_file workspace/<module>.py (docstrings)
5. execute `python -m pytest -q workspace` (failing)
6. edit_file <shared helper>
7. edit_file <other callers / remaining functions>
8. execute `python -m pytest -q workspace` (re-run)
9. ... (abridged; 28 tool calls in total in the scenario)

### Final message (simulated)
PARTIAL FOLLOW: read the conventions skill, added type hints and a changelog, but wrote only 2 regression tests (skill says one per bug, at least 3). New version-bump convention is not in any skill.

### Check results
- PASS visible_suite_passes
- PASS tests_not_modified
- PASS parse_duration_all_formats
- PASS other_caller_fixed
- PASS billable_blocks_round_up
- FAIL add_slot_no_shared_state: two Schedule objects share one slot list (mutable default argument still present)
- PASS negative_minutes_rejected
- PASS rule_type_hints
- FAIL rule_regression_tests: RULE: add tests/test_regressions.py with one test function per bug fixed (at least 3); the file must pass.
- PASS rule_changelog
- FAIL rule_version_bump: RULE: increment the patch number of __version__ once per fix session.
