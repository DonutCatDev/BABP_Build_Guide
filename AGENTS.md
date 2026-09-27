# Instructions for AI Agents

This file is the tool-neutral onboarding contract for any AI agent working in this repository. Read it before making changes, then read `CONTRIBUTING.md` for the complete authoring and maintenance guide.

## Project purpose

This repository publishes the BABP assembly guide as a MkDocs Material site. Its maintainable sources are Markdown, YAML, media assets, CSS, and Python generation/validation scripts. The checked-in DOCX is a historical baseline used by a project-specific rebuild tool; it is not the live source of truth for every site concern.

## Read first

1. `README.md` for setup and common commands.
2. `CONTRIBUTING.md` for structure, page types, media rules, materials schema, importer safety, and handoff procedures.
3. The relevant source file and generator before editing generated output.

When instructions conflict, follow the more specific repository documentation and preserve explicit user direction.

## Source-of-truth rules

- Edit ordinary page content in `docs/index.md` or `docs/assembly/**/*.md`.
- Edit all material identities, quantities, variants, notes, and material-card image choices in `docs/data/materials.yml`.
- Do not hand-edit `docs/materials/index.md` or `docs/assembly/*/materials.md`; they are generated.
- Treat the block between `AUTO-GENERATED NAV` markers in `mkdocs.yml` as generated.
- Edit site configuration outside that block directly in `mkdocs.yml`.
- Store source media under `docs/media/<owning-section>/`.
- Never edit or commit `site/`; it is ignored, disposable build output.

## Normal workflow

Before editing:

- Inspect `git status` and preserve unrelated work already present.
- Identify whether the target is hand-maintained or generated.
- Search for all references before renaming or deleting pages, IDs, or media.

For ordinary instruction or homepage edits:

1. Edit the Markdown source.
2. Keep heading hierarchy and step numbering coherent.
3. Keep each image next to the operation it illustrates.
4. Run `python scripts/dev.py check`.

For material changes:

1. Edit `docs/data/materials.yml`.
2. Ensure every component has an accurate existing image.
3. Run `python scripts/dev.py generate`.
4. Inspect both the section material page and master catalog.
5. Run `python scripts/dev.py check`.

For new, removed, or renamed assembly pages:

1. Follow the page recipes in `CONTRIBUTING.md`.
2. Update navigation title/order mappings when required.
3. Run `python scripts/dev.py generate`.
4. Review the generated navigation diff.
5. Run `python scripts/dev.py check`.

## Images and media

- Use the component's actual baseline render when one exists.
- A focused contextual image is acceptable when no isolated render exists.
- Do not assign a general assembly image to several unrelated components merely to populate cards.
- Visually inspect ambiguous assets; filenames and extraction order alone are not reliable semantic labels.
- Preserve imported filenames unless a deliberate migration updates every reference.
- Use descriptive alt text for new Markdown images.
- Search `docs` and `scripts` before deleting an asset.
- Treat tiny or empty DOCX image artifacts as source noise, but verify references before removal.

## DOCX importer boundary

`scripts/rebuild_assembly_pages_from_docx.py` is **not a general DOCX-to-site converter**. It is coupled to `refs/BABP Assembly Instructions V0.1.docx` and compatible revisions that retain the same BABP headings, ordering, paragraph conventions, and image anchoring.

The importer contains exact section names, variant boundaries, BOM/procedure image cutoffs, skipped paragraphs, merged steps, and asset-number mappings. It does not create `materials.yml`, infer a new information architecture, or reliably support arbitrary tables, text boxes, captions, lists, or unrelated documents.

Therefore:

- Do not run the importer for routine edits.
- Do not run it against an unrelated or structurally changed DOCX.
- Do not assume importer output is authoritative without reviewing the full diff.
- When a baseline rebuild is explicitly required, follow the safe rebuild procedure in `CONTRIBUTING.md` and inspect step/image association, material-image leakage, encoding, duplicate media, and overwritten curation.
- If a manual correction must survive future rebuilds, encode the durable rule in the importer or clearly document the intentional divergence.

## Generation and validation

Use the project wrapper rather than assembling ad hoc command sequences:

```text
python scripts/dev.py generate  # materials and navigation
python scripts/dev.py check     # data, generated files, links, nav, strict build
python scripts/dev.py build     # regenerate and build site/
python scripts/dev.py serve     # regenerate and serve locally
```

`check` is the required completion gate. It validates the material model, required component images, generated file currency, local links, navigation, and a strict MkDocs build.

The Material for MkDocs toolchain may print its known MkDocs 2.0 informational notice while completing successfully. Do not use that known notice to dismiss other warnings or failures.

## Change discipline

- Make the smallest coherent change that fully addresses the task.
- Do not overwrite or revert unrelated user changes in a dirty worktree.
- Do not invent missing mechanical instructions, quantities, or safety claims.
- Preserve explicit baseline-coverage notices.
- Keep catalog IDs stable; change reader-facing labels with `label`.
- Keep hardware quantities as positive integer one-key mappings.
- Investigate surprising generated diffs rather than accepting them blindly.
- Do not add dependencies when the existing standard library or installed project tooling is sufficient.
- Update `README.md`, `CONTRIBUTING.md`, and this file when a workflow or ownership rule changes.

## Definition of done

A change is complete when:

- the correct source-of-truth file was edited;
- generated materials/navigation are current when applicable;
- media references resolve and depict the intended subject;
- `python scripts/dev.py check` passes;
- no intended work exists only under `site/`;
- no accidental or orphaned media was introduced; and
- the final handoff identifies any remaining unverified source limitation.

## Current source gaps

The baseline does not provide substantive procedures for the bolt-action variant, straight-pull variant, troubleshooting page, or tuning/maintenance page. The final firing-sequence animation is also absent. Preserve these gaps honestly until verified source material is supplied.
