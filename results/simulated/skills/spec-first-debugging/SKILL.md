---
name: spec-first-debugging
description: General procedure for fixing bugs where docstrings are the specification: read docstrings, find the shared root cause, check all callers.
---

# Spec-first debugging

1. Read every docstring in the package before editing; the docstring is the specification, visible tests may be incomplete.
2. If several tests fail, look for a shared helper that is their common cause and fix it once.
3. Search for other callers of a helper you changed (`grep`) and make sure they still behave correctly.
4. Look for mutable default arguments and other shared state when objects behave inconsistently between instances.
5. Run the tests after each change; never edit the existing tests to make them pass.
