---
title: Map Overview
---

# Map Overview

<a href="./interactive" class="map-launch-card">
  <span class="map-launch-icon">◎</span>
  <span class="map-launch-body">
    <span class="map-launch-title">Open the Spatial Map</span>
    <span class="map-launch-desc">Full-screen map · topic filters · historical events · time playback</span>
  </span>
  <span class="map-launch-arrow">→</span>
</a>

::: warning WebGL Required
The map renderer depends on WebGL. If the map fails to load, check that hardware acceleration is enabled in your browser settings (Chrome: *Settings → System → Use hardware acceleration*; Firefox: open `about:config`, search for `webgl.disabled`, and set it to `false`). Some browser extensions that block canvas access may also prevent the map from rendering correctly.
:::

## How to Use the Map

### Navigating

Pan by clicking and dragging. Zoom with the scroll wheel or trackpad. On mobile, use pinch-to-zoom. The map supports switching between a **modern base layer** and a period **Rand McNally** layer from the sidebar controls.

::: tip
Switching to the **Rand McNally** layer gives a sense of how contemporaries understood the geography, county names and railroad routes as they appeared in 1882 press atlases.
:::

### Clicking Points

Click any dot to open a record popup showing the newspaper name, publication city, date, topic label, and an excerpt from the original article. Reprinted articles (the same text appearing in multiple papers) are marked with a reprint count.

::: info
A high reprint count is a strong signal of editorial salience: the story circulated through wire services and was considered worth republishing across the country. Filter by topic and zoom out to see how a single article's footprint can span dozens of cities.
:::

### Filtering by Topic

The **Topics panel** (left or bottom depending on screen size) lists all topic categories. Toggle a category on or off using its switch. Click a category name to enter *solo mode*, which hides all other categories and lets you focus on a single theme. Within each category, expand the topic list to see individual topics and their relative weight in the corpus, shown as a small bar beside each label. Click a topic row to filter down to that single topic.

### Filtering by Time

Use the **Date filter** to restrict visible records to a single month. This is useful for tracing how coverage shifted around specific events, such as the passage of the Exclusion Act in May 1882 or the Rock Springs Massacre in September 1885.

::: tip
For the sharpest geographic contrast, combine the time filter with a single topic category. Try **Law, Politics & Exclusion** filtered to May 1882, then compare it with **Violence & War** in September 1885. The shift in regional emphasis is immediately visible.
:::

### Historical Events

The **Events panel** provides a curated list of key historical moments during the 1880–1885 period. Selecting an event:

- Highlights the relevant state or county on the map with a color overlay
- Filters the record layer to the event's associated date range
- Opens a card anchored to the geographic location with a description of the event

## Topic Categories

The corpus is organized into nine thematic categories derived from LDA topic modeling. Each dot on the map is colored by its assigned category:

- Chinese Educational Mission
- Education & Schools
- Children & Family
- Law, Politics & Exclusion
- Violence & War
- Commerce & Material Culture
- Daily Life & Urban Space
- Land, Migration & Labor
- Culture, Perception & Acculturation

For full descriptions of each category and the modeling methodology, see [Analytical Methods](/methodology/analytical-methods#topic-labeling-and-categorization).

## Historical Events on the Map

The map includes ten anchored events that serve as navigational waypoints through the period.

| Event | Date | Location |
|---|---|---|
| Angell Treaty Signed | Nov 1880 | (global) |
| Chinese New Year Press Coverage Wave | Jan 1881 | San Francisco, New York, Boston |
| Chinese Educational Mission Recall Begins | Jun 1881 | Hartford / Springfield area |
| Chinese Exclusion Act Signed | May 1882 | San Francisco |
| First CEM Student Graduates from Yale | Jun 1883 | New Haven, CT |
| *Tape v. Hurley* School Desegregation Case | Sep 1884 | San Francisco |
| Sino-French War, Battle of Fuzhou | Aug 1884 | (global) |
| Rock Springs Massacre | Sep 1885 | Sweetwater County, WY |
| Tacoma Expulsion | Nov 1885 | Pierce County, WA |
| Seattle Expulsion Attempt | Feb 1886 | King County, WA |

Each event is linked to one or more topic categories and filtered to the months of its most intense press coverage.

::: info
Selecting an event automatically updates the time filter and topic filter together, so you can immediately browse the records most relevant to that moment. Deselect the event to return to your previous filter state. Clicking the year number on the timeline filters the map to show only records from that year.
:::


## Data Sources

**Newspaper records:** Chronicling America digital archive, Library of Congress. Retrieved via keyword searches for terms including *Chinese student*, *Chinese children*, *Chinese school*, and *Chinese education*. Approximately 2,100 excerpts cover the period January 1880 to December 1885.

**Historical boundaries:** Atlas of Historical County Boundaries, Newberry Library (2012 edition). County and state shapefiles representing administrative divisions as of 1882.

**Topic model:** MALLET LDA, run on cleaned and excerpt-filtered text. Categories and topic assignments were reviewed and refined through iterative close reading.

::: info
Topic labels are interpretive, not algorithmic. LDA produces probability distributions over words; the category names and topic groupings reflect the researcher's judgment after multiple rounds of close reading. Treat them as analytical lenses rather than ground-truth classifications.
:::

Full citations for all data sources, basemaps, text processing libraries, geospatial tools, and frontend dependencies are collected in [Map References](/map/references).

## Key Observations

Coverage is geographically uneven in ways that reflect both population distribution and political salience. **San Francisco** dominates the record count, as the city was home to the largest Chinese community in the United States and was the site of the most contentious legal and political battles over Chinese children's rights. **New York**, **Chicago**, and several New England cities contribute a substantial share of Chinese Educational Mission coverage, reflecting the regional concentration of CEM student placements in Connecticut and Massachusetts.

**Western states and territories** show higher proportions of law-and-exclusion and violence-related records, particularly in the months around the Exclusion Act and the 1885 anti-Chinese expulsions. **Eastern papers** are more likely to engage with the CEM and with education debates in a tone that, while not necessarily sympathetic, tends toward curiosity rather than outright hostility.

The volume of press attention peaks sharply in **spring 1882** (the Exclusion Act debate) and again in **fall 1885** (Rock Springs and the expulsion wave), with a secondary peak during the **CEM recall** in mid-1881. Outside these moments, coverage is steady but lower, comprising city-beat reporting, school-admission disputes, and missionary school notices.
