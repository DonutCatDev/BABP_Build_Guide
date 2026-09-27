# Contributing and Maintainer Guide

This is the operational guide for maintaining and extending the BABP assembly site. Read the ownership rules and DOCX importer warning before changing generated content or running bulk tools.

## Quick start

Requirements: Python 3.12 or 3.13 and Git.

PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/dev.py check
python scripts/dev.py serve
```

macOS/Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/dev.py check
python scripts/dev.py serve
```

The development server normally runs at <http://127.0.0.1:8000/>.

## Edit the source, not its output

| Content | Source of truth | Generated output |
| --- | --- | --- |
| Homepage | `docs/index.md` | `site/index.html` |
| Instructions and overviews | Markdown under `docs/assembly/` | HTML under `site/` |
| Materials, quantities, variants, component images | `docs/data/materials.yml` | `docs/materials/index.md` and `docs/assembly/*/materials.md` |
| Navigation | Page layout plus `scripts/generate_nav.py` | Generated block in `mkdocs.yml` |
| Presentation | `mkdocs.yml` and `docs/stylesheets/extra.css` | Files under `site/` |
| Baseline import behavior | The baseline DOCX and `scripts/rebuild_assembly_pages_from_docx.py` | Many instruction and media files |

Never edit or commit `site/`. It is disposable build output.

Do not hand-edit generated material pages. Change `docs/data/materials.yml` and regenerate. Do not manually edit between the generated navigation markers in `mkdocs.yml`.

## Repository structure

```text
docs/
  index.md                         Hand-maintained homepage
  data/materials.yml              Material catalogs and section BOMs
  materials/index.md              Generated master catalog
  assembly/<section>/
    index.md                       Overview or primary instructions
    materials.md                   Generated section materials
    <variant>.md                   Variant/subassembly instructions
  media/<section>/                 Source images and animations
  stylesheets/extra.css            Project styles
refs/
  BABP Assembly Instructions V0.1.docx
  extracted-media/                 Import trace data
scripts/
  dev.py                           Normal development entrypoint
  generate_materials.py            Material-page generator
  validate_materials.py            Material validation
  generate_nav.py                  Navigation generator
  rebuild_assembly_pages_from_docx.py
                                     BABP-specific bulk importer
mkdocs.yml                         Site configuration
requirements.txt                   Python dependencies
site/                              Ignored build output
.github/workflows/
  ci.yml                           Pull-request validation
  pages.yml                        Main-branch validation and Pages deployment
```

Media belongs to the assembly section that primarily owns it, even when another page references it as a component image.

## Current page types

### Homepage

`docs/index.md` is hand-maintained Markdown. Use it for orientation, assembly order, prominent notices, and links into the guide. It is not generated from the DOCX or material catalog.

### Overview or primary instruction page

Every assembly directory normally has an `index.md`. It may introduce subassemblies or contain the section's primary procedure.

Use this structure for procedures:

```markdown
# Example Assembly

[View Materials List](materials.md)

## Overview

Optional prerequisites or orientation.

## Steps

### Step 1

Describe one coherent operation, including orientation and quantities.

![Parts aligned before insertion](../../media/example/example-step-01_picture1.png)
```

Use one `### Step N` heading per coherent operation. Keep images immediately after the text they illustrate. Alt text should identify what the reader should notice.

### Variant or subassembly page

Variant pages sit beside the section `index.md`, such as `assembly/shroud/railgun.md`, and use the same step structure.

The navigation generator treats Markdown other than `index.md`, `materials.md`, and `instructions.md` as a variant. Add a friendly label to `SPECIAL_PAGE_LABELS` in `scripts/generate_nav.py` if the filename does not title-case correctly.

### Materials page

Section material pages and the master catalog are generated from `docs/data/materials.yml`. Never edit their card markup directly.

### Informational or coverage-gap page

Troubleshooting, maintenance, and customization pages may use normal Markdown headings, lists, tables, and admonitions. If no verified procedure exists, state the gap instead of inventing instructions.

## Editing an existing page

For an ordinary correction:

1. Edit the owning Markdown file under `docs/assembly/<section>/`.
2. Keep step numbering sequential.
3. Place images with the steps they support.
4. Use links relative to the Markdown source.
5. Preview with `python scripts/dev.py serve`.
6. Run `python scripts/dev.py check`.

Use warnings next to risky operations:

