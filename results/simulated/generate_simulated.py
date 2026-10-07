#!/usr/bin/env python3
"""SIMULATED / DEMONSTRATION DATA generator. NOT a real API run.

Writes results/simulated/<condition>/<task>/{run.json,trace.md} and results/simulated/skills/*/SKILL.md from ONE
hand-specified scenario (below). Nothing here calls a model. See results/simulated/README.md.

    python results/simulated/generate_simulated.py
    python -m lab.compare --results results/simulated > report/table_simulated.md
"""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
BANNER = "SIMULATED / DEMONSTRATION DATA - not produced by a real API run (Groq free-tier quota prevented the real experiment)."
EMPTY_SHA = hashlib.sha256(b"").hexdigest()

# task -> (role, ordered check names). Names/order copied from tasks/<id>/check.py.
TASKS = {
    "code-learn": ("learn", ["visible_suite_passes", "tests_not_modified", "parse_price_all_formats", "other_caller_fixed",
                             "discount_rounds_half_up", "low_stock_follows_docstring", "csv_quoting_follows_docstring",
                             "rule_type_hints", "rule_regression_tests", "rule_changelog"]),
    "data-learn": ("learn", ["north_q1_revenue", "north_q1_orders", "top_region", "missing_amount_orders",
                             "duplicate_rows_removed", "rule_money_in_cents", "rule_meta_block", "rule_clean_csv"]),
    "logs-learn": ("learn", ["valid_structure", "entry_count", "timestamps_utc", "exception_fields", "repeat_counts",
                             "counts_by_service", "rule_service_names", "rule_sorted_errors", "rule_schema_header"]),
    "code-eval": ("eval", ["visible_suite_passes", "tests_not_modified", "parse_duration_all_formats", "other_caller_fixed",
                           "billable_blocks_round_up", "add_slot_no_shared_state", "negative_minutes_rejected",
                           "rule_type_hints", "rule_regression_tests", "rule_changelog", "rule_version_bump"]),
    "data-eval": ("eval", ["march_revenue_utc", "march_orders_utc", "top_category", "missing_total_orders",
                           "duplicate_events_removed", "rule_money_in_cents", "rule_meta_block", "rule_clean_csv",
                           "rule_sorted_keys_format"]),
    "logs-eval": ("eval", ["valid_structure", "entry_count", "timestamps_utc", "levels_uppercase", "repeat_counts",
                           "counts_by_service", "rule_service_names", "rule_sorted_errors", "rule_schema_header",
                           "rule_source_line"]),
}

# Generic, non-answer failure details (no expected values are quoted).
DETAIL = {
    "csv_quoting_follows_docstring": "to_csv_row did not quote a field containing a comma and a double quote as the docstring says",
    "missing_amount_orders": "wrong count of orders with an empty amount",
    "repeat_counts": "repeat_count wrong for collapsed repeated lines",
    "add_slot_no_shared_state": "two Schedule objects share one slot list (mutable default argument still present)",
    "missing_total_orders": "wrong count of orders with an empty total",
    "levels_uppercase": "level values not normalised to upper-case in all entries",
    "rule_type_hints": "RULE: every public function has type annotations on all parameters and the return value",
    "rule_regression_tests": "RULE: add tests/test_regressions.py with one test function per bug fixed (at least 3); the file must pass.",
    "rule_changelog": "RULE: record each fix in CHANGELOG.md under '## Unreleased' as bullets",
    "rule_version_bump": "RULE: increment the patch number of __version__ once per fix session.",
    "rule_money_in_cents": "RULE: money values in answer.json are integer cents",
    "rule_meta_block": "RULE: answer.json has an object `meta` with the required keys",
    "rule_clean_csv": "RULE: workspace/clean.csv has the required header order and one row per distinct order",
    "rule_sorted_keys_format": "RULE: key-order / number-format rule for answer.json not met",
    "rule_service_names": "RULE: service names must be lower-case with '-' replaced by '_'",
    "rule_sorted_errors": "RULE: `errors` must be sorted by service, then by timestamp_utc",
    "rule_schema_header": "RULE: top-level object must carry the required schema header fields",
    "rule_source_line": "RULE: every entry must carry the required source_line field",
}

