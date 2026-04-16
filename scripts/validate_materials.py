from __future__ import annotations

from pathlib import Path
import sys
from collections import defaultdict

try:
    import yaml
except ImportError as exc:
    raise SystemExit(
        "PyYAML is required. Install it with: pip install pyyaml"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MATERIALS_FILE = DOCS / "data" / "materials.yml"
ASSEMBLY_DIR = DOCS / "assembly"


def load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing materials file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("materials.yml must contain a top-level mapping/object")
    return data


def expect_mapping(obj, label: str, errors: list[str]) -> dict:
    if obj is None:
        return {}
    if not isinstance(obj, dict):
        errors.append(f"{label} must be a mapping/object")
        return {}
    return obj


def expect_list(obj, label: str, errors: list[str]) -> list:
    if obj is None:
        return []
    if not isinstance(obj, list):
        errors.append(f"{label} must be a list")
        return []
    return obj


def validate_catalog_entry_shapes(catalog_name: str, catalog: dict, errors: list[str]) -> dict[str, str]:
    """
    Returns a mapping of id -> display label.
    components may be bare keys with null/empty values, or objects with label.
    hardware/consumables should usually be objects with label, but bare values are tolerated.
    """
    labels: dict[str, str] = {}
    for item_id, value in catalog.items():
        if not isinstance(item_id, str):
            errors.append(f"{catalog_name} contains a non-string ID: {item_id!r}")
            continue

        if " " in item_id:
            errors.append(f"{catalog_name}.{item_id}: IDs must not contain spaces")

        label = item_id
        if value is None:
            label = item_id
        elif isinstance(value, str):
            label = value
        elif isinstance(value, dict):
            if "label" in value:
                if not isinstance(value["label"], str) or not value["label"].strip():
                    errors.append(f"{catalog_name}.{item_id}.label must be a non-empty string")
                else:
                    label = value["label"]
            else:
                # Allow bare object for future extensibility, but warn via fallback label
                label = item_id
        else:
            errors.append(
                f"{catalog_name}.{item_id} must be null, string, or mapping/object"
            )
            continue

        labels[item_id] = label
    return labels


def parse_quantity_mapping(item, label: str, errors: list[str]) -> tuple[str | None, int | None]:
    if not isinstance(item, dict) or len(item) != 1:
        errors.append(f"{label} entries must be one-key mappings like {{item_id: quantity}}")
        return None, None

    item_id, qty = next(iter(item.items()))
    if not isinstance(item_id, str):
        errors.append(f"{label} item ID must be a string")
        return None, None
    if not isinstance(qty, int) or qty <= 0:
        errors.append(f"{label}.{item_id} quantity must be a positive integer")
        return None, None
    return item_id, qty


def collect_duplicate_labels(label_maps: dict[str, dict[str, str]], warnings: list[str]) -> None:
    reverse: dict[str, list[str]] = defaultdict(list)
    for catalog_name, items in label_maps.items():
        for item_id, label in items.items():
            reverse[label].append(f"{catalog_name}.{item_id}")

    for label, refs in sorted(reverse.items()):
        if len(refs) > 1:
            warnings.append(
                f'Duplicate display label "{label}" used by multiple IDs: {", ".join(refs)}'
            )


def validate_material_group(
    group_name: str,
    group_data: dict,
    catalogs: dict[str, dict[str, str]],
    errors: list[str],
    warnings: list[str],
    seen_refs: dict[str, list[str]],
    *,
    check_duplicates_against: dict[str, set[str]] | None = None,
) -> None:
    components = expect_list(group_data.get("components"), f"{group_name}.components", errors)
    hardware = expect_list(group_data.get("hardware"), f"{group_name}.hardware", errors)
    consumables = expect_list(group_data.get("consumables"), f"{group_name}.consumables", errors)

    local_sets = {
        "components": set(),
        "hardware": set(),
        "consumables": set(),
    }

    for item_id in components:
        if not isinstance(item_id, str):
            errors.append(f"{group_name}.components entries must be strings")
            continue
        if item_id not in catalogs["components"]:
            errors.append(f"{group_name}.components references undefined component ID: {item_id}")
        else:
            seen_refs["components"].append(item_id)
            if item_id in local_sets["components"]:
                warnings.append(f"{group_name}.components contains duplicate reference: {item_id}")
            local_sets["components"].add(item_id)

    for item in hardware:
        item_id, _qty = parse_quantity_mapping(item, f"{group_name}.hardware", errors)
        if item_id is None:
            continue
        if item_id not in catalogs["hardware"]:
            errors.append(f"{group_name}.hardware references undefined hardware ID: {item_id}")
        else:
            seen_refs["hardware"].append(item_id)
            if item_id in local_sets["hardware"]:
                warnings.append(f"{group_name}.hardware contains duplicate reference: {item_id}")
            local_sets["hardware"].add(item_id)

    for item_id in consumables:
        if not isinstance(item_id, str):
            errors.append(f"{group_name}.consumables entries must be strings")
            continue
        if item_id not in catalogs["consumables"]:
            errors.append(f"{group_name}.consumables references undefined consumable ID: {item_id}")
        else:
            seen_refs["consumables"].append(item_id)
            if item_id in local_sets["consumables"]:
                warnings.append(f"{group_name}.consumables contains duplicate reference: {item_id}")
            local_sets["consumables"].add(item_id)

    if check_duplicates_against:
        for kind in ("components", "hardware", "consumables"):
            overlap = local_sets[kind] & check_duplicates_against[kind]
            for item_id in sorted(overlap):
                warnings.append(
                    f"{group_name}.{kind} duplicates base item {item_id}; keep shared items in base where possible"
                )


def validate_sections(
    sections: dict,
    catalogs: dict[str, dict[str, str]],
    errors: list[str],
    warnings: list[str],
    seen_refs: dict[str, list[str]],
) -> None:
    for section_id, section_data in sections.items():
        if not isinstance(section_id, str):
            errors.append(f"sections contains a non-string section ID: {section_id!r}")
            continue
        if " " in section_id:
            errors.append(f"sections.{section_id}: section IDs must not contain spaces")

        section_data = expect_mapping(section_data, f"sections.{section_id}", errors)

        base = expect_mapping(section_data.get("base"), f"sections.{section_id}.base", errors)
        validate_material_group(
            f"sections.{section_id}.base",
            base,
            catalogs,
            errors,
            warnings,
            seen_refs,
        )

        base_sets = {
            "components": set(expect_list(base.get("components"), "", [])),
            "hardware": {
                next(iter(item.keys()))
                for item in expect_list(base.get("hardware"), "", [])
                if isinstance(item, dict) and len(item) == 1
            },
            "consumables": set(expect_list(base.get("consumables"), "", [])),
        }

        variants = expect_mapping(section_data.get("variants"), f"sections.{section_id}.variants", errors)
        for variant_id, variant_data in variants.items():
            if not isinstance(variant_id, str):
                errors.append(f"sections.{section_id}.variants contains a non-string variant ID: {variant_id!r}")
                continue
            if " " in variant_id:
                errors.append(f"sections.{section_id}.variants.{variant_id}: variant IDs must not contain spaces")

            variant_data = expect_mapping(
                variant_data,
                f"sections.{section_id}.variants.{variant_id}",
                errors,
            )
            validate_material_group(
                f"sections.{section_id}.variants.{variant_id}",
                variant_data,
                catalogs,
                errors,
                warnings,
                seen_refs,
                check_duplicates_against=base_sets,
            )


def validate_section_folders(sections: dict, errors: list[str], warnings: list[str]) -> None:
    yaml_section_ids = {section_id for section_id in sections.keys() if isinstance(section_id, str)}

    if not ASSEMBLY_DIR.exists():
        warnings.append(f"Assembly directory not found: {ASSEMBLY_DIR}")
        return

    folder_ids = {p.name for p in ASSEMBLY_DIR.iterdir() if p.is_dir()}

    missing_folders = sorted(yaml_section_ids - folder_ids)
    extra_folders = sorted(folder_ids - yaml_section_ids)

    for section_id in missing_folders:
        warnings.append(f"Section defined in materials.yml but missing docs folder: docs/assembly/{section_id}")
    for folder_id in extra_folders:
        warnings.append(f"Docs folder exists without YAML section entry: docs/assembly/{folder_id}")

    required_pages = ("index.md", "materials.md")
    for folder_id in sorted(folder_ids & yaml_section_ids):
        folder = ASSEMBLY_DIR / folder_id
        for page in required_pages:
            if not (folder / page).exists():
                warnings.append(f"docs/assembly/{folder_id}/{page} is missing")


def validate_orphans(
    catalogs: dict[str, dict[str, str]],
    seen_refs: dict[str, list[str]],
    warnings: list[str],
) -> None:
    for kind, catalog in catalogs.items():
        used = set(seen_refs[kind])
        all_ids = set(catalog.keys())
        unused = sorted(all_ids - used)
        for item_id in unused:
            warnings.append(f"Unused {kind[:-1] if kind.endswith('s') else kind} ID: {item_id}")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        data = load_yaml(MATERIALS_FILE)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2

    components = expect_mapping(data.get("components"), "components", errors)
    hardware = expect_mapping(data.get("hardware"), "hardware", errors)
    consumables = expect_mapping(data.get("consumables"), "consumables", errors)
    sections = expect_mapping(data.get("sections"), "sections", errors)

    catalogs = {
        "components": validate_catalog_entry_shapes("components", components, errors),
        "hardware": validate_catalog_entry_shapes("hardware", hardware, errors),
        "consumables": validate_catalog_entry_shapes("consumables", consumables, errors),
    }

    collect_duplicate_labels(catalogs, warnings)

    seen_refs = {
        "components": [],
        "hardware": [],
        "consumables": [],
    }

    validate_sections(sections, catalogs, errors, warnings, seen_refs)
    validate_section_folders(sections, errors, warnings)
    validate_orphans(catalogs, seen_refs, warnings)

    if errors:
        print("Materials validation failed.\n")
        print("Errors:")
        for msg in errors:
            print(f"  - {msg}")
        if warnings:
            print("\nWarnings:")
            for msg in warnings:
                print(f"  - {msg}")
        return 1

    print("Materials validation passed.")
    if warnings:
        print("\nWarnings:")
        for msg in warnings:
            print(f"  - {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
