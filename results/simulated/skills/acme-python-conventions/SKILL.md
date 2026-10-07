---
name: acme-python-conventions
description: Apply Acme Python team conventions (type hints on public functions, one regression test per bug, CHANGELOG entries) whenever you modify a Python package.
---

# Acme Python conventions

Use when you fix or change code in a Python package that Acme's review bot will check.

1. Public functions (names not starting with `_`) need type annotations on every parameter and on the return value.
2. Add `tests/test_regressions.py` with one test function per bug you fix (at least 3 when you fix 3 or more bugs). Run it and make sure it passes. Do not edit existing test files.
3. Record each fix in `CHANGELOG.md` under the heading `## Unreleased`, one bullet per fix.
4. Before finishing, run the full test suite and list the files you changed.

Check: re-read the task's list of fixed bugs and count your regression tests against it.
