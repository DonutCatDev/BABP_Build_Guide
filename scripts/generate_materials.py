from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DATA_FILE = DOCS / "data" / "materials.yml"
MASTER_FILE = DOCS / "materials" / "index.md"

SECTION_TITLES = {
    "stock-magwell": "Stock/Magwell Assembly",
    "shroud": "Shroud Assembly",
    "gear-tensioner": "Gear Tensioner Assembly",
    "receiver": "Receiver Assembly",
    "prime-block": "Prime Block Assembly",
    "core": "Core Assembly",
    "loader": "Loader Assembly",
    "turnaround": "Turnaround Assembly",
    "final": "Final Assembly",
}

VARIANT_TITLES = {
    "railgun": "Railgun Variant",
    "bipod-sub-assembly": "Bipod Sub-Assembly",
    "bipod": "Bipod Variant",
    "dual-window": "Dual-Window Receiver",
    "shroud-selection": "Shroud Selection",
    "bolt-action": "Bolt Action",
    "straight-pull": "Straight Pull",
    "dual-straight-pull": "Dual Straight Pull",
    "scar": "SCAR",
}


def load_data() -> dict:
    data = yaml.safe_load(DATA_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{DATA_FILE} must contain a top-level mapping")
    return data


def entry(data: dict, kind: str, item_id: str) -> dict:
    value = data[kind][item_id]
    if value is None:
        return {"label": item_id}
    if isinstance(value, str):
        return {"label": value}
    return {"label": item_id, **value}


def image_markup(image: str | None, label: str, output: Path) -> str:
    if not image:
        return ""
    image_path = DOCS / "media" / image
    relative = image_path.relative_to(output.parent, walk_up=True).as_posix()
    # A page named materials.md renders at .../materials/index.html, one URL
    # level deeper than its source directory. Raw HTML URLs are not rewritten
    # by MkDocs, so account for that extra level explicitly.
    if output.name == "materials.md":
        relative = f"../{relative}"
    return f'\n  <a href="{relative}" class="glightbox" data-type="image">\n    <img src="{relative}" alt="Reference image for {label}" loading="lazy">\n  </a>'


def render_items(data: dict, kind: str, items: list, output: Path) -> list[str]:
    lines = ['<div class="material-grid" markdown>']
    for raw in items:
        if isinstance(raw, str):
            item_id, quantity = raw, None
        else:
            item_id, quantity = next(iter(raw.items()))
        item = entry(data, kind, item_id)
        label = item["label"]
        quantity_text = f" × {quantity}" if quantity is not None else ""
        note = item.get("note")
        lines.extend([
            '<div class="material-card" markdown>',
            f"**{label}**{quantity_text}",
        ])
        image = image_markup(item.get("image"), label, output)
        if image:
            lines.append(image)
        if note:
            lines.append(f"\n{note}")
        lines.extend(["</div>", ""])
    lines.append("</div>")
    return lines


def render_group(data: dict, group: dict, output: Path, heading_level: int) -> list[str]:
    lines: list[str] = []
    for kind, title in (("components", "Components"), ("hardware", "Hardware"), ("consumables", "Consumables")):
        items = group.get(kind) or []
        if not items:
            continue
        lines.extend([f"{'#' * heading_level} {title}", ""])
        lines.extend(render_items(data, kind, items, output))
        lines.append("")
    return lines


def render_section(data: dict, section_id: str, section: dict, output: Path) -> str:
    title = SECTION_TITLES.get(section_id, section_id.replace("-", " ").title())
    lines = [f"# {title} Materials", "", "This page is generated from `docs/data/materials.yml`.", "", "## Base Materials", ""]
    lines.extend(render_group(data, section.get("base") or {}, output, 3))

    variants = section.get("variants") or {}
    if variants:
        lines.extend(["## Variant Materials", ""])
        for variant_id, group in variants.items():
            variant_title = VARIANT_TITLES.get(variant_id, variant_id.replace("-", " ").title())
            lines.extend([f"### {variant_title}", ""])
            lines.extend(render_group(data, group or {}, output, 4))
    else:
        lines.extend(["## Variant Materials", "", "No section-specific variant materials.", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_master(data: dict, output: Path) -> str:
    lines = [
        "# Master Materials",
        "",
        "This catalog lists every material currently referenced by the assembly sections. "
        "Quantities belong to the section and variant lists; use those pages when preparing a build.",
        "",
    ]
    for kind, title in (("components", "Components"), ("hardware", "Hardware"), ("consumables", "Consumables")):
        lines.extend([f"## {title}", ""])
        lines.extend(render_items(data, kind, list(data.get(kind, {}).keys()), output))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def generated_outputs(data: dict) -> dict[Path, str]:
    outputs = {MASTER_FILE: render_master(data, MASTER_FILE)}
    for section_id, section in (data.get("sections") or {}).items():
        output = DOCS / "assembly" / section_id / "materials.md"
        outputs[output] = render_section(data, section_id, section, output)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate material pages from the YAML catalog.")
    parser.add_argument("--check", action="store_true", help="Fail if generated pages are stale.")
    args = parser.parse_args()
    outputs = generated_outputs(load_data())
    stale: list[Path] = []
    for path, content in outputs.items():
        if path.exists() and path.read_text(encoding="utf-8") == content:
            continue
        stale.append(path)
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if args.check and stale:
        print("Generated material pages are stale:")
        for path in stale:
            print(f"  - {path.relative_to(ROOT)}")
        print("Run: python scripts/generate_materials.py")
        return 1
    action = "Checked" if args.check else "Generated"
    print(f"{action} {len(outputs)} material page(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
