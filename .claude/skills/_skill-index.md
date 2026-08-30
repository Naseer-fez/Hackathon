# SKILL ROUTER

Load skills based on detected task type:

| Trigger | Skill | When |
|---------|-------|------|
| `.py`, ML/AI, data, training | `py-ml.md` | Python files, model work, data pipelines |
| `.tsx/.jsx`, components, UI | `react-framer.md` | React components, animations, UI |
| ANY file read/write optimization | `file-io.md` | Token-efficient file operations |
| Coding standards, naming, types | `core-rules.md` | Abbreviations, conventions, patterns |

## Loading Protocol
1. Parse user intent → match trigger keywords
2. Inject matching skill(s) into context ONCE per session
3. Cache skill rules → never re-read unless context resets
4. For multi-domain tasks → load all relevant skills simultaneously
5. `core-rules.md` abbreviations apply across all skills
