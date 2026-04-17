# Copilot Instructions: BABP Assembly Documentation System

## 1. Overview

This project is a customer-facing assembly documentation system using:
- MkDocs (Material theme)
- MkSlides (Reveal.js)
- Fusion 360 media exports (PNG + MP4)

Documentation is modular and includes assemblies and variants.

---

## 2. Directory Structure

/docs
  /assembly/
    [section]/
      index.md
      materials.md
      slides.md
  /media/
    [section]/
  /data/
    materials.yml
  /materials/
    index.md

Rules:
- One folder per section
- Media grouped per section
- YAML is single source of truth

---

## 3. Media Naming Rules

Images:
[step-name]_picture[x].png

Videos:
[step-name]_video[x].mp4

Rules:
- lowercase only
- hyphens only
- no spaces

---

## 4. Page Structure

### index.md
# Section Name

[View Materials List](materials.md)

## Overview
## Steps

### Step X: Action
- Instruction
- Image
- Optional video

---

### slides.md

# Step X
Content

---

Rules:
- one step per slide
- minimal text

---

## 5. Media Embeds

Images:
![desc](../../media/section/file.png)

Videos:
<video controls>
  <source src="../../media/section/file.mp4" type="video/mp4">
</video>

---

## 6. YAML Materials System

Location:
/docs/data/materials.yml

Structure:
components:
hardware:
consumables:
sections:

IDs must be normalized and reused.

---

## 7. Variant Handling

Each section:
- base materials
- variants

Variants must not duplicate base.

---

## 8. Materials Pages

Generated from YAML.

Sections include:
- Base materials
- Variant materials

Global materials:
/docs/materials/index.md

---

## 9. Navigation Rules

Hierarchy must be preserved.
Variants nested under sections.

---

## 10. Copilot Rules

MUST:
- Use YAML as source
- Maintain naming consistency
- Generate all required files

MUST NOT:
- Hardcode materials
- Break structure
- Use inconsistent naming

---

## 11. Priority Order

1. YAML
2. Section materials
3. Global materials
4. Docs
5. Slides
