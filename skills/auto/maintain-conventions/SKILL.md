---
name: maintain-conventions
description: Use this skill to ensure code adheres to Acme Python team conventions (type hints, regression tests, changelog updates).
---
1. Add type annotations to every public function: annotate all parameters and the return type.  
2. After fixing a bug, create a new test in `tests/test_regressions.py` that reproduces the failure and passes.  
3. Add a corresponding entry in `CHANGELOG.md` under `## Unreleased` in the form `- fix(<function name>): <short description>`.  
4. Run `flake8` or similar linters to catch missing annotations or style issues.  
5. Verify that the test suite passes before committing.  
6. Keep the changelog updated for every change that affects public behavior.  
7. Ensure that any new helper functions are also documented and typed.