```markdown
!!! warning
    Read the complete operation before applying adhesive.
```

A future DOCX rebuild may overwrite manual instruction edits. If a correction represents a durable import rule, update the importer too, or document why the Markdown intentionally differs from the baseline.

## Adding a variant or subassembly

1. Create `docs/assembly/<section>/<variant-slug>.md`.
2. Add its title, overview if useful, and sequential steps.
3. Put media under `docs/media/<section>/`.
4. Add variant-only materials under `sections.<section>.variants` in `materials.yml`.
5. Add a label to `VARIANT_TITLES` in `generate_materials.py` if needed.
6. Add a label to `SPECIAL_PAGE_LABELS` in `generate_nav.py` if needed.
7. Run `python scripts/dev.py generate` and `python scripts/dev.py check`.

Variant material entries contain additions specific to that choice. Do not repeat all base items in every variant.

## Adding an assembly section

1. Create `docs/assembly/<section-slug>/index.md`.
2. Create `docs/media/<section-slug>/` when the section has media.
3. Add `sections.<section-slug>` to `materials.yml` when it needs a material page.
4. Add the display name to `SECTION_TITLES` in `generate_nav.py` and `generate_materials.py`.
5. Add the slug to `SECTION_ORDER` in `generate_nav.py`.
6. Add any variant pages and variant material groups.
7. Run `python scripts/dev.py generate`.
8. Review the generated pages and navigation diff.
9. Run `python scripts/dev.py check`.

A section without materials can be omitted from `materials.yml`. Adding a website section does not add DOCX import support; that requires deliberate importer changes.

## Materials data model

`docs/data/materials.yml` contains `components`, `hardware`, `consumables`, and `sections`. Catalog IDs are stable identifiers without spaces. Use `label` for reader-facing wording.

Every component requires an image:

```yaml
components:
  ExamplePart:
    label: Example Part
    image: example/example-part.png
    note: Optional clarification shown on its card.
```

Image paths are relative to `docs/media/`. Prefer an isolated baseline render. A focused contextual image is acceptable when no isolated render exists. Do not reuse an overall assembly image for unrelated cards merely to satisfy validation.

Hardware quantities are positive integers; components and consumables are ID lists:

```yaml
hardware:
  screw_example:
    label: Example Screw

consumables:
  threadlocker:
    label: Threadlocker

sections:
  example:
    base:
      components:
        - ExamplePart
      hardware:
        - screw_example: 4
      consumables:
        - threadlocker
    variants:
      alternate:
        components:
          - AlternatePart
        hardware:
          - screw_example: 2
```

`base` applies to every build. `variants` adds choice-specific requirements. The master catalog does not calculate one universal total because totals depend on selected variants.

After any material change:

```text
python scripts/dev.py generate
python scripts/dev.py check
```

## Adding and replacing media

Store media in `docs/media/<owning-section>/`. For new hand-maintained assets, use lowercase descriptive names with hyphens, for example `install-trigger-pivot_picture1.png`.

Imported assets retain names such as `section-step-03_picture2.png`. Do not rename them casually: instructions, material entries, and import trace data may reference them.

Use PNG or WebP for static instructional images and GIF only when motion adds necessary information. SVG is acceptable for trusted project-authored diagrams.

To add an instruction image:

1. Add it to the owning media directory.
2. Add meaningful alt text and a relative Markdown link.
3. Confirm it renders under the intended step.
4. Run `python scripts/dev.py check`.

To add a material image:

1. Add it under `docs/media/`.
2. Set the component's `image` in `materials.yml`.
3. Regenerate.
4. Inspect the section page and master catalog.
5. Run the checks.

Replace a file in place only when it still depicts the same subject. Otherwise add a new filename and update references explicitly. Before deleting media, search for references:

```text
rg "filename.png" docs scripts
```

## Navigation behavior

`generate_nav.py` scans immediate Markdown children of `docs/assembly/<section>/`:

- `index.md`, `materials.md`, and `instructions.md` are primary pages.
- Other Markdown files are grouped as variants.
- Section order comes from `SECTION_ORDER`.
- Labels come from explicit mappings or file slugs.
- Files outside this structure are not automatically published in navigation.

Regenerate after adding, removing, or renaming pages.

## DOCX importer: important scope limitation

> **The importer is not a general DOCX-to-site converter.** It is a BABP baseline-specific rebuild tool for `refs/BABP Assembly Instructions V0.1.docx` and revisions that preserve the same structure.

