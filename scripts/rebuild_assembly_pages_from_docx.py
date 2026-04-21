from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
DOCX_PATH = ROOT / "refs" / "BABP Assembly Instructions V0.1.docx"
DOCS_ASSEMBLY_DIR = ROOT / "docs" / "assembly"
MEDIA_ROOT = ROOT / "docs" / "media"
EXTRACTED_MEDIA_DIR = ROOT / "refs" / "extracted-media"
MAPPING_FILE = EXTRACTED_MEDIA_DIR / "placeholder-mapping.json"

SECTION_DIR_BY_TITLE = {
    "Customization Options": "customization-options",
    "Stock/Magwell Assembly": "stock-magwell",
    "Shroud Assembly": "shroud",
    "Gear Tensioner Assembly": "gear-tensioner",
    "Receiver Assembly": "receiver",
    "Prime Block Assembly": "prime-block",
    "Core Assembly": "core",
    "Loader Assembly": "loader",
    "Turnaround Assembly": "turnaround",
    "Final Assembly": "final",
    "Troubleshooting": "troubleshooting",
    "Tuning/Maintenance": "tuning-maintenance",
}

MAIN_SECTION_TITLES = list(SECTION_DIR_BY_TITLE)


@dataclass
class Para:
    idx: int
    style: str
    text: str
    image_rids: list[str]


@dataclass
class Step:
    text: str
    image_rids: list[str]


