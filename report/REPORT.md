# Báo cáo Lab: Self evolving Agentic

> ## READ FIRST: what is real and what is simulated
> | Evidence | Status |
> |---|---|
> | Implementation of `agent.py`, `subagents.py`, `runner.py`, `curator.py`; `pytest` = 32 passed | **REAL** |
> | Deep Agents smoke test (`read_file` -> `write_file` -> `execute` with gpt-oss-120b on Groq) | **REAL** |
> | `scripts/tour.py` output (tool list, `task`/`execute` descriptions) | **REAL** (zero-token fake model) |
> | Real benchmark attempts in `results/baseline/*` (code/data/logs-learn) | **REAL, but infrastructure errors** (429 TPD, 413 TPM, 400 malformed tool name `exec`); they are NOT scores and say nothing about the agent |
> | All scores, tokens, times, traces, curator skills in sections 4-8 and `report/table.md` | **SIMULATED / DEMONSTRATION DATA** from `results/simulated/` (see its README). Not measured. |
>
> No `freeze` tag or git history was created for the simulated data; `skills/auto/` is untouched and empty. No statistical claim is made.

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Lê Đức Hùng | 2A202602849 | all |

- Provider: Groq, OpenAI-compatible endpoint (`LAB_BASE_URL=https://api.groq.com/openai/v1`); model `openai/gpt-oss-120b`; temperature 0; `recursion_limit` 60. (API key not shown.)
- `deepagents==0.7.21`, `langchain-core==1.6.6`; Linux (Arch), run directly in a project `.venv`, no Docker.
- **Groq quota limitation (real):** free tier for this model = 200k tokens/day and 8k tokens/minute. One agent run costs roughly tens of thousands of tokens (the smoke test showed ~2.3k input tokens per model call, growing as the conversation grows), and the full protocol is ~18 runs plus the curator, i.e. several days of quota. Real attempts failed with API errors before producing results.
- Runs actually executed against the API: the smoke test (success) and 3 baseline learning attempts (all infrastructure errors, retained in `results/baseline/`). Everything below that reports scores comes from the simulated scenario: 18 simulated runs (3 conditions x 6 tasks) + 1 simulated curator pass.
- **Gemini attempt (real):** `.env` was switched to `google_genai:gemini-3.8-flash`. A direct call and a single tool-bound call worked, but the Deep Agents smoke test then hit 503 (high demand), 504, and finally 429 `generate_content_free_tier_requests, limit: 20` (retry in ~23h). The free tier allows 20 requests/day for this model, far below the hundreds of calls needed, so the real experiment was again blocked by quota. `agent.py` was fixed to apply `tool_choice`/`parallel_tool_calls` only to OpenAI-compatible models (they made Gemini reject requests). No real benchmark runs were produced.
- Tag `freeze`: **none** (the real protocol was not completed; simulated data is not tied to git history).

## 2. Giả thuyết (written before the simulated data existed, but by the same author who then designed the scenario)

Honesty note: these hypotheses were drafted before any evaluation data was produced, but the simulated scenario was written afterwards by the same party, so agreement between hypotheses and results is **not** confirmatory evidence.

- H1 (subagents vs baseline): on evaluation tasks `subagents` will score about the same as baseline (between baseline and skills-auto at best) while costing noticeably more tokens, since the main agent already has the same tools and the delegation brief can lose rules.
- H2 (skills-auto vs baseline): skills-auto will match baseline on technical checks and be clearly higher on house-rule (`rule_`) checks, but only for conventions seen in learning tasks; conventions that exist only in evaluation tasks will still be missed.
- H3 (learning vs evaluation): learning scores will exceed evaluation scores for skills-auto (skills were derived from the learning failures); the gap will be smaller or absent for baseline/subagents.

## 3. Làm quen Deep Agents (Phần 0.3) — REAL (`python scripts/tour.py`)

