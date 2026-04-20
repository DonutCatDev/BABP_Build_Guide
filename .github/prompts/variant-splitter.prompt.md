# Variant Splitter

Split an assembly into base + variant structure.

## Input
Use the provided content.

## Tasks

1. ANALYZE
- Identify shared steps (base)
- Identify variant-specific steps
- Identify variant-specific materials

2. STRUCTURE
- Define base content
- Define each variant cleanly
- Remove duplication

3. YAML OUTPUT
Provide updated section structure compatible with materials.yml

4. INSTRUCTION GROUPING
Provide:
- Base instruction block
- Variant instruction blocks

## VALIDATION
- No duplication between base and variants
- Variants are clearly separated
- Naming is consistent

## Constraints
- Do NOT generate full markdown pages
- Focus only on structure

## Output
Structured YAML + instruction grouping