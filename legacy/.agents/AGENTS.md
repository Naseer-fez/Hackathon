# PROJECT RULES [ALWAYS ACTIVE]

## Immutable Rules
- [R1] Type hints required on all Python functions
- [R2] Components must be <100 lines; decompose if larger
- [R3] No hardcoded secrets; use env vars only
- [R4] All async ops use async/await; no callbacks
- [R5] Imports: absolute paths only, no relative imports
- [R6] Error handling: specific exceptions, never bare `except:`
- [R7] Git commits: conventional commits format only
- [R8] Tests must exist for any new logic file

## File Naming
- Python: `snake_case.py`
- React: `PascalCase.tsx`
- Tests: `test_<name>.py` or `<Name>.test.tsx`
- Utils: `<domain>.utils.py` or `<domain>.utils.ts`

## Configuration
- Never hardcode file paths, model names, API endpoints, or voice names
- Use config files (YAML/JSON/TOML/.env), env vars, or CLI args
- All values must be changeable without modifying source code
