> **SIMULATED / DEMONSTRATION DATA.** Not from a real API run (Groq quota). Source: results/simulated/. Mean tokens are over 6 runs per condition.

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 6/10 | 7/10 | 9/10 |
| data-learn | 4/8 | 5/8 | 7/8 |
| logs-learn | 5/9 | 5/9 | 8/9 |
| code-eval | 7/11 | 8/11 | 8/11 |
| data-eval | 5/9 | 5/9 | 7/9 |
| logs-eval | 6/10 | 5/10 | 8/10 |
| **Mean score - learning tasks** | 0.55 | 0.63 | 0.89 |
| **Mean score - evaluation tasks** | 0.60 | 0.59 | 0.77 |
| **Mean tokens per run** | 49,300 | 92,555 | 58,795 |
| **Runs that read a skill** | 0/6 | 0/6 | 6/6 |
