---
name: follow-docstring-spec
description: Use this skill when implementing or modifying a function to guarantee its behavior matches the docstring and test expectations.
---
1. Read the function’s docstring fully, noting input types, output format, and any edge‑case behavior.  
2. Identify all examples and constraints mentioned (e.g., rounding rules, quoting rules, special string formats).  
3. Write unit tests that cover each example and edge case before coding the logic.  
4. Implement the function, verifying each test passes.  
5. If the function must parse or format data, use standard libraries (e.g., `csv`, `decimal`, `re`) to avoid re‑implementing complex logic.  
6. For numeric rounding, use `Decimal` with the appropriate rounding mode (`ROUND_HALF_UP`).  
7. For CSV quoting, follow RFC 4180: wrap fields containing commas or quotes in double quotes and escape internal quotes by doubling them.  
8. For parsing prices, strip currency symbols, commas, and parentheses, then convert to a numeric type.  
9. After implementation, run the full test suite to confirm no hidden failures.  
10. Document any deviations from the docstring only if they are intentional and update the docstring accordingly.
