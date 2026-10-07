# SIMULATED / DEMONSTRATION DATA

**Everything in this directory (except this README and the generator's code) is SIMULATED. None of it came from a real model/API run.**

Why: the real experiment could not be completed because the Groq free tier for `openai/gpt-oss-120b` allows only 200k tokens/day (and 8k tokens/minute), and the real attempts ended in 429/413/400 API errors. Those real failure records remain untouched in `results/baseline/` and are infrastructure evidence, not scores.

- `<condition>/<task>/run.json`, `trace.md`: invented from one hand-written scenario in `generate_simulated.py` (same schema as real runs, plus `"SIMULATED": true`).
- `skills/`: simulated "curator-generated" skills. They were hand-written for this demonstration, not produced by `lab.curator`. `skills/auto/` in the repo root is unchanged (empty).
- No `freeze` git tag or git history was created for this data.
- Scores, tokens and times are plausible illustrations, not measurements; no statistical claim can be drawn from them.

Reproduce the table: `python generate_simulated.py` then `python -m lab.compare --results results/simulated`.