def slugify(value: str) -> str:
    slug = value.lower().strip()
    slug = slug.replace("/", "-")
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def get_image_rids(para) -> list[str]:
    # Extract all image embed ids from a paragraph while preserving order.
    blips = para._p.xpath('.//a:blip[@r:embed]')
    return [blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed') for blip in blips]


def load_paragraphs(doc: Document) -> list[Para]:
    out: list[Para] = []
    for i, para in enumerate(doc.paragraphs):
        style = para.style.name if para.style else "normal"
        text = para.text.strip().replace("\t", " ")
        image_rids = get_image_rids(para)
        out.append(Para(idx=i, style=style, text=text, image_rids=image_rids))
    return out


def find_main_sections(paras: list[Para]) -> list[tuple[str, int, int]]:
    starts: list[tuple[str, int]] = []
    for i, p in enumerate(paras):
        if p.style == "Heading 1" and p.text in MAIN_SECTION_TITLES:
            starts.append((p.text, i))

    sections: list[tuple[str, int, int]] = []
    for idx, (title, start) in enumerate(starts):
        end = starts[idx + 1][1] if idx + 1 < len(starts) else len(paras)
        sections.append((title, start, end))
    return sections


def build_steps(paras: list[Para], start: int, end: int) -> list[Step]:
    steps: list[Step] = []
    pending_images: list[str] = []

    for p in paras[start:end]:
        is_heading = p.style.startswith("Heading")
        if is_heading and p.text:
            pending_images = []
            continue

        if p.text:
            image_rids = pending_images + p.image_rids
            steps.append(Step(text=p.text, image_rids=image_rids))
            pending_images = []
        else:
            if p.image_rids:
                pending_images.extend(p.image_rids)

    return steps


def find_first_subheading(paras: list[Para], start: int, end: int, styles: set[str]) -> int:
    for i in range(start, end):
        p = paras[i]
        if p.style in styles and p.text:
            return i
    return end


def subrange_by_heading(
    paras: list[Para],
    start: int,
    end: int,
    heading_style: str,
    heading_text: str,
    next_markers: list[tuple[str, str]],
) -> tuple[int, int]:
    h_start = None
    for i in range(start, end):
        p = paras[i]
        if p.style == heading_style and p.text == heading_text:
            h_start = i + 1
            break
    if h_start is None:
        return (end, end)

    h_end = end
    for i in range(h_start, end):
        p = paras[i]
        for style, text in next_markers:
            if p.style == style and p.text == text:
                h_end = i
                return (h_start, h_end)
    return (h_start, h_end)


def render_page(
    title: str,
    overview_lines: list[str],
    steps: list[Step],
    media_section: str,
    page_slug: str,
    doc: Document,
    mappings: list[dict[str, str]],
) -> str:
    lines: list[str] = [f"# {title}", ""]

    materials_path = DOCS_ASSEMBLY_DIR / media_section / "materials.md"
    if materials_path.exists() and page_slug == "index":
        lines.append("[View Materials List](materials.md)")
        lines.append("")

    if overview_lines:
        lines.append("## Overview")
        for line in overview_lines:
            lines.append(line)
            lines.append("")

    lines.append("## Steps")
    lines.append("")

    if not steps:
        lines.append("No documented steps in the reference document for this section.")
        lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    for idx, step in enumerate(steps, start=1):
        lines.append(f"### Step {idx}")
        lines.append(step.text)
        lines.append("")

        by_ext: dict[str, int] = {}
        for rid in step.image_rids:
            part = doc.part.related_parts.get(rid)
            if part is None:
                continue
            source_name = Path(str(part.partname)).name
            ext = Path(source_name).suffix.lower() or ".png"
            by_ext[ext] = by_ext.get(ext, 0) + 1
            image_idx = by_ext[ext]

            media_dir = MEDIA_ROOT / media_section
            media_dir.mkdir(parents=True, exist_ok=True)

            base = page_slug if page_slug != "index" else media_section
            target_name = f"{base}-step-{idx:02d}_picture{image_idx}{ext}"
            target_path = media_dir / target_name

            target_path.write_bytes(part.blob)

            mappings.append(
                {
                    "source": f"word/media/{source_name}",
                    "target": str(target_path.relative_to(ROOT)).replace('\\', '/'),
                    "strategy": "docx-paragraph-order",
                    "step": f"{media_section}/{page_slug}#{idx}",
                }
            )
            lines.append(f"![Step {idx} image {image_idx}](../../media/{media_section}/{target_name})")
        if step.image_rids:
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_page(rel_path: str, content: str) -> None:
    path = DOCS_ASSEMBLY_DIR / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def section_steps_and_overview(paras: list[Para], start: int, end: int, first_subheading_styles: set[str]) -> tuple[list[str], list[Step]]:
    sub_start = find_first_subheading(paras, start, end, first_subheading_styles)
    overview = [p.text for p in paras[start:sub_start] if p.style == "normal" and p.text]
    steps = build_steps(paras, start, sub_start)
    return overview, steps


def main() -> None:
    if not DOCX_PATH.exists():
        raise FileNotFoundError(f"Reference DOCX missing: {DOCX_PATH}")

    doc = Document(DOCX_PATH)
    paras = load_paragraphs(doc)
    sections = find_main_sections(paras)

    EXTRACTED_MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    mappings: list[dict[str, str]] = []

    bounds = {title: (start, end) for title, start, end in sections}

    # Customization Options
    start, end = bounds["Customization Options"]
    overview = [p.text for p in paras[start + 1:end] if p.style == "normal" and p.text]
    page = render_page(
        title="Customization Options",
        overview_lines=overview,
        steps=[],
        media_section="customization-options",
        page_slug="index",
        doc=doc,
        mappings=mappings,
    )
    write_page("customization-options/index.md", page)

    # Stock/Magwell
    start, end = bounds["Stock/Magwell Assembly"]
    steps = build_steps(paras, start + 1, end)
    page = render_page(
        title="Stock/Magwell Assembly",
        overview_lines=[],
        steps=steps,
        media_section="stock-magwell",
        page_slug="index",
        doc=doc,
        mappings=mappings,
    )
    write_page("stock-magwell/index.md", page)

    # Shroud main + variants
    start, end = bounds["Shroud Assembly"]

    rail_start, rail_end = subrange_by_heading(
        paras,
        start,
        end,
        heading_style="Heading 2",
        heading_text="Railgun Variant",
        next_markers=[("Heading 2", "Railgun Bipod Variant")],
    )
    bipod_sub_start, bipod_sub_end = subrange_by_heading(
        paras,
        start,
        end,
        heading_style="Heading 3",
        heading_text="Bipod Sub Assembly",
        next_markers=[("Heading 3", "Final Assembly")],
    )
    bipod_start, bipod_end = subrange_by_heading(
        paras,
        start,
        end,
        heading_style="Heading 3",
        heading_text="Final Assembly",
        next_markers=[("Heading 1", "Gear Tensioner Assembly")],
    )

    shroud_overview = [
        "The shroud has two variants documented in the reference guide:",
        "- [Railgun Variant](railgun.md)",
        "- [Railgun Bipod Variant](bipod.md)",
        "- [Bipod Sub Assembly](bipod-sub-assembly.md)",
    ]
    write_page(
        "shroud/index.md",
        render_page(
            title="Shroud Assembly",
            overview_lines=shroud_overview,
            steps=[],
            media_section="shroud",
            page_slug="index",
            doc=doc,
            mappings=mappings,
        ),
    )

    write_page(
        "shroud/railgun.md",
        render_page(
            title="Railgun Variant",
            overview_lines=[],
            steps=build_steps(paras, rail_start, rail_end),
            media_section="shroud",
            page_slug="railgun",
            doc=doc,
            mappings=mappings,
        ),
    )
    write_page(
        "shroud/bipod-sub-assembly.md",
        render_page(
            title="Bipod Sub Assembly",
            overview_lines=[],
            steps=build_steps(paras, bipod_sub_start, bipod_sub_end),
            media_section="shroud",
            page_slug="bipod-sub-assembly",
            doc=doc,
            mappings=mappings,
        ),
    )
    write_page(
        "shroud/bipod.md",
        render_page(
            title="Railgun Bipod Variant Final Assembly",
            overview_lines=[],
            steps=build_steps(paras, bipod_start, bipod_end),
            media_section="shroud",
            page_slug="bipod",
            doc=doc,
            mappings=mappings,
        ),
    )

    # Gear tensioner
    start, end = bounds["Gear Tensioner Assembly"]
    write_page(
        "gear-tensioner/index.md",
        render_page(
            title="Gear Tensioner Assembly",
            overview_lines=[],
            steps=build_steps(paras, start + 1, end),
            media_section="gear-tensioner",
            page_slug="index",
            doc=doc,
            mappings=mappings,
        ),
    )

    # Receiver
    start, end = bounds["Receiver Assembly"]
    write_page(
        "receiver/index.md",
        render_page(
            title="Receiver Assembly",
            overview_lines=[],
            steps=build_steps(paras, start + 1, end),
            media_section="receiver",
            page_slug="index",
            doc=doc,
            mappings=mappings,
        ),
    )

    # Prime block + variants
    start, end = bounds["Prime Block Assembly"]
    common_start, common_end = subrange_by_heading(
        paras,
        start,
        end,
        heading_style="Heading 2",
        heading_text="Common Assembly",
        next_markers=[("Heading 2", "Bolt Action Assembly")],
    )
    bolt_start, bolt_end = subrange_by_heading(
        paras,
        start,
        end,
        heading_style="Heading 2",
        heading_text="Bolt Action Assembly",
        next_markers=[("Heading 2", "Straight Pull Assembly")],
    )
    straight_start, straight_end = subrange_by_heading(
        paras,
        start,
        end,
        heading_style="Heading 2",
        heading_text="Straight Pull Assembly",
        next_markers=[("Heading 2", "Dual Straight Pull Assembly")],
    )
    dual_start, dual_end = subrange_by_heading(
        paras,
        start,
        end,
        heading_style="Heading 2",
        heading_text="Dual Straight Pull Assembly",
        next_markers=[("Heading 1", "Core Assembly")],
    )

    pb_overview = [p.text for p in paras[start + 1:common_start - 1] if p.style == "normal" and p.text]
    write_page(
        "prime-block/index.md",
        render_page(
            title="Prime Block Assembly",
            overview_lines=pb_overview,
            steps=[],
            media_section="prime-block",
            page_slug="index",
            doc=doc,
            mappings=mappings,
        ),
    )
    write_page(
        "prime-block/common-assembly.md",
        render_page(
            title="Common Assembly",
            overview_lines=[],
            steps=build_steps(paras, common_start, common_end),
            media_section="prime-block",
            page_slug="common-assembly",
            doc=doc,
            mappings=mappings,
        ),
    )
    write_page(
        "prime-block/bolt-action.md",
        render_page(
            title="Bolt Action Assembly",
            overview_lines=[],
            steps=build_steps(paras, bolt_start, bolt_end),
            media_section="prime-block",
            page_slug="bolt-action",
            doc=doc,
            mappings=mappings,
        ),
    )
    write_page(
        "prime-block/straight-pull.md",
        render_page(
            title="Straight Pull Assembly",
            overview_lines=[],
            steps=build_steps(paras, straight_start, straight_end),
            media_section="prime-block",
            page_slug="straight-pull",
            doc=doc,
            mappings=mappings,
        ),
    )
    write_page(
        "prime-block/dual-straight-pull.md",
        render_page(
            title="Dual Straight Pull Assembly",
            overview_lines=[],
            steps=build_steps(paras, dual_start, dual_end),
            media_section="prime-block",
            page_slug="dual-straight-pull",
            doc=doc,
            mappings=mappings,
        ),
    )

    # Core + subpages
    start, end = bounds["Core Assembly"]
    plunger_start, plunger_end = subrange_by_heading(
        paras,
        start,
        end,
        heading_style="Heading 2",
        heading_text="Plunger Sub Assembly",
        next_markers=[("Heading 2", "Final Assembly")],
    )
    core_final_start, core_final_end = subrange_by_heading(
        paras,
        start,
        end,
        heading_style="Heading 2",
        heading_text="Final Assembly",
        next_markers=[("Heading 1", "Loader Assembly")],
    )

    core_overview = [p.text for p in paras[start + 1:plunger_start - 1] if p.style == "normal" and p.text]
    write_page(
        "core/index.md",
        render_page(
            title="Core Assembly",
            overview_lines=core_overview,
            steps=[],
            media_section="core",
            page_slug="index",
            doc=doc,
            mappings=mappings,
        ),
    )
    write_page(
        "core/plunger-sub-assembly.md",
        render_page(
            title="Plunger Sub Assembly",
            overview_lines=[],
            steps=build_steps(paras, plunger_start, plunger_end),
            media_section="core",
            page_slug="plunger-sub-assembly",
            doc=doc,
            mappings=mappings,
        ),
    )
    write_page(
        "core/final-assembly.md",
        render_page(
            title="Final Assembly",
            overview_lines=[],
            steps=build_steps(paras, core_final_start, core_final_end),
            media_section="core",
            page_slug="final-assembly",
            doc=doc,
            mappings=mappings,
        ),
    )

    # Loader
    start, end = bounds["Loader Assembly"]
    write_page(
        "loader/index.md",
        render_page(
            title="Loader Assembly",
            overview_lines=[],
            steps=build_steps(paras, start + 1, end),
            media_section="loader",
            page_slug="index",
            doc=doc,
            mappings=mappings,
        ),
    )

    # Turnaround
    start, end = bounds["Turnaround Assembly"]
    write_page(
        "turnaround/index.md",
        render_page(
            title="Turnaround Assembly",
            overview_lines=[],
            steps=build_steps(paras, start + 1, end),
            media_section="turnaround",
            page_slug="index",
            doc=doc,
            mappings=mappings,
        ),
    )

    # Final
    start, end = bounds["Final Assembly"]
    write_page(
        "final/index.md",
        render_page(
            title="Final Assembly",
            overview_lines=[],
            steps=build_steps(paras, start + 1, end),
            media_section="final",
            page_slug="index",
            doc=doc,
            mappings=mappings,
        ),
    )

    # Troubleshooting + tuning pages (heading-only in reference)
    start, end = bounds["Troubleshooting"]
    write_page(
        "troubleshooting/index.md",
        render_page(
            title="Troubleshooting",
            overview_lines=[p.text for p in paras[start + 1:end] if p.style == "normal" and p.text],
            steps=[],
            media_section="other",
            page_slug="troubleshooting",
            doc=doc,
            mappings=mappings,
        ),
    )

    start, end = bounds["Tuning/Maintenance"]
    write_page(
        "tuning-maintenance/index.md",
        render_page(
            title="Tuning/Maintenance",
            overview_lines=[p.text for p in paras[start + 1:end] if p.style == "normal" and p.text],
            steps=[],
            media_section="other",
            page_slug="tuning-maintenance",
            doc=doc,
            mappings=mappings,
        ),
    )

    MAPPING_FILE.write_text(json.dumps(mappings, indent=2), encoding="utf-8")
    print(f"Rebuilt assembly pages with {len(mappings)} image mappings")


if __name__ == "__main__":
    main()
