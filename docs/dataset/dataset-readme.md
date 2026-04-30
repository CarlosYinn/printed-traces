---
title: Dataset Reference
---

# Dataset Reference

## Overview

The corpus contains **1,535 records** drawn from 323 distinct newspaper titles published across the United States between January 1880 and December 1885. Each record represents one newspaper page on which relevant material was identified through keyword search. Records are sourced from [Chronicling America: Historic American Newspapers](https://www.loc.gov/collections/chronicling-america/about-this-collection/), a digital newspaper collection hosted by the Library of Congress and jointly sponsored with the National Endowment for the Humanities through the National Digital Newspaper Program (NDNP). Persistent URLs to the original page images on www.loc.gov are retained for every record.

### Corpus composition

| Dimension | Value |
|---|---|
| Total records | 1,535 |
| Unique newspapers | 323 |
| Date range | 1880-01-01 to 1885-12-31 |
| Original articles | 786 |
| Reprints | 749 |
| Used in topic modeling | 1,107 |

### Records by keyword

| Keyword | Count |
|---|---|
| Chinese student | 482 |
| Chinese boy | 289 |
| Chinese children | 265 |
| Chinese girl | 227 |
| Chinese school | 168 |
| Chinese child | 81 |
| Chinese education | 23 |

### Records by region

| Region | Count |
|---|---|
| West | 469 |
| South | 420 |
| Midwest | 394 |
| Northeast | 251 |

### Records by year

| Year | Count |
|---|---|
| 1880 | 164 |
| 1881 | 379 |
| 1882 | 212 |
| 1883 | 200 |
| 1884 | 261 |
| 1885 | 319 |

## Column Descriptions

### Bibliographic metadata

**Keyword**
The search term used to retrieve the page. One of seven values: `Chinese student`, `Chinese boy`, `Chinese girl`, `Chinese child`, `Chinese children`, `Chinese school`, `Chinese education`. Tracking the search term supports analysis of how different queries shape what the corpus contains.

**Date**
Publication date in `YYYY-MM-DD` format.

**Newspaper_Name**
Title of the newspaper as recorded in the Chronicling America database.

**Pub_City**
City of publication.

**Pub_State**
State (or historical territory) of publication.

**Coverage_Region**
Additional geographic references associated with the article or newspaper, separated by vertical bars (e.g., `Richland | Greenville | Columbia`). Captures spatial scope beyond the publication city.

**region_bin**
Normalized Census region derived from publication location: `West`, `South`, `Midwest`, or `Northeast`.

**Image_Number**
The specific page image within the issue (e.g., `Image 7`).

**Page_URL**
Persistent link to the digitized page on the Library of Congress Chronicling America platform.

### Content fields

**OCR_cleaned**
A cleaned excerpt containing the passage relevant to Chinese children or schooling. OCR noise has been reduced and line breaks normalized.

**model_text**
Version of the excerpt used as input to topic modeling. May differ slightly from `OCR_cleaned` due to additional preprocessing.

**token_count**
Approximate word count of the cleaned excerpt.

**relevance_tier**
Manual classification of how directly the page discusses Chinese children, schooling, or related debates. Values: `core` (1,426 records) or `secondary` (109 records).

**topic_tags**
Thematic tags applied during corpus review, separated by vertical bars (e.g., `education|school|student`). Support qualitative filtering and thematic search.

**doc_id**
Unique document identifier within the corpus (format: `DOC_NNNNNN`).

### Deduplication and reprint tracking

Nineteenth-century newspapers frequently reprinted articles from other papers. These fields track duplicated material.

**is_reprint**
Boolean (`true`/`false`). Marks whether this record is a reprinted version of an earlier article.

**is_original**
Boolean. Marks the earliest known appearance of a text within a reprint chain.

**reprint_count**
Total number of records in the same duplicate group, including the original.

**duplicate_group**
Identifier linking records that share substantially similar text (e.g., `REP_0374`). Empty if no duplicate was detected.

**sim_score**
Similarity score used during fuzzy deduplication.

**chain_position**
Position of this record within the reprint chain (1 = earliest).

**propagation_chain**
Ordered list of `doc_id` values in the reprint chain, from original to latest reprint.

**dedup_text**
Normalized lowercase version of the excerpt used during deduplication processing.

**model_text_deduped**
Version of the text used for topic modeling in the deduplicated corpus.

### Topic modeling flags

**use_for_mallet**
Final selection flag for the MALLET input corpus (`yes`/`no`). 1,107 records are marked `yes`.

**mallet_type**
Distinguishes `full` (all-corpus run) from `deduped` (deduplicated run) corpus membership.

**mallet_ready_text**
Final cleaned text passed to MALLET.

**mallet_rank**
Ordering variable used when exporting the MALLET document set.

### Temporal and geographic bins

**month**
Integer month of publication (1–12).

**year_month**
Year and month in `YYYY-MM` format. Used for time-series aggregation.

**time_bin**
Four-digit year as a string. Used for coarser temporal grouping.

## Topic Taxonomy

The following table lists all non-noise topics identified across both model runs (S1: full corpus K25_S1; S2: deduplicated corpus K25_S2), with their thematic categories and discourse labels. Topic IDs correspond to the `topic_id` values used in the spatial map and dataset browser.

### Chinese Educational Mission

| Topic ID | Run | Weight | Discourse Label |
| --- | --- | --- | --- |
| deduped_topic_17 | S2 | 0.2963 | The Hartford Experiment: Government Students and the Politics of Return |
| all_topic_24 | S1 | 0.1328 | The Hartford Experiment: Government Orders, Military Discipline, and the Politics of Return |
| all_topic_14 | S1 | 0.0411 | From Hartford to Shanghai: Friendships, Courtship, and Return |
| all_topic_0 | S1 | 0.0280 | The Prettiest Girl in Class: Intermarriage, Scandal, and the Student Abroad |
| all_topic_17 | S1 | 0.0205 | Sherman, Kensington, and the Threat of Beheading: The Politics of Student Recall |

### Education & Schools

| Topic ID | Run | Weight | Discourse Label |
| --- | --- | --- | --- |
| deduped_topic_7 | S2 | 0.1286 | Teaching English, Making Americans: The Pedagogy of Assimilation |
| deduped_topic_8 | S2 | 0.1284 | "Born on This Soil": The Courtroom Battle over School Access |
| deduped_topic_13 | S2 | 0.1144 | Saving Heathen Girls: Missionary Schooling and Christian Conversion |
| all_topic_3 | S1 | 0.0778 | Teaching English, Making Americans: The Pedagogy of Assimilation |
| all_topic_2 | S1 | 0.0703 | "Born on This Soil": The Courtroom Battle over School Access |
| all_topic_16 | S1 | 0.0789 | Saving Heathen Girls: Missionary Schooling and Christian Conversion |
| all_topic_18 | S1 | 0.0331 | Sabbath Schools and Branch Missions: The Institutional Network |

### Children & Family

| Topic ID | Run | Weight | Discourse Label |
| --- | --- | --- | --- |
| deduped_topic_18 | S2 | 0.2734 | Narrating Chinese Childhood: Domesticity, Gender, and Sentiment |
| all_topic_6 | S1 | 0.1107 | Narrating Chinese Childhood: Domesticity, Gender, and Sentiment |
| deduped_topic_6 | S2 | 0.0218 | Filial Piety and the Rural Chinese Subject |
| all_topic_8 | S1 | 0.0249 | Filial Piety and the Obligations of Kinship |
| all_topic_12 | S1 | 0.0228 | Poor and Peculiar: Poverty, Gender, and the Sympathetic Gaze |

### Law, Politics & Exclusion

| Topic ID | Run | Weight | Discourse Label |
| --- | --- | --- | --- |
| deduped_topic_16 | S2 | 0.0763 | Lost in Translation: Crime, Courts, and the Interpreter Problem |
| deduped_topic_24 | S2 | 0.0594 | Legislating Exclusion: The Chinese Exclusion Act and Congressional Debate |
| all_topic_1 | S1 | 0.0363 | Legislating Exclusion: Treaties and Congressional Debate |
| all_topic_5 | S1 | 0.0238 | Lost in Translation: Formal Proceedings and the Interpreter Problem |
| all_topic_19 | S1 | 0.0564 | The Chinatown Beat: Arrests and Daily Court Proceedings |

### Violence & War

| Topic ID | Run | Weight | Discourse Label |
| --- | --- | --- | --- |
| deduped_topic_22 | S2 | 0.0426 | Torches and Mobs: Arson, Riot, and Racial Expulsion |
| deduped_topic_20 | S2 | 0.0336 | Imperial Rivalries: The Sino-French War in the American Press |
| all_topic_10 | S1 | 0.0266 | Torches and Mobs: Arson, Riot, and Racial Expulsion |

### Commerce & Material Culture

| Topic ID | Run | Weight | Discourse Label |
| --- | --- | --- | --- |
| deduped_topic_21 | S2 | 0.0201 | Consuming the Orient: Chinoiserie and Holiday Commerce |
| deduped_topic_14 | S2 | 0.0327 | The Oriental Parlor: Domesticity, Hospitality, and Curiosity |
| deduped_topic_10 | S2 | 0.0385 | Marking Difference: Bodies, Dress, and the Oriental Type |
| all_topic_23 | S1 | 0.0200 | Consuming the Orient: Chinoiserie and Holiday Commerce |
| all_topic_21 | S1 | 0.0249 | Silk and Silver: Commodifying the Oriental Domestic |

### Daily Life & Urban Space

| Topic ID | Run | Weight | Discourse Label |
| --- | --- | --- | --- |
| deduped_topic_9 | S2 | 0.1926 | The Chinatown Beat: Everyday News Coverage |
| deduped_topic_23 | S2 | 0.0375 | Inside Chinatown: Death, Darkness, and Sensory Reportage |
| deduped_topic_0 | S2 | 0.0322 | Hired Hands: Chinese Domestic Labor and Wage Relations |
| all_topic_22 | S1 | 0.0172 | Hired Hands: Chinese Domestic Labor and Wage Relations |

### Land, Migration & Labor

| Topic ID | Run | Weight | Discourse Label |
| --- | --- | --- | --- |
| deduped_topic_15 | S2 | 0.0694 | Pacific Crossings: Hawaii, Steamships, and Transpacific Migration Control |
| deduped_topic_11 | S2 | 0.0151 | Chinese Agricultural Labor in the American West |
| all_topic_11 | S1 | 0.0794 | Pacific Crossings: Hawaii, Steamships, and Transpacific Migration Control |

### Culture, Perception & Acculturation

| Topic ID | Run | Weight | Discourse Label |
| --- | --- | --- | --- |
| deduped_topic_4 | S2 | 0.0192 | The "Chinese Question" on Stage: Public Spectacle and Reform Rhetoric |
| deduped_topic_12 | S2 | 0.0232 | Opium Dens and Degraded Subjects: The Vice Narrative |
| all_topic_20 | S1 | 0.0166 | Shaved Heads and Sprouts: The Exotic Body on Display |
| all_topic_15 | S1 | 0.0149 | The Preacher and the Mosquito: Everyday Struggles of Acculturation |

### Diplomacy

| Topic ID | Run | Weight | Discourse Label |
| --- | --- | --- | --- |
| all_topic_9 | S1 | 0.0464 | The Minister's Daughter: Chinese Children in Diplomatic Settings |


## Example Record

| Field | Value |
|---|---|
| doc_id | DOC_000606 |
| Date | 1885-05-28 |
| Newspaper_Name | Baptist Courier |
| Pub_City | Greenville |
| Pub_State | South Carolina |
| region_bin | South |
| Keyword | Chinese girl |
| relevance_tier | core |
| topic_tags | child\|children\|general_chinese_reference\|language\|school |
| is_reprint | false |
| reprint_count | 1 |
| token_count | 312 |
| Page_URL | [↗ Chronicling America](https://www.loc.gov/resource/sn92073907/1885-05-28/ed-1/?sp=1) |

**Excerpt:**
> Dear Children: As you have shown your interest in missions in so many ways, and especially in supporting a missionary in China, I thought a letter from one who, just a few years ago, was where you are now — in a South Carolina school — might be interesting to you. My first chapter will describe a Chinese school. As it is a Chinese school, of course they study the Chinese language…
