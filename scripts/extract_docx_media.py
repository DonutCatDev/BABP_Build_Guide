from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DOCX_PATH = ROOT / "refs" / "BABP Assembly Instructions V0.1.docx"
OUTPUT_DIR = ROOT / "refs" / "extracted-media"
DOCS_DIR = ROOT / "docs"
MAPPING_FILE = OUTPUT_DIR / "placeholder-mapping.json"


IMAGE_PATTERN = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def natural_picture_key(path: Path) -> tuple[int, str]:
    match = re.search(r"(\d+)", path.stem)
    if not match:
        return (10**9, path.name)
    return (int(match.group(1)), path.name)


def iter_markdown_image_targets() -> list[Path]:
    targets: list[Path] = []
    seen: set[Path] = set()

    for markdown_file in sorted(DOCS_DIR.glob("**/*.md")):
        text = markdown_file.read_text(encoding="utf-8")
        for raw_target in IMAGE_PATTERN.findall(text):
            target = raw_target.strip()
            if target.startswith("http://") or target.startswith("https://"):
                continue
            if "<" in target or ">" in target:
                continue
            resolved = (markdown_file.parent / target).resolve()
            if not str(resolved).startswith(str((DOCS_DIR / "media").resolve())):
                continue
            if resolved.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            targets.append(resolved)

    return sorted(targets)


def main() -> None:
    if not DOCX_PATH.exists():
        raise FileNotFoundError(f"Reference document not found: {DOCX_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Clean previously extracted files so reruns are deterministic.
    for existing in OUTPUT_DIR.iterdir():
        if existing.is_file() and existing.name != MAPPING_FILE.name:
            existing.unlink()

    extracted: list[Path] = []
    with zipfile.ZipFile(DOCX_PATH) as docx_zip:
        media_members = sorted(
            [name for name in docx_zip.namelist() if name.startswith("word/media/")]
        )
        for idx, member in enumerate(media_members, start=1):
            suffix = Path(member).suffix.lower()
            target = OUTPUT_DIR / f"reference-picture{idx}{suffix}"
            with docx_zip.open(member) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted.append(target)

    if not extracted:
        print("No images were found in the reference DOCX.")
        return

    extracted_sorted = sorted(extracted, key=natural_picture_key)
    placeholder_targets = iter_markdown_image_targets()

    mapping: list[dict[str, str]] = []
    source_index = 0

    for target in placeholder_targets:
        if target.exists():
            continue
        source = extracted_sorted[source_index % len(extracted_sorted)]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        mapping.append(
            {
                "source": str(source.relative_to(ROOT)).replace("\\", "/"),
                "target": str(target.relative_to(ROOT)).replace("\\", "/"),
            }
        )
        source_index += 1

    MAPPING_FILE.write_text(json.dumps(mapping, indent=2), encoding="utf-8")

    print(f"Extracted {len(extracted)} files to: {OUTPUT_DIR}")
    print(f"Mapped {len(mapping)} missing placeholder image(s)")
    print(f"Wrote mapping log: {MAPPING_FILE}")


if __name__ == "__main__":
    main()
