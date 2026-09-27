# BABP Assembly Guide

Source and build tooling for the MkDocs-based BABP assembly guide.

## Quick start

Requirements:

- Python 3.12 or 3.13
- Git

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

The local site is normally available at <http://127.0.0.1:8000/>. See [CONTRIBUTING.md](CONTRIBUTING.md) for the complete authoring model, page and media workflows, generation rules, importer constraints, and maintainer handoff guide.

> **DOCX importer scope:** `scripts/rebuild_assembly_pages_from_docx.py` is specific to the current BABP baseline document and its exact structure. It is not a general DOCX-to-site converter and should not be run against an unrelated document. Read the importer safety section in `CONTRIBUTING.md` before using it.

AI-assisted contributors should also read [AGENTS.md](AGENTS.md), which summarizes repository-wide source ownership, safe automation boundaries, and the required completion checks for any agent tool.

## Common commands

```text
python scripts/dev.py generate  Regenerate navigation and material pages
python scripts/dev.py check     Validate data, generated files, links, and MkDocs
python scripts/dev.py build     Generate and build the production site
python scripts/dev.py serve     Generate and run the live-reload server
```

`site/` is generated locally and by GitHub Actions. It is intentionally not version-controlled.
