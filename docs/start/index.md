---
title: Get Started
---

# Get Started

This site presents the research and data from *Printed Traces: Chinese Immigrant Children in the U.S. Press, 1880–1885*, a digital history project combining corpus-based text analysis with close historical reading to examine how American newspapers represented Chinese children during the Chinese exclusion era.

## The Corpus

The dataset consists of **1,535 newspaper pages** drawn from the Library of Congress's [*Chronicling America*](https://www.loc.gov/collections/chronicling-america/about-this-collection/) digital archive, covering the years **1880–1885**. Pages were retrieved through seven keyword searches (*Chinese student*, *Chinese school*, *Chinese girl*, *Chinese children*, *Chinese child*, *Chinese boy*, and *Chinese education*) chosen to capture the range of language through which Chinese youth appeared in the press.

| Keyword | Pages |
| --- | --- |
| Chinese student | 482 |
| Chinese boy | 289 |
| Chinese children | 265 |
| Chinese girl | 227 |
| Chinese school | 168 |
| Chinese child | 81 |
| Chinese education | 23 |

After retrieval, each page was processed through OCR extraction and text cleaning to produce a machine-readable corpus. Documents were classified into two relevance tiers: **core** (1,426 pages directly relevant to Chinese children) and **secondary** (109 pages with tangential relevance). All documents were retained in the dataset, but only core documents formed the primary basis for analysis.

Publication locations span **53 states and territories** (from California and Hawaii to Connecticut and Georgia) across **323 distinct newspaper titles**. Geographic coverage is recorded at three levels: publication city, county-level `Coverage_Region` (capturing the spatial scope of each article beyond its masthead city), and a Census-region bin (`West`, `South`, `Midwest`, `Northeast`) used as an analytical grouping in the topic model.

## Reprint Detection and Deduplication

Nineteenth-century newspaper content circulated extensively through reprinting. A story originating in one paper might be copied verbatim, or lightly edited, by dozens of regional papers over the following weeks. To prevent this telegraphic reprinting from distorting the topic model, each document was compared against others using text similarity scoring, and **propagation chains** were reconstructed for reprinted items.

One article originating in the *Savannah Morning News* on April 6, 1885, for instance, was subsequently reprinted by at least ten other papers across Mississippi, Connecticut, Wisconsin, West Virginia, and Louisiana over the following three months. Tracking these chains allowed reprints to be identified and handled appropriately before modeling.

Of the 1,535 total documents:

- **946** are identified as original publications
- **749** are identified reprints carrying a `propagation_chain` record
- **161** form a further-deduplicated subset, retaining only the most distinctive portion of each reprint chain

Both the full set of originals and the deduplicated subset were submitted separately to MALLET for topic modeling, enabling comparison across sampling strategies.

## Topic Modeling with MALLET

Topic modeling was performed using [**MALLET**](https://mimno.github.io/Mallet/) (Machine Learning for Language Toolkit), an implementation of **Latent Dirichlet Allocation (LDA)**. Two model runs were produced:

| Run | Corpus | Documents | Topics (K) |
| --- | --- | --- | --- |
| **S1** | Full corpus (originals only) | 946 | 25 |
| **S2** | Deduplicated subset | 161 | 25 |

Each run produced two key output files. The **`doc-topics`** file records, for every document, a probability distribution across all 25 topics: each row is identified by a `DOC_XXXXXX` ID and contains 25 probability values that sum to 1. The **`diag`** file records diagnostic statistics for each topic, including token counts, document entropy, word-length averages, coherence scores, exclusivity, and the top 25 most probable words.

Topics were evaluated using these diagnostics, and representative documents for each topic were reviewed before labeling. Three topics in each run were identified as **noise** (covering OCR artifacts, commercial advertising text, and church or mission directory listings) and excluded from the main analysis.

## Topic Labeling

After reviewing top words and representative documents, each of the 25 topics in both S1 and S2 was assigned two labels. The **analytic label** describes content in neutral terms (e.g., *Public School Admission*, *Missionary & Church Schools*). The **discourse label** offers a more interpretive, historically grounded title suited to public-facing presentation (e.g., *"Born on This Soil": The Courtroom Battle over School Access*; *Saving Heathen Girls: Missionary Schooling and Christian Conversion*).

Topics from S1 and S2 were then cross-referenced in a **merged label table**. Where a topic appeared in both runs with similar content, the two were matched and assigned shared attributes. Topics unique to one run were retained separately.

The full set of labeled topics was organized into ten thematic categories (plus noise):

| Category | Description |
| --- | --- |
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#fe640b;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Chinese Educational Mission | Chinese government-sponsored students in the U.S. |
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#209fb5;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Education & Schools | Public school admission, classroom instruction, missionary schools |
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#40a02b;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Children & Family | Family life, childhood conditions, Confucian family ethics |
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#8839ef;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Law, Politics & Exclusion | Exclusion legislation, citizenship cases, court proceedings |
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#d20f39;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Violence & War | Anti-Chinese violence, the Sino-French War |
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#179299;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Commerce & Material Culture | Chinese goods, trade, domestic employment |
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#1e66f5;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Daily Life & Urban Space | Chinatown narratives, routine press reporting |
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#df8e1d;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Land, Migration & Labor | Hawaii and Pacific migration, agriculture, labor |
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#ea76cb;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Culture, Perception & Acculturation | Public lectures, physical curiosity narratives, opium |
| <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#7287fd;vertical-align:middle;margin-right:6px;flex-shrink:0"></span>Diplomacy | Diplomatic events and ceremonial coverage |

## Exploring the Map

The topic categories above are the primary lens through which the [interactive map](/map/interactive) can be read. Each newspaper record in the corpus is plotted as a point on a map of the United States using 1882 historical county and state boundaries from the Newberry Library's *Atlas of Historical County Boundaries*, reflecting the political geography of the exclusion era rather than present-day borders. Each point is positioned at the publication city of the paper that printed it and colored by topic category, and can be filtered by topic, time period, or one of ten anchored historical events:

| Event | Year |
| --- | --- |
| Angell Treaty Signed | 1880 |
| Chinese New Year Press Coverage Wave | 1881 |
| Chinese Educational Mission Recall Begins | 1881 |
| Chinese Exclusion Act Signed | 1882 |
| First CEM Student Graduates from Yale | 1883 |
| *Tape v. Hurley* Public School Case | 1884 |
| Sino-French War: Battle of Fuzhou | 1884 |
| Rock Springs Massacre | 1885 |
| Tacoma Expulsion | 1885 |
| Seattle Expulsion Attempt | 1886 |

The Topics panel on the map mirrors the category table above: any category can be toggled on or off, clicked to enter solo mode, or expanded to filter down to a single topic. Selecting a historical event filters the visible records to that event's date window and highlights the relevant state or county. The time filter further narrows records to a single year or month, making it possible to trace how coverage shifted around specific moments such as the Exclusion Act debate in spring 1882 or the expulsion wave in fall 1885.
