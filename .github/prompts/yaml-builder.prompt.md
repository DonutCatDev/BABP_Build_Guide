# YAML Materials Builder

Extract structured materials from an assembly section.

Follow ALL rules in `../copilot-instructions.md`.

## Input
Use the provided text.

## Tasks (STRICT ORDER)

1. IDENTIFY MATERIALS
- Components
- Hardware (with quantities)
- Consumables

2. NORMALIZE
- Reuse existing IDs if present
- Otherwise create new IDs following naming rules
- Ensure consistent labeling

3. STRUCTURE
Output ONLY valid YAML:

sections:
  [section-name]:
    base:
    variants (if applicable)

4. VALIDATION
- No duplicate entries
- No inconsistent naming
- Hardware includes quantities
- Variants separated from base

## Constraints
- Do NOT generate markdown
- Do NOT invent materials
- Do NOT duplicate global entries

## Output
Return ONLY the YAML block