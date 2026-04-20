from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MKDOCS_YML = ROOT / "mkdocs.yml"

NAV_START = "# AUTO-GENERATED NAV START"
NAV_END = "# AUTO-GENERATED NAV END"

PRIMARY_PAGE_ORDER = {
    "index.md": 0,
    "materials.md": 1,
    "instructions.md": 2,
}

PAGE_LABELS = {
    "index.md": "Overview",
    "materials.md": "Materials",
    "instructions.md": "Instructions",
}

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
    "troubleshooting": "Troubleshooting",
    "tuning-maintenance": "Tuning/Maintenance",
    "customization-options": "Customization Options",
}

SPECIAL_PAGE_LABELS = {
    "railgun": "Railgun Variant",
    "bipod": "Bipod Variant",
    "bipod-sub-assembly": "Bipod Sub-Assembly",
    "common-assembly": "Common Assembly",
    "bolt-action": "Bolt Action Assembly",
    "straight-pull": "Straight Pull Assembly",
    "dual-straight-pull": "Dual Straight Pull Assembly",
    "plunger-sub-assembly": "Plunger Sub-Assembly",
    "final-assembly": "Final Assembly",
}

SECTION_ORDER = [
    "customization-options",
    "stock-magwell",
    "shroud",
    "gear-tensioner",
    "receiver",
    "prime-block",
    "core",
    "loader",
    "turnaround",
    "final",
    "troubleshooting",
    "tuning-maintenance",
]


def title_case_from_slug(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.replace("_", "-").split("-"))


def section_title(section_slug: str) -> str:
    return SECTION_TITLES.get(section_slug, title_case_from_slug(section_slug))


def page_label(path: Path) -> str:
    if path.name in PAGE_LABELS:
        return PAGE_LABELS[path.name]
    stem = path.stem
    if stem in SPECIAL_PAGE_LABELS:
        return SPECIAL_PAGE_LABELS[stem]
    return title_case_from_slug(stem)


def is_slide_page(path: Path) -> bool:
    return path.name == "slides.md" or path.stem.startswith("slides-")


def is_variant_page(path: Path) -> bool:
    return path.name not in PAGE_LABELS and not is_slide_page(path)


def section_sort_key(path: Path) -> tuple[int, str]:
    try:
        idx = SECTION_ORDER.index(path.name)
    except ValueError:
        idx = 999
    return (idx, path.name)


def page_sort_key(path: Path) -> tuple[int, str]:
    if path.name in PRIMARY_PAGE_ORDER:
        return (PRIMARY_PAGE_ORDER[path.name], path.name)
    if is_variant_page(path):
        return (20, path.name)
    return (50, path.name)


def build_nav_lines() -> list[str]:
    lines: list[str] = []
    lines.append("nav:")
    lines.append("  - Home: index.md")

    master_materials = DOCS / "materials" / "index.md"
    if master_materials.exists():
        lines.append("  - Master Materials: materials/index.md")

    assembly_dir = DOCS / "assembly"
    if assembly_dir.exists():
        lines.append("  - Assembly:")
        for section in sorted((p for p in assembly_dir.iterdir() if p.is_dir()), key=section_sort_key):
            md_files = sorted(section.glob("*.md"), key=page_sort_key)
            if not md_files:
                continue

            lines.append(f"      - {section_title(section.name)}:")

            primary_pages = [p for p in md_files if p.name in PRIMARY_PAGE_ORDER]
            variant_pages = [p for p in md_files if is_variant_page(p)]

            for page in primary_pages:
                rel = page.relative_to(DOCS).as_posix()
                lines.append(f"          - {page_label(page)}: {rel}")

            if variant_pages:
                lines.append("          - Variants:")
                for page in variant_pages:
                    rel = page.relative_to(DOCS).as_posix()
                    lines.append(f"              - {page_label(page)}: {rel}")

    return lines


def replace_nav_block(original: str, nav_block: str) -> str:
    pattern = re.compile(
        rf"{re.escape(NAV_START)}.*?{re.escape(NAV_END)}",
        re.DOTALL,
    )
    replacement = f"{NAV_START}\n{nav_block}\n{NAV_END}"

    if pattern.search(original):
        return pattern.sub(replacement, original)

    if not original.endswith("\n"):
        original += "\n"
    return original + "\n" + replacement + "\n"


def main() -> None:
    nav_block = "\n".join(build_nav_lines())
    current = MKDOCS_YML.read_text(encoding="utf-8") if MKDOCS_YML.exists() else ""
    updated = replace_nav_block(current, nav_block)
    MKDOCS_YML.write_text(updated, encoding="utf-8")
    print("Updated mkdocs.yml navigation.")


if __name__ == "__main__":
    main()
