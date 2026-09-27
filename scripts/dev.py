from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
IMAGE_RE = re.compile(r"!\[[^]]*]\(([^)]+)\)|(?:src|href)=\"([^\"]+)\"")


def run(*args: str) -> None:
    print(f"> {' '.join(args)}", flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def generate() -> None:
    run(sys.executable, "scripts/generate_materials.py")
    run(sys.executable, "scripts/generate_nav.py")


def check_local_links() -> None:
    broken: list[str] = []
    for markdown in DOCS.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        for match in IMAGE_RE.finditer(text):
            raw = next(value for value in match.groups() if value)
            target = raw.split("#", 1)[0].split("?", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (markdown.parent / target).resolve()
            if resolved.exists():
                continue
            # A materials.md source renders as materials/index.html. Raw HTML
            # therefore needs one additional parent segment in its browser URL.
            # Validate that URL against the corresponding source-level path.
            if markdown.name == "materials.md" and target.startswith("../"):
                source_target = target[3:]
                if (markdown.parent / source_target).resolve().exists():
                    continue
            broken.append(f"{markdown.relative_to(ROOT)} -> {raw}")
    if broken:
        raise SystemExit("Broken local links:\n  - " + "\n  - ".join(broken))
    print("Local link validation passed.")


def check() -> None:
    run(sys.executable, "scripts/validate_materials.py")
    run(sys.executable, "scripts/generate_materials.py", "--check")
    check_local_links()
    run(sys.executable, "scripts/generate_nav.py", "--check")
    run(sys.executable, "-m", "mkdocs", "build", "--strict", "--clean")


def main() -> int:
    parser = argparse.ArgumentParser(description="BABP documentation development commands.")
    parser.add_argument("command", choices=("generate", "check", "build", "serve"))
    args = parser.parse_args()

    if args.command == "generate":
        generate()
    elif args.command == "check":
        check()
    elif args.command == "build":
        generate()
        run(sys.executable, "scripts/validate_materials.py")
        run(sys.executable, "-m", "mkdocs", "build", "--strict", "--clean")
    else:
        generate()
        run(sys.executable, "scripts/validate_materials.py")
        run(sys.executable, "-m", "mkdocs", "serve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
