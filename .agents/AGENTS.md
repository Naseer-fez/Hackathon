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
- [R9] Truthfulness: Never synthesize fake/mock domain data; if no AI model is active, faithfully report unavailability
- [R10] Mandatory GPU Acceleration: Target NVIDIA RTX 3050 6GB GPU (cuda:0). All PyTorch tensor operations and llama.cpp GGUF inference must execute on CUDA. Never install or revert to +cpu wheels. Fail fast or explicitly report CUDA status at boot.


## File Naming
- Python: `snake_case.py`
- React: `PascalCase.tsx`
- Tests: `test_<name>.py` or `<Name>.test.tsx`
- Utils: `<domain>.utils.py` or `<domain>.utils.ts`

## Configuration
- Never hardcode file paths, model names, API endpoints, or voice names
- Use config files (YAML/JSON/TOML/.env), env vars, or CLI args
- All values must be changeable without modifying source code
