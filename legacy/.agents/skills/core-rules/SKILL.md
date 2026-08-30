---
name: core-rules
description: >-
  Project-wide abbreviations, naming conventions, and coding patterns.
  Use when you need to reference standard abbreviations or check naming
  conventions for any file type.
---

# Core Rules & Abbreviations

## Abbreviations (use across all skills)
| ABBR | Meaning |
|------|---------|
| CP | Component |
| FN | Function |
| VAR | Variable |
| MOD | Module |
| CTX | Context |
| PROP | Property |
| ST | State |
| EF | Side Effect |
| RET | Return |
| ASYNC | Asynchronous |
| ERR | Error |
| VAL | Value |

## Anti-Patterns [NEVER DO]
- ❌ Bare `except:` — always catch specific exceptions
- ❌ Hardcoded secrets or config values in source
- ❌ Missing type hints on function signatures
- ❌ Files >100 lines without decomposition plan
- ❌ Relative imports in Python
- ❌ Callback-based async — use async/await