# (condition, task) -> failed checks, seconds, tokens (input, output), tool_calls, subagent_calls, skills_read, notes
S = {}
def r(cond, task, fails, sec, tin, tout, tools, subs, skills, note):
    S[(cond, task)] = dict(fails=fails, sec=sec, tin=tin, tout=tout, tools=tools, subs=subs, skills=skills, note=note)

# ---- baseline ----
r("baseline", "code-learn", ["csv_quoting_follows_docstring", "rule_type_hints", "rule_regression_tests", "rule_changelog"], 71.3, 43870, 3120, 19, 0, 0,
  "Fixed parse_price and its other caller, half-up rounding and low_stock; skipped the csv docstring and never touched conventions (none were mentioned in the instruction).")
r("baseline", "data-learn", ["missing_amount_orders", "rule_money_in_cents", "rule_meta_block", "rule_clean_csv"], 58.9, 38240, 2790, 15, 0, 0,
  "Answered with decimal dollars, wrote a clean.csv without the Acme layout; miscounted empty amounts (treated '0' strings differently).")
r("baseline", "logs-learn", ["repeat_counts", "rule_service_names", "rule_sorted_errors", "rule_schema_header"], 64.2, 47110, 3560, 17, 0, 0,
  "Parsed multi-line stack traces and timestamps correctly; kept original service names, no schema header, entries in file order.")
r("baseline", "code-eval", ["add_slot_no_shared_state", "rule_regression_tests", "rule_changelog", "rule_version_bump"], 83.6, 61480, 4010, 24, 0, 0,
  "Hit one malformed tool call ('exec') that the harness recovery note corrected (cf. the REAL 400s observed earlier); added type hints but no tests/changelog/version bump.")
r("baseline", "data-eval", ["missing_total_orders", "rule_meta_block", "rule_clean_csv", "rule_sorted_keys_format"], 52.7, 35960, 2540, 14, 0, 0,
  "Cents conversion done this time (noise vs. data-learn) but meta block and clean.csv layout missed.")
r("baseline", "logs-eval", ["levels_uppercase", "rule_service_names", "rule_schema_header", "rule_source_line"], 66.8, 49730, 3390, 18, 0, 0,
  "Correct counts and UTC timestamps; mixed-case levels left as-is; no house rules applied.")

# ---- subagents ----
r("subagents", "code-learn", ["rule_type_hints", "rule_regression_tests", "rule_changelog"], 158.4, 96540, 7210, 31, 4, 0,
  "explorer read docstrings and reported them, which helped csv_quoting; implementer was not given conventions (there were none to give).")
r("subagents", "data-learn", ["rule_money_in_cents", "rule_meta_block", "rule_clean_csv"], 121.7, 79320, 5830, 26, 3, 0,
  "Explorer's checklist fixed the empty-amount count; house rules still absent.")
r("subagents", "logs-learn", ["repeat_counts", "rule_service_names", "rule_sorted_errors", "rule_schema_header"], 139.2, 91880, 6460, 29, 3, 0,
  "Implementer received a thin brief (no mention of repeat collapsing) so the duplicated-line semantics were lost.")
r("subagents", "code-eval", ["add_slot_no_shared_state", "rule_regression_tests", "rule_changelog"], 171.5, 118250, 8040, 36, 5, 0,
  "Reviewer subagent caught a negative-minutes edge case; the shared-state bug and the conventions were missed. Version bump was done incidentally.")
r("subagents", "data-eval", ["missing_total_orders", "rule_meta_block", "rule_clean_csv", "rule_sorted_keys_format"], 112.9, 74610, 5320, 24, 3, 0,
  "No gain over baseline; delegation cost only.")
r("subagents", "logs-eval", ["levels_uppercase", "rule_service_names", "rule_sorted_errors", "rule_schema_header", "rule_source_line"], 94.6, 57890, 3980, 20, 0, 0,
  "Main agent never used `task` (subagent_calls = 0) despite SUBAGENTS_NOTE; behaved like baseline with worse sorting luck.")

