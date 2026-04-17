from __future__ import annotations

from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DOCX_PATH = ROOT / "refs" / "BABP Assembly Instructions V0.1.docx"
OUTPUT_DIR = ROOT / "refs" / "extracted-media"
STOCK_MAGWELL_DIR = ROOT / "docs" / "media" / "stock-magwell"


def main() -> None:
    if not DOCX_PATH.exists():
        raise FileNotFoundError(f"Reference document not found: {DOCX_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    STOCK_MAGWELL_DIR.mkdir(parents=True, exist_ok=True)

    # Clean previously extracted files so reruns are deterministic.
    for existing in OUTPUT_DIR.iterdir():
        if existing.is_file():
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

    # Map the first extracted image to the currently referenced stock-magwell placeholder.
    placeholder = STOCK_MAGWELL_DIR / f"attach-buttplate_picture1{extracted[0].suffix.lower()}"
    shutil.copy2(extracted[0], placeholder)

    print(f"Extracted {len(extracted)} files to: {OUTPUT_DIR}")
    print(f"Mapped current placeholder image: {placeholder.name}")


if __name__ == "__main__":
    main()
