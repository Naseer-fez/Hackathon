---
name: skill-router
description: >-
  Routing index for all available skills. Use this to determine which skill(s)
  to activate based on the user's task type. Load this when you need to decide
  which domain skill applies to the current request.
---

# Skill Router

| Trigger | Skill | When |
|---------|-------|------|
| `.py`, ML/AI, data, training | `py-ml` | Python files, model work, data pipelines |
| `.tsx/.jsx`, components, UI | `react-framer` | React components, animations, UI |
| BIS, Indian Standards, QCO, GeM, Tender | `bis-specai` | Indian Standards recommendation & tender auditing |
| ANY file read/write optimization | `file-io` | Token-efficient file operations |
| Coding standards, naming, types | `core-rules` | Abbreviations, conventions, patterns |

## Loading Protocol
1. Parse user intent → match trigger keywords
2. Activate matching skill(s) — read their `SKILL.md`
3. For multi-domain tasks → activate all relevant skills
4. `core-rules` abbreviations apply across all skills
