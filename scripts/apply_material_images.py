from __future__ import annotations

from pathlib import Path
import os
import re
import sys

try:
    import yaml
except ImportError as exc:
    raise SystemExit(
        "PyYAML is required. Install it with: pip install pyyaml"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MATERIALS_FILE = DOCS / "data" / "materials.yml"
MEDIA_DIR = DOCS / "media"
MASTER_MATERIALS_FILE = DOCS / "materials" / "index.md"
ASSEMBLY_DIR = DOCS / "assembly"

ITEM_RE = re.compile(r"^(\s*)-\s+(.+?)\s*$")
INJECTED_IMAGE_RE = re.compile(
    r"^\s+!\[.*\]\([^)]*\)\{\s*\.material-inline-image\s*\}\s*$"
)
INLINE_IMAGE_RE = re.compile(
    r"\s+!\[[^\]]*\]\([^)]*\)\{\s*\.material-inline-image\s*\}\s*$"
)


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("materials.yml must contain a top-level mapping/object")
    return data


def normalize_image_path(path_value: str) -> str:
    value = path_value.strip().replace("\\", "/")
    if value.startswith("media/"):
        value = value[len("media/") :]
    return value


def iter_entry_names(item_id: str, value) -> list[str]:
    names = [item_id]
    if isinstance(value, str):
        if value.strip():
            names.append(value.strip())
    elif isinstance(value, dict):
        label = value.get("label")
        if isinstance(label, str) and label.strip():
            names.append(label.strip())
        aliases = value.get("aliases") or []
        if isinstance(aliases, list):
            names.extend(
                alias.strip()
                for alias in aliases
                if isinstance(alias, str) and alias.strip()
            )
    return names


def normalize_name(text: str) -> str:
    normalized = text.strip().lower()
    normalized = normalized.replace('"', " inch ")
    normalized = normalized.replace("-", " ")
    normalized = normalized.replace("_", " ")
    normalized = re.sub(r"\s+x\d+$", "", normalized)
    normalized = re.sub(r"\s+\([^)]*\)$", "", normalized)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def build_image_lookup(data: dict) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for catalog_name in ("components", "hardware", "consumables"):
        catalog = data.get(catalog_name) or {}
        if not isinstance(catalog, dict):
            continue
        for item_id, value in catalog.items():
            if not isinstance(value, dict):
                continue
            image = value.get("image")
            if not isinstance(image, str) or not image.strip():
                continue
            image_path = normalize_image_path(image)
            for name in iter_entry_names(item_id, value):
                key = normalize_name(name)
                if key:
                    lookup[key] = image_path
    return lookup


def possible_match_keys(text: str) -> list[str]:
    raw = text.strip()
    variants = [raw]

    without_note = re.sub(r"\s+\([^)]*\)$", "", raw).strip()
    if without_note != raw:
        variants.append(without_note)

    without_qty = re.sub(r"\s+x\d+$", "", without_note, flags=re.IGNORECASE).strip()
    if without_qty and without_qty not in variants:
        variants.append(without_qty)

    keys: list[str] = []
    for variant in variants:
        key = normalize_name(variant)
        if key and key not in keys:
            keys.append(key)
    return keys


def materials_files() -> list[Path]:
    files = [MASTER_MATERIALS_FILE]
    files.extend(sorted(ASSEMBLY_DIR.glob("*/materials.md")))
    return files


def render_image_line(markdown_path: Path, item_text: str, image_path: str, indent: str) -> str:
    absolute_image = MEDIA_DIR / image_path
    relative_image = os.path.relpath(absolute_image, start=markdown_path.parent).replace("\\", "/")
    return (
        f"{indent}- {item_text} ![{item_text}]({relative_image})"
        "{ .material-inline-image }\n"
    )


def inject_images(path: Path, lookup: dict[str, str]) -> bool:
    original_lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    new_lines: list[str] = []
    index = 0

    while index < len(original_lines):
        line = original_lines[index]
        match = ITEM_RE.match(line)
        if not match:
            new_lines.append(line)
            index += 1
            continue

        indent, item_text = match.groups()
        clean_item_text = INLINE_IMAGE_RE.sub("", item_text).strip()
        index += 1

        while index < len(original_lines) and INJECTED_IMAGE_RE.match(original_lines[index]):
            index += 1

        image_path = None
        for candidate in possible_match_keys(clean_item_text):
            image_path = lookup.get(candidate)
            if image_path:
                break

        if image_path:
            new_lines.append(render_image_line(path, clean_item_text, image_path, indent))
        else:
            new_lines.append(f"{indent}- {clean_item_text}\n")

    original_text = "".join(original_lines)
    new_text = "".join(new_lines)
    if new_text != original_text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def main() -> int:
    data = load_yaml(MATERIALS_FILE)
    lookup = build_image_lookup(data)
    files = materials_files()
    updated = 0

    for path in files:
        if inject_images(path, lookup):
            updated += 1

    print(f"Processed {len(files)} materials page(s); updated {updated} file(s)")
    print(f"Found {len(lookup)} material image mapping(s) in {MATERIALS_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
