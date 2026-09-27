from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import sys
import tomllib
from urllib.parse import unquote, urlsplit

import yaml


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
LINK_RE = re.compile(r"!?\[[^]]*]\(([^)]+)\)|(?:src|href)=\"([^\"]+)\"")
REQUIREMENTS = ROOT / "requirements.txt"
PYPROJECT = ROOT / "pyproject.toml"
MKDOCS = ROOT / "mkdocs.yml"
SITE = ROOT / "site"


def run(*args: str) -> None:
    print(f"> {' '.join(args)}", flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def generate() -> None:
    run(sys.executable, "scripts/generate_materials.py")
    run(sys.executable, "scripts/generate_nav.py")


def check_python_version() -> None:
    if sys.version_info[:2] not in {(3, 12), (3, 13)}:
        raise SystemExit(
            "Python 3.12 or 3.13 is required by pyproject.toml and CI; "
            f"current interpreter is {sys.version_info.major}.{sys.version_info.minor}."
        )
    print("Python version check passed.")


def dependency_lines(path: Path) -> set[str]:
    return {
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def check_dependency_sync() -> None:
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    declared = {item.lower() for item in project["project"]["dependencies"]}
    required = dependency_lines(REQUIREMENTS)
    if declared != required:
        only_project = sorted(declared - required)
        only_requirements = sorted(required - declared)
        details = []
        if only_project:
            details.append(f"only in pyproject.toml: {', '.join(only_project)}")
        if only_requirements:
            details.append(f"only in requirements.txt: {', '.join(only_requirements)}")
        raise SystemExit("Dependency declarations are out of sync; " + "; ".join(details))
    print("Dependency declaration check passed.")


def markdown_target(raw: str) -> str:
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        return value[1:value.index(">")]
    # Markdown permits an optional title after the destination. Project-local
    # paths do not contain unescaped spaces, so the first token is the target.
    return value.split(maxsplit=1)[0]


def check_local_links() -> None:
    broken: list[str] = []
    for markdown in DOCS.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            raw = next(value for value in match.groups() if value)
            parsed = urlsplit(markdown_target(raw))
            if parsed.scheme or parsed.netloc:
                continue
            target = unquote(parsed.path)
            if not target:
                continue
            resolved = (
                (DOCS / target.lstrip("/"))
                if target.startswith("/")
                else (markdown.parent / target)
            ).resolve()
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


class HtmlLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.targets: list[str] = []

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        self.targets.extend(
            values[name]
            for name in ("href", "src")
            if values.get(name) is not None
        )


def rendered_candidates(target: Path) -> list[Path]:
    if target.suffix:
        return [target]
    return [target / "index.html", target.with_suffix(".html")]


def check_rendered_links() -> None:
    config = yaml.safe_load(MKDOCS.read_text(encoding="utf-8")) or {}
    site_prefix = urlsplit(config.get("site_url", "")).path.rstrip("/")
    broken: list[str] = []
    html_pages = list(SITE.rglob("*.html"))

    for page in html_pages:
        parser = HtmlLinks()
        parser.feed(page.read_text(encoding="utf-8"))
        for raw in parser.targets:
            parsed = urlsplit(raw)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue

            path = unquote(parsed.path)
            if path.startswith("/"):
                if site_prefix and (path == site_prefix or path.startswith(f"{site_prefix}/")):
                    path = path[len(site_prefix):]
                target = SITE / path.lstrip("/")
            else:
                target = page.parent / path

            if not any(candidate.exists() for candidate in rendered_candidates(target.resolve())):
                broken.append(f"{page.relative_to(ROOT)} -> {raw}")

    if broken:
        raise SystemExit("Broken rendered links:\n  - " + "\n  - ".join(broken))
    print(f"Rendered link validation passed ({len(html_pages)} HTML pages).")


def check() -> None:
    check_python_version()
    check_dependency_sync()
    run(sys.executable, "scripts/validate_materials.py")
    run(sys.executable, "scripts/generate_materials.py", "--check")
    check_local_links()
    run(sys.executable, "scripts/generate_nav.py", "--check")
    run(sys.executable, "-m", "mkdocs", "build", "--strict", "--clean")
    check_rendered_links()


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
        check_rendered_links()
    else:
        generate()
        run(sys.executable, "scripts/validate_materials.py")
        run(sys.executable, "-m", "mkdocs", "serve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
