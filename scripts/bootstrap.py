"""
Bootstrap script: generates bilingual JSON files by aligning
01_parsed/en/ (structured English) with 02_translated/pt/*.md (Portuguese markdown).

Usage:
    python scripts/bootstrap.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"


def load_parsed_json(work_path: Path) -> dict:
    with open(work_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_pt_markdown(md_path: Path) -> dict[str, dict]:
    """Parse Portuguese markdown into {chapter_title_slug: {title, text, notes}}.

    Uses chapter titles for matching instead of numbers, since numbering
    may differ between parsed JSON and translated markdown.
    """
    text = md_path.read_text(encoding="utf-8")

    chapters = {}
    current_key = None
    current_title = ""
    current_lines = []
    current_notes = []

    def save_current():
        if current_key and (current_lines or current_notes):
            full_text = "\n\n".join(current_lines)
            chapters[current_key] = {
                "title_pt": current_title,
                "text_pt": full_text,
                "notes_pt": current_notes[:]
            }

    for line in text.split("\n"):
        # Match chapter headers: "## Capítulo N — Title" or "## Capítulo N"
        ch_match = re.match(r"^## Capítulo\s+\d+\s*[—–-]?\s*(.*)", line)
        if ch_match:
            save_current()
            current_title = ch_match.group(1).strip()
            # Create a slug from the title for matching
            current_key = re.sub(r"[^\w\s]", "", current_title.lower()).strip()
            current_key = re.sub(r"\s+", "_", current_key)
            if not current_key:
                current_key = f"chapter_{len(chapters)+1}"
            current_lines = []
            current_notes = []
            continue

        # Skip non-content headers
        if line.startswith("###") or line.startswith("---") or line.startswith("# "):
            continue
        if line.startswith("**Autor:") or line.startswith("**Nome completo:"):
            continue
        if re.match(r"^## (LIVRO|Prefácio|Da Encarnação)", line):
            continue

        # Notes
        note_match = re.match(r"^\s+\[Nota (\d+)\]:\s*(.*)", line)
        if note_match:
            current_notes.append({
                "number": note_match.group(1),
                "text": note_match.group(2).strip()
            })
            continue

        # Regular paragraph text
        if line.strip() and current_key is not None:
            current_lines.append(line.strip())

    save_current()
    return chapters


def merge_paragraphs_to_blocks(paragraphs: list[str]) -> list[dict]:
    """Group consecutive text lines into paragraph blocks, separate notes."""
    blocks = []
    current_text_lines = []

    for line in paragraphs:
        if line.startswith("[Nota "):
            # Note line — attach to previous block
            if blocks:
                blocks[-1]["notes_pt"].append(line)
            continue

        # Check if this starts a new section (numbered marker)
        if re.match(r"^\*\*\(\d+\)\*\*", line):
            # Save previous block
            if current_text_lines:
                blocks.append({
                    "text_pt": "\n\n".join(current_text_lines),
                    "notes_pt": []
                })
                current_text_lines = []
            current_text_lines.append(line)
        else:
            current_text_lines.append(line)

    if current_text_lines:
        blocks.append({
            "text_pt": "\n\n".join(current_text_lines),
            "notes_pt": []
        })

    return blocks


def slugify(text: str) -> str:
    """Create a matching slug from a title."""
    s = re.sub(r"[^\w\s]", "", text.lower()).strip()
    return re.sub(r"\s+", "_", s)


def build_bilingual_json(parsed: dict, pt_chapters: dict[str, dict], work_id: str) -> dict:
    """Merge English parsed JSON with Portuguese chapter text.

    Matching is done by title similarity (slugified), with chapter-level
    text alignment rather than paragraph-level to avoid boundary mismatches.
    """
    metadata = parsed["metadata"]

    bilingual = {
        "metadata": {
            "canonical_id": work_id,
            "title_en": metadata.get("title", ""),
            "title_pt": "",
            "author_en": metadata.get("author_short", ""),
            "author_pt": "",
            "author_full": metadata.get("author_full", ""),
            "subjects": metadata.get("subjects", []),
            "lang_original": "en",
            "lang_translated": "pt",
            "rights": metadata.get("rights", "Public Domain"),
            "ccel_id": metadata.get("ccel_id", ""),
            "translation_method": "claude-opus-4-6 (1M context)",
            "translation_passes": 3,
            "pass_descriptions": [
                "Full editorial translation with theological glossary",
                "Editorial review: fidelity, fluency, terminological consistency",
                "Final polish: typography, capitalization, biblical references"
            ]
        },
        "chapters": []
    }

    # Build EN text per chapter (concatenate all paragraphs)
    for chapter in parsed["chapters"]:
        en_paragraphs = chapter.get("paragraphs", [])
        en_full_text = "\n\n".join(p.get("text", "") for p in en_paragraphs)
        en_notes = []
        en_refs = []
        for p in en_paragraphs:
            en_notes.extend(p.get("notes", []))
            en_refs.extend(p.get("scripture_refs", []))

        # Try to find matching PT chapter by title slug
        en_title = chapter.get("title", "")
        en_slug = slugify(en_title)
        pt_match = None

        # Direct slug match
        if en_slug in pt_chapters:
            pt_match = pt_chapters[en_slug]
        else:
            # Try partial match (first 3+ words)
            for pt_slug, pt_data in pt_chapters.items():
                # Check if slugs share significant words
                en_words = set(en_slug.split("_")) - {"the", "of", "and", "a", "in", "on", "to", "for"}
                pt_words = set(pt_slug.split("_")) - {"da", "do", "de", "e", "a", "em", "no", "na", "o", "as", "os", "ao", "das", "dos", "como"}
                if len(en_words) >= 2 and len(pt_words) >= 2:
                    # Simple heuristic: check if chapter order matches
                    pass

        ch_data = {
            "number": chapter["number"],
            "title_en": en_title,
            "title_pt": pt_match["title_pt"] if pt_match else None,
            "subtitle_en": chapter.get("subtitle", ""),
            "text_en": en_full_text if en_full_text.strip() else None,
            "text_pt": pt_match["text_pt"] if pt_match else None,
            "notes_en": [{"number": n.get("number", ""), "text": n.get("text", "")} for n in en_notes],
            "notes_pt": pt_match["notes_pt"] if pt_match else [],
            "scripture_refs": [{"passage": r.get("passage", ""), "display": r.get("display", "")} for r in en_refs],
            "paragraph_ids": [p.get("id", "") for p in en_paragraphs],
            "has_translation": pt_match is not None
        }

        bilingual["chapters"].append(ch_data)

    return bilingual


def build_bilingual_json_sequential(parsed: dict, pt_by_ch_num: dict[int, dict], work_id: str) -> dict:
    """Build bilingual JSON using sequential chapter mapping."""
    metadata = parsed["metadata"]

    bilingual = {
        "metadata": {
            "canonical_id": work_id,
            "title_en": metadata.get("title", ""),
            "title_pt": "",
            "author_en": metadata.get("author_short", ""),
            "author_pt": "",
            "author_full": metadata.get("author_full", ""),
            "subjects": metadata.get("subjects", []),
            "lang_original": "en",
            "lang_translated": "pt",
            "rights": metadata.get("rights", "Public Domain"),
            "ccel_id": metadata.get("ccel_id", ""),
            "translation_method": "claude-opus-4-6 (1M context)",
            "translation_passes": 3,
            "pass_descriptions": [
                "Full editorial translation with theological glossary",
                "Editorial review: fidelity, fluency, terminological consistency",
                "Final polish: typography, capitalization, biblical references"
            ]
        },
        "chapters": []
    }

    for chapter in parsed["chapters"]:
        ch_num = chapter["number"]
        en_paragraphs = chapter.get("paragraphs", [])
        en_full_text = "\n\n".join(p.get("text", "") for p in en_paragraphs)
        en_notes = []
        en_refs = []
        for p in en_paragraphs:
            en_notes.extend(p.get("notes", []))
            en_refs.extend(p.get("scripture_refs", []))

        pt_match = pt_by_ch_num.get(ch_num)

        ch_data = {
            "number": ch_num,
            "title_en": chapter.get("title", ""),
            "title_pt": pt_match["title_pt"] if pt_match else None,
            "subtitle_en": chapter.get("subtitle", ""),
            "text_en": en_full_text if en_full_text.strip() else None,
            "text_pt": pt_match["text_pt"] if pt_match else None,
            "notes_en": [{"number": n.get("number", ""), "text": n.get("text", "")} for n in en_notes],
            "notes_pt": pt_match["notes_pt"] if pt_match else [],
            "scripture_refs": [{"passage": r.get("passage", ""), "display": r.get("display", "")} for r in en_refs],
            "paragraph_ids": [p.get("id", "") for p in en_paragraphs],
            "has_translation": pt_match is not None
        }

        bilingual["chapters"].append(ch_data)

    return bilingual


def generate_index(layer_path: Path, works: dict) -> dict:
    """Generate _index.json for a layer."""
    index = {
        "layer": layer_path.name,
        "works": {},
        "generated_at": "2026-03-22"
    }
    for work_id, info in works.items():
        index["works"][work_id] = info
    return index


def main():
    print("=" * 60)
    print("  Bible Classics Dataset — Bootstrap")
    print("=" * 60)

    # --- 01_parsed index ---
    parsed_works = {}
    for author_dir in (DATA / "01_parsed" / "en").iterdir():
        if not author_dir.is_dir():
            continue
        for json_file in author_dir.glob("*.json"):
            parsed = load_parsed_json(json_file)
            work_id = f"{author_dir.name}:{json_file.stem}"
            total_paras = sum(len(ch.get("paragraphs", [])) for ch in parsed.get("chapters", []))
            total_notes = sum(
                len(n) for ch in parsed.get("chapters", [])
                for p in ch.get("paragraphs", [])
                for n in [p.get("notes", [])]
            )
            parsed_works[work_id] = {
                "file": f"en/{author_dir.name}/{json_file.name}",
                "title": parsed.get("metadata", {}).get("title", ""),
                "chapters": len(parsed.get("chapters", [])),
                "paragraphs": total_paras,
                "notes": total_notes
            }
            print(f"  [01_parsed] {work_id}: {total_paras} paragraphs, {total_notes} notes")

    index_01 = generate_index(DATA / "01_parsed", parsed_works)
    index_01["total_works"] = len(parsed_works)
    with open(DATA / "01_parsed" / "_index.json", "w", encoding="utf-8") as f:
        json.dump(index_01, f, indent=2, ensure_ascii=False)

    # --- 02_translated bilingual JSONs ---
    translations = {
        "athanasius:incarnation": {
            "parsed_path": DATA / "01_parsed" / "en" / "athanasius" / "incarnation.json",
            "md_path": DATA / "02_translated" / "pt" / "athanasius" / "incarnation.md",
            "out_path": DATA / "02_translated" / "pt" / "athanasius" / "incarnation.json",
            "title_pt": "Da Encarnação do Verbo",
            "author_pt": "Santo Atanásio",
            "status": "complete"
        },
        "kempis:imitation": {
            "parsed_path": DATA / "01_parsed" / "en" / "kempis" / "imitation.json",
            "md_path": DATA / "02_translated" / "pt" / "kempis" / "imitation_book1.md",
            "out_path": DATA / "02_translated" / "pt" / "kempis" / "imitation_book1.json",
            "title_pt": "Imitação de Cristo",
            "author_pt": "Tomás de Kempis",
            "status": "partial",
            "section": "book_1"
        },
        "lawrence:practice": {
            "parsed_path": DATA / "01_parsed" / "en" / "lawrence" / "practice.json",
            "md_path": DATA / "02_translated" / "pt" / "lawrence" / "practice.md",
            "out_path": DATA / "02_translated" / "pt" / "lawrence" / "practice.json",
            "title_pt": "A Prática da Presença de Deus",
            "author_pt": "Irmão Lourenço",
            "status": "complete"
        }
    }

    translated_works = {}

    for work_id, config in translations.items():
        print(f"\n  [02_translated] Processing {work_id}...")

        parsed = load_parsed_json(config["parsed_path"])
        pt_chapters_raw = parse_pt_markdown(config["md_path"])

        # Convert to ordered list for sequential matching
        pt_list = list(pt_chapters_raw.values())

        # Filter EN chapters that have content (skip empty dividers/indexes/forewords)
        skip_titles = {"title page", "foreword", "indexes", "subject index",
                       "index of scripture references", "index of names",
                       "index of pages of the print edition"}
        en_content_chapters = [
            ch for ch in parsed["chapters"]
            if ch.get("paragraphs") and len(ch["paragraphs"]) > 0
            and ch.get("title", "").lower() not in skip_titles
        ]

        print(f"    EN total chapters: {len(parsed['chapters'])}")
        print(f"    EN chapters with content: {len(en_content_chapters)}")
        print(f"    PT chapters found: {len(pt_list)}")

        # Build sequential mapping: PT chapter i → EN content chapter i
        pt_by_en_number = {}
        for i, pt_data in enumerate(pt_list):
            if i < len(en_content_chapters):
                en_ch_num = en_content_chapters[i]["number"]
                pt_by_en_number[en_ch_num] = pt_data
                if i < 3:
                    print(f"    Mapping: EN ch{en_ch_num} '{en_content_chapters[i]['title'][:40]}' ↔ PT '{pt_data['title_pt'][:40]}'")

        # Rebuild pt_chapters dict keyed by slug for build_bilingual_json
        # But we'll pass the mapping directly
        bilingual = build_bilingual_json_sequential(parsed, pt_by_en_number, work_id)
        bilingual["metadata"]["title_pt"] = config["title_pt"]
        bilingual["metadata"]["author_pt"] = config["author_pt"]

        # Count aligned chapters
        total_en = len([ch for ch in bilingual["chapters"] if ch.get("text_en")])
        total_aligned = sum(1 for ch in bilingual["chapters"] if ch.get("has_translation"))

        with open(config["out_path"], "w", encoding="utf-8") as f:
            json.dump(bilingual, f, indent=2, ensure_ascii=False)

        translated_works[work_id] = {
            "file": f"pt/{config['out_path'].relative_to(DATA / '02_translated' / 'pt')}",
            "markdown": f"pt/{config['md_path'].relative_to(DATA / '02_translated' / 'pt')}",
            "status": config["status"],
            "chapters_en": total_en,
            "chapters_aligned": total_aligned,
            "coverage": f"{total_aligned/total_en*100:.1f}%" if total_en > 0 else "0%"
        }
        print(f"    Aligned: {total_aligned}/{total_en} paragraphs ({translated_works[work_id]['coverage']})")
        print(f"    Saved: {config['out_path']}")

    index_02 = generate_index(DATA / "02_translated", translated_works)
    index_02["language"] = "pt"
    index_02["total_works"] = len(translated_works)
    with open(DATA / "02_translated" / "_index.json", "w", encoding="utf-8") as f:
        json.dump(index_02, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print("  Bootstrap complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
