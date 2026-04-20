# Master Convert

Convert a BABP assembly section into structured MkDocs + MkSlides documentation.

Follow ALL rules in `../copilot-instructions.md`.

## Input
Use the selected text or ask for it.

## Execution Order (STRICT)

1. STRUCTURE ANALYSIS
- Identify section name
- Detect variants (if any)
- Separate base vs variant content BEFORE proceeding

2. MATERIALS (SOURCE OF TRUTH)
- Extract all components, hardware, consumables
- Normalize naming using existing IDs
- Create/update `/docs/data/materials.yml`
- Use base + variant structure ONLY
- Do NOT proceed until YAML is complete

3. MATERIALS PAGE
- Generate `/docs/assembly/[section]/materials.md`
- Derived ONLY from YAML
- Include:
  - Base materials
  - Variant-specific materials

4. INSTRUCTIONS (MkDocs)
- Generate `index.md`
- Include:
  - Overview
  - Materials link
  - Step-by-step instructions
- One action per step
- Maintain orientation + alignment clarity

5. MEDIA PLACEHOLDERS
- Insert placeholders using naming convention:
  - [section]_[step-number]_picture[x].png
  - [section]_[step-number]_video[x].mp4
- Do NOT invent arbitrary names

6. VALIDATION (MANDATORY)
- No duplicate materials
- Base and variants are clearly separated
- YAML is the only source of materials
- Naming rules enforced
- No spaces in filenames

## Output Format (STRICT)
Return clearly separated sections:
- YAML
- materials.md
- index.md