---
title: Analytical Methods
---

# Analytical Methods

This document describes the computational analysis pipeline applied to the cleaned corpus: corpus preparation for topic modeling, model selection and training, topic labeling and categorization, and the preparation of Datawrapper chart data.

## Topic Modeling

Topic modeling was conducted using [MALLET](https://mimno.github.io/Mallet/) (Machine Learning for Language Toolkit), which implements Latent Dirichlet Allocation (LDA) with efficient Gibbs sampling. Two parallel model runs were performed: one on a deduplicated corpus of original articles (1,100 documents) and one on the full corpus including reprints (1,525 documents). Comparing results across both corpora reveals how the reprinting network amplified certain discourse patterns.

### Corpus preparation

Corpus preparation proceeded in three scripted steps before any MALLET command was invoked.

**Step 1: Document normalization (`mallet_1.py`)**

Each document was assigned a unique identifier (`DOC_000001` through `DOC_001535`) and two text representations were generated:

- `dedup_text`: All text lowercased, punctuation and digits removed. Used only for similarity-based reprint detection in the next step.
- `model_text`: Lightly cleaned text preserving original wording. Used as MALLET input.

**Step 2: Reprint detection and deduplication (`mallet_2.py`)**

Nineteenth-century newspapers routinely copied articles verbatim or with minor edits. This step identifies reprint chains using word trigram Jaccard similarity. Two documents are flagged as probable reprints if they share at least 20% of their trigrams (Jaccard threshold = 0.20) or if one text is largely contained within the other (containment threshold = 0.50 for short or truncated texts).

For each reprint group:
- The longest article is treated as the original and included in the deduplicated corpus with its full text.
- Other group members are included only if they contribute at least 20 unique words after sentence-level deduplication (shared-sentence threshold = 0.50). If they meet this threshold, a deduplicated version of their text is used as the MALLET input for the full-corpus run.

The result is two MALLET-ready text files:
- `corpus_for_mallet.txt`: 1,100 documents, one original per reprint group
- `corpus_for_mallet_all.txt`: 1,525 documents, full corpus including reprints

**Step 3: Temporal and regional labeling (`mallet_3.py`)**

Each document was enriched with metadata fields used later for time-series and regional analysis:

| Field | Description |
|---|---|
| `time_bin` | Publication year (YYYY) |
| `month` | Publication month (1–12) |
| `year_month` | Publication year-month (YYYY-MM) |
| `region_bin` | U.S. Census region: Northeast, Midwest, South, West |

The state-to-region mapping covers all 50 states, Washington D.C., and historical territories.

### Selecting the number of topics

Before training the final models, coherence scores were computed across three candidate topic counts (K = 20, 25, 30) and three random seeds per count. MALLET was run for each combination and the resulting topic keys files were parsed. Gensim's `CoherenceModel` (metric: `c_v`) was used to score each configuration against the corpus vocabulary.

K = 25 was selected based on coherence scores and interpretability: it produced internally consistent topics while maintaining sufficient granularity to distinguish sub-discourses within the largest categories (education, the Chinese Educational Mission).

### Model training

Both corpora were imported with MALLET's `import-file` command using `--keep-sequence` (required for LDA) and `--remove-stopwords`. In addition to MALLET's built-in English stopword list, a custom stopword file (`scripts/build_mallet/custom_stopwords.txt`) was compiled specifically for this corpus. It removes high-frequency terms that are uninformative for topical discrimination in this particular collection, including newspaper boilerplate (e.g., *said*, *would*, *made*), OCR artifacts, and corpus-specific proper nouns that would otherwise dominate topic keys without adding interpretive value. Training was conducted with the following parameters:

```
mallet train-topics \
  --input corpus.mallet \
  --num-topics 25 \
  --optimize-interval 20 \
  --num-iterations 10000 \
  --output-topic-keys topic_keys.txt \
  --output-doc-topics doc_topics.txt
```

| Parameter | Value | Rationale |
|---|---|---|
| `--num-topics` | 25 | Selected by coherence evaluation |
| `--num-iterations` | 10,000 | Ensures Gibbs sampling convergence |
| `--optimize-interval` | 20 | Enables hyperparameter (alpha/beta) optimization during training |

Two model runs were saved:
- **Deduped model** (K25_S2): trained on the 1,100-document deduplicated corpus
- **Full-corpus model** (K25_S1): trained on the 1,525-document full corpus

### Topic labeling and categorization

Each of the 25 topics in both models was manually reviewed using the highest-probability words and the top documents. Five topics were excluded as OCR noise (empty or near-empty vocabulary, dominated by symbols and garbled tokens). The remaining 20 substantive topics were labeled at two levels:

- **Analytic label**: a short descriptive title (e.g., "Public School Admission")
- **Discourse label**: a longer interpretive phrase capturing the register (e.g., *"Born on This Soil": The Courtroom Battle over School Access*)

Topics were then grouped into 9 thematic categories:

| Category | Topics |
|---|---|
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#fe640b;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Chinese Educational Mission | 4 topics (deduped model merges these into one) |
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#209fb5;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Education & Schools | Public School Admission, Missionary & Church Schools, Classroom Instruction |
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#40a02b;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Children & Family | Children & Family Life, Confucian Family Ethics |
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#1e66f5;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Daily Life & Urban Space | Domestic Employment, Urban Chinatown & Criminal Cases |
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#8839ef;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Law, Politics & Exclusion | Exclusion Legislation, Anti-Chinese Violence |
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#179299;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Commerce & Material Culture | Trade in Chinese Goods, East Asian Consumer Goods |
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#df8e1d;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Land, Migration & Labor | Hawaii & Pacific Migration, Labor & Mining Camps |
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#ea76cb;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Culture, Perception & Acculturation | Physical Appearance & Curiosity Narratives |
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#7287fd;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Diplomacy | Diplomacy & Ceremonial Events |

Topic labels, category assignments, and color codes are stored in `data/topic_labels.csv` (deduped model), `data/all_topic_labels.csv` (full-corpus model), and `data/merged_topic_labels.csv` (cross-model comparison).

## Datawrapper Visualizations

All charts embedded in the analysis pages were built using Python preprocessing scripts that output Datawrapper-ready CSV files. Each CSV was uploaded to Datawrapper and configured manually for color, annotation, and interactivity. The charts are embedded in the site via the `<DatawrapperChart>` Vue component.

### Scatter plot: thematic landscape (Chart 1)

Script: `scripts/build_datawrapper_data/chart1_build_scatter.py`

Two scatter plot CSVs are generated from the MALLET output and dataset metadata.

The **analysis scatter** (`scatter_analysis.csv`) places each document on a grid with publication year on the horizontal axis and topic category on the vertical axis. Deterministic jitter (seed = 42) is applied to both axes to prevent overplotting. Documents are colored by topic category using the `category_color` field from the topic labels CSV.

The **showcase scatter** (`scatter_showcase.csv`) is used for homepage display. It uses exact publication date on the horizontal axis and dominant topic confidence (weight × 100) on the vertical axis. For each document, a KWIC (Key Word in Context) snippet is extracted from the `model_text` field using a tiered keyword pattern: Chinese-education collocations are prioritized, followed by general Chinese mentions, with a 120-character context window.

### Education topics time series (Chart 2)

Script: `scripts/build_datawrapper_data/chart2_edu_lines.py`

The MALLET doc-topics file is parsed to extract per-document weights for four education-related topics: Chinese Educational Mission, Classroom Instruction, Public School Admission, and Missionary & Church Schools. Weights are aggregated by publication month (`year_month`) and converted to percentages. The output is a wide-format CSV with one row per month and one column per topic, used to draw the four-line time series chart.

### Topic prominence comparison (Charts 4, 5, 5B)

Scripts: `chart4_build_split.py`, `chart5_build_dotplot.py`, `chart5B_build_dotplot.py`

These charts compare topic weights between the deduplicated and full corpora. Mean topic weights are computed separately for both model runs. The dumbbell and dot-plot charts show each topic as a paired point (deduplicated weight in blue, full-corpus weight in red) with a connecting bar indicating the magnitude and direction of the reprint effect. The bar chart (`chart5B`) ranks topics by the percentage-point difference between the two corpora.

### Alluvial flow diagram (Chart 5C)

Script: `scripts/build_datawrapper_data/chart5C_build_alluvial_flow.py`

This chart maps the 1,100 documents present in both corpora to their dominant category in each model, plus the 425 reprint-only documents that appear only in the full-corpus model. For the shared documents, the dominant category is compared across both model runs; for reprint-only documents, the source node is labeled "New (reprints)."

The output is an edge-list CSV (source category, target category, count). The Sankey diagram itself was built using [RAWGraphs](https://www.rawgraphs.io/), an open-source data visualization framework, and exported as an SVG for embedding.

### Heatmap: keyword-to-topic loadings (Chart 7)

Script: `scripts/build_datawrapper_data/chart7_build_heatmap.py`

For each of the seven search keywords, the mean topic weight across all documents retrieved with that keyword is computed. The result is a keyword × topic matrix showing which topics are disproportionately associated with each search term. This reveals how the choice of vocabulary shaped what the corpus contains.

### Entropy chart (Chart 8)

Script: `scripts/build_datawrapper_data/chart8_build_entropy.py`

Shannon entropy of the topic weight distribution is computed for each publication month. Higher entropy indicates that a month's coverage was spread across many topics; lower entropy indicates narrowing onto a few dominant themes. This chart tracks discourse concentration across the full 1880–1885 window.

### Bubble chart: presence vs. propagation (Chart 9)

Script: `scripts/build_datawrapper_data/chart9_spread.py`

Each topic category is plotted as a bubble. The horizontal axis shows total article count (presence); the vertical axis shows average reprint count per article (propagation). Bubble size is proportional to total article count. This makes the distinction between topics that were written about frequently and topics that spread widely through reprinting visually explicit.
