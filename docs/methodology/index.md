---
title: Methodology
---

# Methodology

The project pipeline moves from raw archival text to structured data to computational analysis to visualization in two main stages.

**Dataset construction** transforms raw *Chronicling America* OCR into a clean, structured, geographically annotated corpus of 1,535 records. This involves geographic metadata standardization, multi-layer OCR cleaning, and passage extraction to isolate China-related content from full newspaper pages.

**Analytical methods** covers topic modeling with MALLET, the construction of Datawrapper charts, and the interactive spatial map. Two parallel LDA models (deduplicated corpus of 1,100 documents and full corpus of 1,525 documents) were trained at K = 25 and compared to trace how the nineteenth-century reprinting network reshaped discourse.

## In this section

- [Dataset Construction](./dataset-construction): corpus assembly, geographic standardization, OCR cleaning, excerpt extraction
- [Analytical Methods](./analytical-methods): MALLET topic modeling, Datawrapper chart preparation
- [Map Construction](./map-construction): historical boundary data, geographic resolution, topic assignment, event overlays
