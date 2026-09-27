# BABP documentation repository instructions

Read `AGENTS.md` and `CONTRIBUTING.md` before changing this repository. `AGENTS.md` is the shared, tool-neutral contract for AI-assisted work; do not create a conflicting Copilot-only workflow.

Critical rules:

- Edit instruction content in source Markdown under `docs/`.
- Treat `docs/data/materials.yml` as the source of truth for all material data and material-card images.
- Do not hand-edit generated material pages or the generated navigation block.
- Run `python scripts/dev.py generate` after material, page-layout, or navigation changes.
- Run `python scripts/dev.py check` before considering work complete.
- Never edit or commit `site/`; it is disposable output.
- Preserve unrelated work in the existing worktree.
- Keep media under `docs/media/<section>/`, inspect ambiguous images visually, and do not reuse a broad assembly image for unrelated component cards.
- Preserve explicit source-coverage gaps; do not invent procedures or quantities.
- Treat `scripts/rebuild_assembly_pages_from_docx.py` as a BABP baseline-specific bulk tool, not a general DOCX importer. Do not run it for routine edits or against an unrelated document.
