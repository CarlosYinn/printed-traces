---
title: Dataset Construction
---

# Dataset Construction

This document describes the pipeline for transforming raw archival newspaper data into the structured corpus used for analysis. The pipeline consists of four steps: corpus assembly, geographic standardization, OCR cleaning, and excerpt extraction.


## Step 1: Corpus Assembly

Articles were collected from the Library of Congress [*Chronicling America*](https://www.loc.gov/collections/chronicling-america/about-this-collection/) digitized newspaper archive. Seven keyword queries were used to retrieve page-level records containing references to Chinese children, students, and schools:

> "Chinese student" · "Chinese boy" · "Chinese girl" · "Chinese child" · "Chinese children" · "Chinese school" · "Chinese education"

All queries used exact phrase matching and were restricted to the date range 1880–1885. For each matched page, the full OCR text of the page was retrieved to allow subsequent passage extraction. The raw collection produced approximately 1,755 unique page-level records before deduplication and quality filtering.

:::info
Exact phrase matching was chosen over proximity-based or stemmed search to minimize false positives. Broader queries (e.g., "Chinese" alone) return far too many unrelated pages to be practically usable at corpus scale.
:::


## Step 2: Geographic Standardization

The raw metadata from *Chronicling America* contains geographic information in loosely formatted text fields. This step transforms that information into structured variables suitable for regional analysis and mapping.

### Parsing location metadata

Two source fields were processed:

- **Title field**: Often formatted as "The Daily Alta California (San Francisco, Calif.)". A regular expression parser extracted the parenthetical component and split it into candidate city and state values.
- **Location field**: A list of geographic entities stored as a Python list string. The `ast.literal_eval` function was used to safely parse these lists.

Each element in the location list was classified against two reference sets:

- `US_STATES`: a comprehensive list of nineteenth-century U.S. states and territories
- `STOP_WORDS`: non-informative terms such as "united states"

Elements matching `US_STATES` were assigned to the `Pub_State` field. Elements ending in "county" were assigned to a county variable. Remaining valid geographic entities were concatenated into a `Coverage_Region` field using vertical bar delimiters (e.g., `Richland | Greenville | Columbia`).

### Historical normalization

Nineteenth-century geographic terminology required additional standardization:

- Abbreviations such as `D.T.` were expanded to `Dakota Territory`
- Variants of `Co.` and `co.` were normalized to `County`
- Historical territorial designations were preserved rather than replaced with modern equivalents

### Administrative type

An `Admin_Type` field distinguishes states from territories. A predefined list of 1880s U.S. territories was used: if a publication state contained "Territory" or matched a known territorial name (Dakota, Washington, Idaho, etc.), `Admin_Type` was set to `Territory`; otherwise to `State`.

### Regional binning

A `region_bin` field assigns each publication to one of four U.S. Census regions (Northeast, Midwest, South, West) using a state-to-region lookup table. This field supports regional comparison of discourse patterns across the corpus.


## Step 3: OCR Cleaning

Nineteenth-century newspaper OCR contains broken Unicode encodings, hyphenated line splits, symbol noise, and repetitive layout artifacts. The cleaning pipeline operates in four phases, moving from character-level repair to semantic filtering.

### Phase 1: Character normalization

The [`ftfy`](https://ftfy.readthedocs.io/) library repaired broken Unicode sequences and normalized encoding errors. A predefined character map (`SAFE_CHAR_MAP`) replaced typographic ligatures (e.g., `ﬁ` to `fi`) and irregular quotation marks. Invisible control characters (`\x00` through `\x08`) were removed.

### Phase 2: Line stitching and physical noise removal

Nineteenth-century typesetting breaks words across lines with hyphens. Regular expressions detected patterns of the form `letter + hyphen + newline + letter` and merged them into complete words. Symbol-heavy noise characters (`^^^`, `|||`, `■`, `□`) were removed. Single line breaks were merged into continuous text; multiple consecutive breaks were preserved as paragraph boundaries.

### Phase 3: Frequency-based noise filtering

Some OCR segments consist almost entirely of garbled text. For each paragraph, the ratio of alphanumeric characters to total characters was calculated. Paragraphs with excessive symbol density were flagged. The [`wordfreq`](https://pypi.org/project/wordfreq/) library's `zipf_frequency()` function was applied to estimate whether extracted tokens resembled real English vocabulary. Paragraphs dominated by extremely low-frequency or non-existent words were removed.

### Phase 4: Semantic and structural filtering

- **Long-token filtering**: Tokens exceeding 20 characters were removed, as they typically represent OCR artifacts rather than real words.

:::tip
For projects requiring more robust tokenization, [spaCy](https://spacy.io/) is a suitable drop-in alternative for the long-token filtering step.
:::
- **Repeated-line removal**: Each line was hashed with MD5; lines appearing more than three times were treated as layout boilerplate and discarded.
- **Spelling correction**: `symspellpy` was applied for lightweight repair of minor OCR distortions.

### Parallel processing

All four phases were applied using `concurrent.futures.ProcessPoolExecutor` to parallelize processing across the full corpus. This significantly reduced wall-clock time without changing the cleaning logic.


## Step 4: Excerpt Extraction

Each record contains the OCR text of an entire newspaper page. A page may include many unrelated items: advertisements, shipping news, local politics, and crime reports. This step reduces each full-page OCR block to a shorter, topic-relevant excerpt while preserving enough surrounding context for historical interpretation.

### Keyword and scoring design

Extraction uses a layered scoring system with four pattern types:

| Pattern | Role |
|---|---|
| `RX_CHINESE_EDU` | Strong signal: Chinese identifier word within 1 word of an education term |
| `RX_CHINESE` | Weak signal: any Chinese identifier present; hard rejection if absent |
| `RX_CONTEXT` | Education-adjacent vocabulary (school board, enrollment, kindergarten, etc.) |
| `RX_EXCLUDE` | Non-target themes (shipping, cargo, tea, silk, railroad); reduces score |

The scoring function returns a numeric relevance score. If no Chinese mention is present, the score is immediately set to -9999 (hard rejection). Otherwise the score is: base 50, +500 per strong Chinese-education match, +50 per context term, -5 per exclusion term.

### Extraction strategies

Two extraction strategies are applied to each document and the higher-scoring result is kept.

**Strategy A: Paragraph-based extraction.** The text is split on double newlines into paragraphs. Each paragraph is scored independently. Positive-scoring paragraphs are included along with one neighboring paragraph on each side (`PARA_WINDOW = 1`). Near-duplicate paragraphs are removed using `SequenceMatcher` similarity above 0.92. The final output is capped at 3,500 characters or 12 paragraphs.

**Strategy B: Sliding-window extraction.** This strategy handles pages where paragraph boundaries are unreliable. Overlapping 800-character windows (step size 400) are extracted, scored, and the top-scoring non-overlapping windows are kept. Each selected window is expanded to sentence boundaries. If two selected windows are separated by more than 100 characters, an explicit divider (`... [UNRELATED CONTENT] ...`) is inserted. This prevents unrelated stories from being silently merged.

:::info
Strategy B was added after inspecting pages from small-town newspapers, where paragraph formatting was frequently lost during digitization, producing single-block OCR output that paragraph-based extraction could not handle.
:::

### Output fields

The extraction step adds the following fields to each record:

| Field | Description |
|---|---|
| `OCR_cleaned` | Final extracted excerpt |
| `token_count` | Word count of the extracted excerpt |
| `relevance_tier` | Computed classification: `core` (score ≥ 550, at least one strong Chinese-education collocation) or `secondary` (Chinese mention present but below threshold) |
| `topic_tags` | Pipe-delimited list of exact keyword phrases matched in the excerpt (e.g., `chinese student\|chinese school`) |