# ---- skills-auto ----
r("skills-auto", "code-learn", ["csv_quoting_follows_docstring"], 86.4, 58320, 3870, 24, 0, 2,
  "Read both python skills first; applied hints/tests/changelog. (Learning task: skills were derived from it, so this is not generalisation evidence.)")
r("skills-auto", "data-learn", ["rule_clean_csv"], 66.1, 46850, 3110, 18, 0, 2,
  "Cents and meta block applied; clean.csv header order slightly wrong.")
r("skills-auto", "logs-learn", ["repeat_counts"], 77.8, 56240, 3640, 21, 0, 2,
  "All three house rules applied; repeat collapsing still wrong.")
r("skills-auto", "code-eval", ["add_slot_no_shared_state", "rule_regression_tests", "rule_version_bump"], 97.3, 71460, 4530, 28, 0, 2,
  "PARTIAL FOLLOW: read the conventions skill, added type hints and a changelog, but wrote only 2 regression tests (skill says one per bug, at least 3). New version-bump convention is not in any skill.")
r("skills-auto", "data-eval", ["missing_total_orders", "rule_sorted_keys_format"], 59.4, 44190, 3020, 17, 0, 2,
  "Cents, meta and clean.csv layout from the skill; the new eval-only formatting rule was not covered.")
r("skills-auto", "logs-eval", ["levels_uppercase", "rule_source_line"], 72.5, 54070, 3470, 20, 0, 1,
  "Read only the log-output skill (skipped the general one); the three learned rules applied; new source_line rule not covered.")

SKILLS = {
    "acme-python-conventions": (
        "Apply Acme Python team conventions (type hints on public functions, one regression test per bug, CHANGELOG entries) whenever you modify a Python package.",
        """# Acme Python conventions

Use when you fix or change code in a Python package that Acme's review bot will check.

1. Public functions (names not starting with `_`) need type annotations on every parameter and on the return value.
2. Add `tests/test_regressions.py` with one test function per bug you fix (at least 3 when you fix 3 or more bugs). Run it and make sure it passes. Do not edit existing test files.
3. Record each fix in `CHANGELOG.md` under the heading `## Unreleased`, one bullet per fix.
4. Before finishing, run the full test suite and list the files you changed.

Check: re-read the task's list of fixed bugs and count your regression tests against it.
"""),
    "spec-first-debugging": (
        "General procedure for fixing bugs where docstrings are the specification: read docstrings, find the shared root cause, check all callers.",
        """# Spec-first debugging

1. Read every docstring in the package before editing; the docstring is the specification, visible tests may be incomplete.
2. If several tests fail, look for a shared helper that is their common cause and fix it once.
3. Search for other callers of a helper you changed (`grep`) and make sure they still behave correctly.
4. Look for mutable default arguments and other shared state when objects behave inconsistently between instances.
5. Run the tests after each change; never edit the existing tests to make them pass.
"""),
    "acme-data-output-conventions": (
        "Output conventions for data-analysis answers: integer cents, a meta block, and the Acme clean.csv layout.",
        """# Acme data output conventions

Use when answering questions from CSV/JSON data and writing deliverable files.

- Money values in `answer.json` are integer cents (a value of 12.34 USD is written 1234), never floats.
- `answer.json` contains a `meta` object recording the source input file name and the other fields the task instruction requests.
- Write `workspace/clean.csv` with the header order the instruction gives, one row per distinct record, timestamps normalised to UTC (ISO 8601).
- Normalise mixed date formats and time zones to UTC before filtering by date; remove exact duplicates before aggregating and count them.
- Re-open the written files and validate them with a short script before finishing.
"""),
    "acme-log-output-conventions": (
        "Output conventions for log-triage JSON: normalised service names, sorted errors, and the schema header.",
        """# Acme log output conventions

Use when turning log files into `errors.json`.

- Service names are lower-case with `-` replaced by `_` (for example `my-service` becomes `my_service`).
- The `errors` list is sorted by service, then by `timestamp_utc`, ascending.
- The top-level object carries `"schema_version": 2` and `"generated_by": "log-triage"`.
- Convert every timestamp to UTC; treat multi-line stack traces as one entry and collapse consecutive identical lines into one entry with a repeat count.
- Validate by loading the JSON again and checking ordering programmatically.
"""),
}
SKILL_DIR_OF = {"code": ["acme-python-conventions", "spec-first-debugging"], "data": ["acme-data-output-conventions", "spec-first-debugging"],
                "logs": ["acme-log-output-conventions", "spec-first-debugging"]}


