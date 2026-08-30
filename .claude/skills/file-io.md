# TOKEN-EFFICIENT FILE I/O

## Read Protocol
1. **First pass**: Extract ONLY FN/class signatures + type hints
2. **Second pass** (if needed): Read specific FN implementation only
3. **Never**: Read entire large files; use targeted line ranges

### Line Range Syntax
```
file.py:L15-L42    # Specific FN
file.py:L10-L25    # Class definition only
file.py:L1-L15     # Imports section
```

## Write Protocol
1. **Small changes**: Output only the modified FN/block
2. **New files**: Full output acceptable
3. **Large mods**: Use search/replace blocks
4. **Never**: Rewrite unchanged code sections

### Search/Replace Format
```
<<<<<<< SEARCH
existing_code_line(s)
=======
new_code_line(s)
>>>>>>> REPLACE
```

## Token Budget
| Operation | Budget |
|-----------|--------|
| File read | Signatures first |
| File write | Changed sections only |
| CTX summary | <200 tokens/file |
| ERR output | Stack trace + 3 lines |

## Anti-Patterns [NEVER DO]
- ❌ Reading entire files when only a FN signature is needed
- ❌ Rewriting unchanged code sections
- ❌ Outputting full file when only 1 FN changed
- ❌ Including blank lines and comments in read summaries
