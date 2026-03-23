# Bible Classics Dataset

Bilingual EN/PT editions of Christian classic texts from the [Christian Classics Ethereal Library (CCEL)](https://www.ccel.org/), translated with editorial quality using Claude Opus 4.6 (1M context).

Part of the [NEUU](https://github.com/neuu-org) biblical studies ecosystem.

## Overview

| Metric | Value |
|--------|-------|
| Works | 2 |
| Complete translations | 1 |
| Languages | English, Portuguese (BR) |
| Translation model | Claude Opus 4.6 (1M context) |
| Translation passes | 3 (translation, review, polish) |
| Source | CCEL (Public Domain) |
| License | CC BY 4.0 |

## Works

| Work | Author | Date | Status | Chapters |
|------|--------|------|--------|----------|
| Da Encarnacao do Verbo | Santo Atanasio (c.296-373) | c.318 | Complete | 9/9 |
| Imitacao de Cristo | Tomas de Kempis (c.1380-1471) | c.1418 | Book I (25/115) | Partial |

## Translation Pipeline

```
CCEL ThML XML --> parse_thml.py --> 01_parsed/en/ (structured JSON)
                                         |
                                 Claude Opus 4.6
                                 Pass 1: Translation
                                 Pass 2: Editorial review
                                 Pass 3: Polish & standardize
                                         |
                                 02_translated/pt/ (bilingual JSON + markdown)
```

### Translation methodology

1. **Pass 1 -- Full translation**: Complete text sent with theological glossary (88 terms + proper names + biblical book names). Claude Opus 4.6's 1M context window allows sending entire books in a single call, ensuring terminological consistency.

2. **Pass 2 -- Editorial review**: Original + translation sent side-by-side for review of fidelity, fluency, terminological consistency, and naturalness in Portuguese.

3. **Pass 3 -- Final polish**: Typography, capitalization of sacred terms, biblical reference formatting (Brazilian standard), footnote sequencing.

## Repository Structure

```
bible-classics-dataset/
|-- _meta.json                          # Dataset registry
|-- data/
|   |-- PROVENANCE.json                 # SHA256 checksums & source tracking
|   |-- 00_raw/                         # Source manifests (no XML copies)
|   |   |-- athanasius/incarnation.manifest.json
|   |   +-- kempis/imitation.manifest.json
|   |-- 01_parsed/                      # Structured English from ThML
|   |   |-- _index.json
|   |   +-- en/
|   |       |-- athanasius/incarnation.json
|   |       +-- kempis/imitation.json
|   +-- 02_translated/                  # Portuguese translations
|       |-- _index.json
|       +-- pt/
|           |-- athanasius/
|           |   |-- incarnation.json    # Bilingual JSON (EN+PT)
|           |   +-- incarnation.md      # Human-readable markdown
|           +-- kempis/
|               |-- imitation_book1.json
|               +-- imitation_book1.md
+-- scripts/
    +-- bootstrap.py                    # Data migration & alignment
```

## Data Schema

### 01_parsed (English structured)

```json
{
  "metadata": {
    "title": "On the Incarnation of the Word",
    "author_short": "St. Athanasius",
    "subjects": ["Theology", "Early Church"],
    "language": "eng",
    "rights": "Public Domain",
    "ccel_id": "/ccel/athanasius/incarnation.html"
  },
  "chapters": [
    {
      "number": 1,
      "title": "Creation and the Fall",
      "paragraphs": [
        {
          "id": "ii-p2",
          "text": "In our former book...",
          "notes": [{"number": "1", "text": "i.e. the Contra Gentes."}],
          "scripture_refs": [{"passage": "Matt 19:4-6", "display": "Matt. xix. 4-6"}]
        }
      ]
    }
  ]
}
```

### 02_translated (Bilingual)

```json
{
  "metadata": {
    "canonical_id": "athanasius:incarnation",
    "title_en": "On the Incarnation of the Word",
    "title_pt": "Da Encarnacao do Verbo",
    "translation_method": "claude-opus-4-6 (1M context)",
    "translation_passes": 3
  },
  "chapters": [
    {
      "number": 2,
      "title_en": "Chapter 1",
      "title_pt": "A Criacao e a Queda",
      "text_en": "Full English chapter text...",
      "text_pt": "Texto completo do capitulo em portugues...",
      "notes_en": [{"number": "1", "text": "i.e. the Contra Gentes."}],
      "notes_pt": [{"number": "1", "text": "Isto e, o Contra Gentes."}],
      "scripture_refs": [],
      "has_translation": true
    }
  ]
}
```

## Related Datasets

| Dataset | Content |
|---------|---------|
| [bible-text-dataset](https://github.com/neuu-org/bible-text-dataset) | 17 Bible translations (EN+PT) |
| [bible-commentaries-dataset](https://github.com/neuu-org/bible-commentaries-dataset) | 55,925 verse commentaries (AD 100-1700) |
| [bible-crossrefs-dataset](https://github.com/neuu-org/bible-crossrefs-dataset) | 1.1M cross-reference edges |
| [bible-topics-dataset](https://github.com/neuu-org/bible-topics-dataset) | 7,873 biblical topics |
| [bible-dictionary-dataset](https://github.com/neuu-org/bible-dictionary-dataset) | 20,900 dictionary entries |
| [bible-gazetteers-dataset](https://github.com/neuu-org/bible-gazetteers-dataset) | 9,176 entities + 376 symbols |
| [bible-images-dataset](https://github.com/neuu-org/bible-images-dataset) | 16,914 biblical artworks |

## License

CC BY 4.0. Source texts are in the Public Domain.

## Citation

```bibtex
@misc{neuu_bible_classics_2026,
  title={Bible Classics Dataset: Bilingual EN/PT Christian Classic Texts},
  author={NEUU},
  year={2026},
  publisher={GitHub},
  url={https://github.com/neuu-org/bible-classics-dataset}
}
```