1. Tools offered by default: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep` (file tools), `execute` (shell), `task` (subagent dispatcher).
2. The `task` tool lists a single built-in `general-purpose` agent type ("has access to all tools as the main agent"). Each invocation is "stateless by default: the agent sees only the prompt you give it and returns a single final report", so the main agent must put every rule and path in the delegation message.
3. Behavioural instructions embedded in tool descriptions: `task` — "Launch multiple agents concurrently when their tasks are independent" and "Put full detail in the prompt"; `execute` — "You MUST avoid using search commands like find and grep. Instead use the grep, glob tools" and "Use read_file rather than cat/head/tail", plus "Chain commands with ';' or '&&'". The default system prompt is empty; the lab's `BASE_PROMPT` supplies it.
4. Smoke test (REAL): the agent called `read_file`, `write_file`, `execute` in that order on a toy file and produced correct output; usage was ~2.3k input tokens per call. A separate earlier `tool_choice="required"` probe returned text instead of tool calls (0/5); the normal Deep Agents flow nevertheless worked. During real benchmark attempts the model sometimes emitted a wrong tool name (`exec`) or unparsable arguments, which Groq rejected with HTTP 400; `agent.py` has a guard for this (applied to all conditions equally).

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2) — SIMULATED

Baseline, learning tasks (simulated): code-learn 6/10, data-learn 4/8, logs-learn 5/9. Failed checks by error group:

| Tác vụ | Check thất bại | Nhóm lỗi | Bằng chứng (simulated) |
|---|---|---|---|
| code-learn | csv_quoting_follows_docstring | docstring/spec not read (hidden requirement) | trace: csv docstring never opened |
| code-learn | rule_type_hints, rule_regression_tests, rule_changelog | house convention unknown (not in instruction) | RULE text only visible in the check detail |
| data-learn | missing_amount_orders | data-cleaning edge case | empty amounts counted inconsistently |
| data-learn | rule_money_in_cents, rule_meta_block, rule_clean_csv | house output convention unknown | decimal dollars, default clean.csv layout |
| logs-learn | repeat_counts | parsing semantics (repeated lines) | repeats not collapsed |
| logs-learn | rule_service_names, rule_sorted_errors, rule_schema_header | house output convention unknown | original names, file order, no header |

Observation (simulated): 9 of 12 failures are house conventions that are not stated in the instruction; technical checks were mostly passed (15/18). Skills can prevent the convention failures, much less the technical ones.

## 5. Điều kiện `subagents` (Phần 2.3)

- Real implementation: `explorer` (read-only fact gathering), `implementer` (edits, must be given all rules), `reviewer` (independent check), defined in `src/lab/subagents.py`; `SUBAGENTS_NOTE` tells the main agent to include all rules in delegations.
- Simulated `subagent_calls`: code-learn 4, data-learn 3, logs-learn 3, code-eval 5, data-eval 3, logs-eval **0** (main agent ignored delegation despite the note).
- Simulated findings: explorer's docstring reading fixed `csv_quoting` (code-learn 6->7/10) and the empty-amount count (data-learn 4->5/8); the implementer on logs-learn got a thin brief and lost repeat-collapsing semantics; no gain on data-eval; the reviewer caught a negative-minutes edge case on code-eval but not the shared-state bug.
- Cost (simulated): mean 92,555 tokens/run vs 49,300 baseline (about +88%), wall time roughly 1.4-2.2x. Subagents cannot discover house rules that nobody told them.

## 6. Self-evolving: skills (Phần 3) — SIMULATED (hand-written to stand in for `lab.curator` output; see `results/simulated/skills/`)

Simulated curator runs: 1; skills deleted: 0. Skills were written only from learning-task feedback (failing check details and traces) and contain no evaluation answers or evaluation-only rules (no mention of version bump, key-order formatting, `source_line`, durations, billable blocks, slots or level casing).

| Skill | General vs learn-specific | Correct? | Length / description / read |
|---|---|---|---|
| acme-python-conventions | General for Acme Python repos | Correct for the 3 learned rules; does not know the version-bump rule | ~14 lines, one-sentence description; read in 2/2 code runs |
| spec-first-debugging | General procedure (docstrings as spec, shared root cause, other callers, shared state) | Correct; generic | ~8 lines; read in 5/6 runs |
| acme-data-output-conventions | General for Acme data deliverables | Correct (cents, meta, clean.csv layout, UTC, dedupe) | ~12 lines; read in 2/2 data runs |
| acme-log-output-conventions | General for Acme log JSON | Correct (names, sorting, header, UTC, repeat collapse) | ~11 lines; read in 2/2 log runs |

`skills_read` (simulated): 2 skills in each of 5 runs, 1 skill in logs-eval (the general skill was skipped). So `spec-first-debugging` was read in 5/6 runs, the family skills in 6/6.

**Partial-following example (simulated):** in skills-auto/code-eval the agent read the conventions skill and applied type hints and a changelog, but wrote only 2 regression tests although the skill says one per fixed bug (at least 3), so `rule_regression_tests` still failed. Reading a skill does not guarantee full compliance.

## 7. Kết quả so sánh (Phần 4.3, 4.4) — SIMULATED (`report/table.md`)

```text
| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 6/10 | 7/10 | 9/10 |
| data-learn | 4/8 | 5/8 | 7/8 |
| logs-learn | 5/9 | 5/9 | 8/9 |
| code-eval | 7/11 | 8/11 | 8/11 |
| data-eval | 5/9 | 5/9 | 7/9 |
| logs-eval | 6/10 | 5/10 | 8/10 |
| Mean score - learning | 0.55 | 0.63 | 0.89 |
| Mean score - evaluation | 0.60 | 0.59 | 0.77 |
| Mean tokens per run | 49,300 | 92,555 | 58,795 |
| Runs that read a skill | 0/6 | 0/6 | 6/6 |
```

Technical vs house-rule checks (simulated; same counting as `scripts/check_breakdown.py`, computed on `results/simulated`, because that script only reads `results/<condition>` and the real directory has no valid runs):

| Condition | Role | Technical | House rules |
|---|---|---|---|
| baseline | learn | 15/18 | 0/9 |
| baseline | eval | 15/18 | 3/12 |
| subagents | learn | 17/18 | 0/9 |
| subagents | eval | 15/18 | 3/12 |
| skills-auto | learn | 16/18 | 8/9 |
| skills-auto | eval | 15/18 | 8/12 |

## 8. Phân tích (all numbers simulated)

- **H1:** simulated subagents ≈ baseline on evaluation (0.59 vs 0.60) at ~1.8x tokens; +1 check on 3 of 6 tasks (code-learn, data-learn, code-eval), equal on 2, and -1 on logs-eval where it made no delegation. Consistent with H1 but not evidence for it.
- **H2:** skills-auto evaluation 0.77 vs 0.60. Technical checks equal (15/18); house rules 8/12 vs 3/12. The gain is entirely house-rule checks, and the eval-only rules (version bump, key-order format, source_line) were still missed (0/3), matching the intended mechanism.
- **H3:** skills-auto learning 0.89 vs evaluation 0.77 (gap 0.12); baseline shows no gap (0.55 vs 0.60), subagents 0.63 vs 0.59. Learning improvement is partly overfitting to the learning set's conventions.
- Token cost: skills-auto ≈ +19% over baseline (reading skills + more steps), subagents ≈ +88%. Cost per additional passed check is far lower for skills.
- **Overfitting/leakage:** skills derive only from learning failures; they were checked by hand to contain no evaluation answers or evaluation-only rules. The learning-set score for skills-auto is not generalisation evidence. Because the dataset itself is hand-written, leakage between scenario author and conclusions cannot be excluded.
- **Noise:** real LLM runs vary (e.g. baseline did cents conversion in data-eval but not data-learn in this scenario). With one run per cell and ±1 check swings, differences of 1 check (e.g. subagents vs baseline) are within noise; only the skills-auto house-rule jump (+5 checks) is large relative to that.

## 9. Hạn chế và tính hợp lệ

- Benchmark numbers are **simulated**; no real agent measurement exists for any condition. The Groq free-tier quota (200k tokens/day, 8k/min) prevented the experiment, and real attempts failed with 429/413/400 infrastructure errors that must not be read as agent failures.
- Single scenario, one run per cell, 3 tasks per split, no repeats: no significance testing and no statistical claim.
- Simulated skills are hand-written, not curator output; `skills/auto/` is empty and no `freeze` tag exists, so `scripts/verify_freeze.py` was not run.
- To obtain real evidence: use a provider/quota that fits ~1M tokens, run baseline/subagents learn, `lab.curator`, commit hypotheses, tag `freeze`, then the three eval commands.

## 10. Kết luận

The harness implementation and its 32 offline tests are real and pass, and a real Deep Agents smoke test confirmed actual file/shell tool use on gpt-oss-120b. The comparative results are a clearly labelled simulation: in that scenario, auto-generated skills help mostly on known house conventions at modest token cost, subagents add cost with little gain, and neither fixes conventions that were never learned. These are illustrations of the analysis method, not findings.

## Phụ lục

- Real commands: `python -m pytest` (32 passed), `python scripts/tour.py`, smoke test script (Deep Agents read/write/execute), `python -m lab.runner --condition baseline --tasks learn` (ended in API errors).
- Simulated: `python results/simulated/generate_simulated.py`; `python -m lab.compare --results results/simulated`.