def skills_hash():
    h = hashlib.sha256()
    for p in sorted((OUT / "skills").rglob("SKILL.md")):
        h.update(str(p.relative_to(OUT / "skills")).encode() + p.read_bytes())
    return h.hexdigest()


def steps(cond, task, d):
    fam = task.split("-")[0]
    lines = []
    if d["skills"]:
        for s in SKILL_DIR_OF[fam][: d["skills"]]:
            lines.append(f"read_file skills/auto/{s}/SKILL.md")
    base = {
        "code": ["ls workspace", "read_file workspace/<module>.py (docstrings)", "execute `python -m pytest -q workspace` (failing)", "edit_file <shared helper>",
                 "edit_file <other callers / remaining functions>", "execute `python -m pytest -q workspace` (re-run)"],
        "data": ["ls workspace", "read_file workspace/<input> (head)", "write_file workspace/analyze.py", "execute `python workspace/analyze.py`",
                 "write_file workspace/answer.json", "write_file workspace/clean.csv", "execute validation snippet"],
        "logs": ["ls workspace", "read_file workspace/app.log (head)", "write_file workspace/parse_logs.py", "execute `python workspace/parse_logs.py`",
                 "write_file workspace/errors.json", "execute validation snippet"],
    }[fam]
    if cond == "subagents" and d["subs"]:
        lines += [f"task(explorer): gather docstrings/inputs", f"task(implementer): apply changes (brief lists rules)"]
        if d["subs"] > 2:
            lines.append("task(reviewer): independent check")
    lines += base
    lines.append(f"... (abridged; {d['tools']} tool calls in total in the scenario)")
    return lines


def main():
    (OUT / "skills").mkdir(exist_ok=True)
    for name, (desc, body) in SKILLS.items():
        (OUT / "skills" / name).mkdir(exist_ok=True)
        (OUT / "skills" / name / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {desc}\n---\n\n{body}", encoding="utf-8")
    sk_sha = skills_hash()
    day = {"baseline": "2026-10-09T08", "subagents": "2026-10-09T10", "skills-auto": "2026-10-10T09"}
    for (cond, task), d in S.items():
        role, names = TASKS[task]
        total = len(names)
        checks = [{"name": n, "passed": n not in d["fails"], "detail": DETAIL.get(n, "check failed (simulated)") if n in d["fails"] else ""} for n in names]
        assert all(f in names for f in d["fails"]), (cond, task)
        passed = sum(c["passed"] for c in checks)
        run = {
            "SIMULATED": True, "data_label": BANNER, "task": task, "condition": cond, "role": role, "error": None,
            "timestamp": f"{day[cond]}:{(len(task) * 7 + len(cond) * 3) % 50 + 5:02d}:00+00:00 (simulated)",
            "skills_sha256": sk_sha if cond == "skills-auto" else EMPTY_SHA,
            "seconds": d["sec"], "tokens": {"input": d["tin"], "output": d["tout"], "total": d["tin"] + d["tout"]},
            "tool_calls": d["tools"], "subagent_calls": d["subs"], "skills_read": d["skills"], "skills_modified": False,
            "final_message": f"[SIMULATED] {d['note']}", "score": round(passed / total, 4), "passed": passed, "total": total, "checks": checks,
        }
        p = OUT / cond / task
        p.mkdir(parents=True, exist_ok=True)
        (p / "run.json").write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        trace = [f"# {BANNER}", "", f"## {cond} / {task} ({role})", "", "### Tool-call sequence (abridged, simulated)"]
        trace += [f"{i + 1}. {s}" for i, s in enumerate(steps(cond, task, d))]
        trace += ["", "### Final message (simulated)", d["note"], "", "### Check results"]
        trace += [f"- {'PASS' if c['passed'] else 'FAIL'} {c['name']}" + (f": {c['detail']}" if c["detail"] else "") for c in checks]
        (p / "trace.md").write_text("\n".join(trace) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