It assumes:

- the fixed source filename and path;
- exact BABP Heading 1, Heading 2, and Heading 3 names;
- the existing section and variant hierarchy;
- known paragraph positions for overview and material text;
- hard-coded BOM/procedure image boundaries;
- BABP-specific skipped paragraphs, merged steps, and media numbering;
- inline paragraph images readable through `python-docx`.

It does not generally interpret arbitrary tables, text boxes, captions, nested lists, renamed sections, or a different information architecture. It does not generate `materials.yml`, infer components or quantities, design a homepage, or configure a new site. An unrelated DOCX will normally fail, omit content, or associate text and images incorrectly.

Compatibility expectations:

| Input | Expected result |
| --- | --- |
| Current baseline | Supported |
| Revised baseline with identical structure | Usually supported; review required |
| Renamed or reordered BABP sections | Importer changes required |
| Entirely different document | Unsupported |

### Safe rebuild procedure

The importer directly overwrites many pages and media files:

1. Understand the working tree and preserve unrelated changes.
2. Confirm the input follows the compatible BABP structure.
3. Run `python scripts/rebuild_assembly_pages_from_docx.py`.
4. Run `python scripts/dev.py generate`.
5. Review the full diff for step boundaries, image placement, BOM images in procedures, orphaned media, encoding, and curated wording.
6. Run `python scripts/dev.py check`.

Do not run the importer as a prerequisite for ordinary editing. Direct Markdown, YAML, and media edits are the normal maintenance path. `refs/extracted-media/placeholder-mapping.json` is import trace data, not a general authoring manifest.

## Development commands

```text
python scripts/dev.py generate  Regenerate materials and navigation
python scripts/dev.py check     Validate data, generated files, links, nav, and strict build
python scripts/dev.py build     Regenerate and build site/
python scripts/dev.py serve     Regenerate and start live reload
```

`check` verifies the supported Python version, dependency-file synchronization, material schema and references, component images, generated-file currency, local Markdown/HTML links, navigation, and a strict MkDocs build. Run it before committing. Pull requests run the same checks through `ci.yml`; pushes to `main` repeat them before deployment through `pages.yml`.

Commit generated material Markdown and the generated navigation block because their diffs are reviewable. Do not commit `site/`, `.venv/`, caches, or editor-local state. Investigate surprising generated diffs rather than accepting them blindly.

## Writing conventions

- Use direct, imperative instructions.
- State orientation before an irreversible action.
- Include quantities where they are needed.
- Keep warnings next to the relevant operation.
- Do not infer missing mechanical procedures from appearance alone.
- Use established component labels from `materials.yml`.
- Keep one page title, then `##` sections and `###` steps.
- Use descriptive alt text and relative internal links.
- Preview unusually large images and tables at narrow and wide widths.

## Troubleshooting

### Material pages are stale

Run `python scripts/dev.py generate` and commit the YAML source plus generated Markdown.

### A card repeats the wrong image

Find the component in `materials.yml`, inspect candidate assets under the owning media directory, select the image that actually identifies it, then inspect both generated material pages.

### A page is missing from navigation

Place it directly under `docs/assembly/<section>/`, regenerate, and add new section mappings/order when applicable.

### A local image link fails

Resolve it relative to its Markdown file. Generated material pages are special because their raw HTML renders one URL level deeper; let the generator create those paths.

### A DOCX rebuild moves images or creates duplicates

Stop and inspect the import rule before accepting or deleting results. Check the BOM/procedure boundary, overview slicing, merged-step behavior, and asset-step mapping in the importer.

### MkDocs prints the Material/MkDocs 2.0 notice

The pinned toolchain may emit this upstream informational notice while the strict build succeeds. Treat any additional warning or build error separately.

## Known baseline gaps

The baseline has no substantive procedure for the bolt-action variant, straight-pull variant, troubleshooting page, or tuning/maintenance page. Those pages disclose the gap instead of presenting guessed instructions. The final firing-sequence animation is also absent.

## Handoff checklist

1. Ensure `python scripts/dev.py check` passes.
2. Confirm no intended source change exists only in `site/`.
3. Include regenerated material and navigation files.
4. Check that new components have accurate, distinct images.
5. Document deliberate divergence from the baseline.
6. Call out unverified quantities or procedures.
7. Review `git status` for accidental or orphaned media.
