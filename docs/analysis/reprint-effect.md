---
title: The Reprint Effect
---

# The Reprint Effect
***How the Newspaper Network Reshaped What Readers Saw***

## Two corpora, two different stories

The deduplicated corpus described in the previous chapter (1,100 articles representing what individual journalists originally wrote) is only half the story. American newspapers in the 1880s did not just write; they copied. A single paragraph composed in a New York or San Francisco office could, within weeks, be set in type by dozens of small-town editors who had never seen the original event and who chose the item because it filled column inches or because it confirmed something they already believed.

To capture this, I built a second corpus: the **full corpus of 1,525 articles**, including all reprints. By comparing topic prominence in the deduplicated corpus (what was *written*) against the full corpus (what was *circulated*), we can see how the reprinting network amplified some themes and compressed others. The system did not redistribute attention neutrally. It had preferences.

## The shape of the reprint effect

This dumbbell chart compares each topic's mean weight across the two corpora: the blue marker shows the deduplicated weight (what was written), and the red marker shows the all-corpus weight (what was circulated).

<DatawrapperChart chartId="yVyRe" :minHeight="879" alt="The Reprint Effect: How Reprinting Reshapes Topic Prominence" />

The connecting bar for each topic reveals the magnitude and direction of the reprint effect.

Several patterns are immediately visible. **Chinese Educational Mission** appears only on the right side: its sub-topics dominate the all-corpus view because the deduplicated baseline split CEM into a single merged topic (18.1%) while the all-corpus view broke it into four narrower sub-topics, the largest being *CEM: Government Policy & Institutional Recall* at 13.8%. The recall story was, in raw terms, the single most reprinted thread of the period.

**Children & Family Life** drops sharply, from 12.5% in the deduplicated corpus to 7.7% in the full corpus. Family stories were written often but reprinted rarely. They were locally interesting filler, not network-level news.

**Public School Admission** moves the opposite direction: from 7.7% written to 9.1% circulated. This is the *Tape v. Hurley* effect: when the California Supreme Court ruled in January 1885 that Chinese children born in the United States were entitled to attend public schools, that single item traveled across the wire in many forms. Stories about *Hawaii & Pacific Migration* show a similar amplification (3.4% to 5.5%): regulatory news from the Hawaiian Kingdom, often issued through the State Department, was also a wire-friendly format.

**Routine Press Reporting** appears as a single blue dot at 9.0%; it exists only in the deduplicated corpus. This is because the topic captures generic press boilerplate that, by definition, does not survive deduplication; once any version is kept, the others vanish.

## A clearer ranking

The bar chart below ranks the same comparison more starkly, showing the percentage-point gain or loss for each topic.

<DatawrapperChart chartId="kuXNx" :minHeight="555" alt="Topic Differences Between Original and Reprinted Articles" />

The picture sorts into two distinct groups.

On the left (blue, gaining through reprints): **Public School Admission** (+7.72), **Diplomacy & Ceremonial Events** (+4.41), **Mission School Directories & Schedules** (+4.19), **CEM: Students & Cross-Cultural Marriage** (+4.06), **Physical Appearance & Curiosity Narratives** (+3.17). What unites these? They are short, novelty-driven, easily detached from local context. A Supreme Court ruling, a diplomatic ceremony, a school schedule, a marriage scandal, a curious physical description: these are paragraph-length items that travel well.

On the right (red, losing in reprints): **Missionary & Church Schools** (–6.38), **Criminal Cases & Court Proceedings (Police)** (–4.65), **Children & Family Life** (–4.09), **Hawaii & Pacific Migration** (–3.17), **Exclusion Legislation** (–1.74). What unites these? They are longer-form, more locally embedded, or more ideologically demanding pieces: the kind of writing that a busy editor of a small-town weekly would not bother to copy out.

The pattern is clear. The reprinting network favored short, sharp, novelty-driven items over reflective or deeply local ones. Stories with a single arresting detail (a courtroom decision, a banquet, a recalled student) propagated faster than stories that required sustained engagement.

## Presence is not the same as propagation

This bubble chart plots each thematic category against two axes: total articles in the corpus (presence, horizontal) and average number of reprints per article (propagation, vertical).

<DatawrapperChart chartId="8tn4R" :minHeight="553" alt="Presence vs. Propagation" />

Most categories cluster in the lower-left corner: low presence, low propagation. **Education & Schools** stands alone in the lower-right: very high presence (~470 articles) but modest reprint count per article (~9.5). It was a constantly-discussed but locally-handled topic: many editors wrote their own school stories rather than copying others.

Two categories occupy the upper region of the chart. **Diplomacy** sits at the upper-middle (8.4 reprints per article on ~75 articles): moderate presence, high propagation. Diplomatic news was wire-service material par excellence. **Culture, Perception & Acculturation** sits at the very top (16+ reprints per article on a small base of ~60 articles). This is the most striking finding in the chart: cultural-curiosity pieces (descriptions of physical appearance, language-learning anecdotes, items about exotic customs) were reprinted, on average, more than three times as often as anything else. They were small, they were vivid, and they confirmed a worldview without requiring any new information from the editor.

The implication for cultural history is uncomfortable. Stories that exoticized Chinese bodies and customs traveled the furthest through the American press, even when they were the smallest part of what was originally written.

## Before and after the reprinting network

The two donuts below visualize the cumulative effect at the category level: the left is the deduplicated corpus (1,100 articles, what journalists originally wrote), the right is the full corpus (1,525 articles, what readers actually encountered).

<DatawrapperChart chartId="jF7lr" :minHeight="561" alt="Discourse Before and After Reprinting" />

Several shifts deserve attention:

**Chinese Educational Mission** grows from 18.1% to 23.5%. The Hartford recall story was already large; reprinting made it dominant.

**Education & Schools** grows from 21.4% to 26.0%. Combined with CEM, education-themed coverage rose from 39.5% to 49.5% of all circulating discourse, half of everything readers encountered.

**Daily Life & Urban Space** collapses from 13.4% to 2.3%. This is the most dramatic compression in the chart. Stories about Chinatown, domestic employment, and routine police-court reporting were written abundantly but reprinted almost not at all. They were, by the structure of the network, local.

**Violence & War** halves, from 5.0% to 2.5%. Even the Rock Springs and Foochow stories did not propagate as widely as the per-article reprint patterns of cultural-curiosity items. Violence was discussed where it happened and in the major dailies; smaller papers picked up the scandal less often than they picked up a tidy school-court ruling.

**Law, Politics & Exclusion** rises modestly, from 8.6% to 10.1%. Legislative news propagated, but not dramatically.

The total share captured by the named categories rises from 93.2% to 95.1%, meaning the reprinting network did not introduce significant new themes. It simply re-weighted the ones that were already there.

## Tracing the flow between the two corpora

The Sankey diagram below traces every category from the deduplicated corpus (left) to the all-corpus distribution (right), with band width proportional to article count. The "New (reprints)" node accounts for the 425 articles that entered circulation purely through reprinting.

![Discourse flow between corpora](/data/5C_Discourse_Flow_Between_Corpora.svg)

Several patterns become legible in this view that the donuts and bar charts could only hint at.

The two largest internal flows are Education & Schools → Education & Schools (209 articles) and Chinese Educational Mission → Chinese Educational Mission (189 articles). These represent the stable core of the discourse, articles whose category did not change between the deduplicated and full corpora. Together they account for nearly 400 articles flowing along their original thematic channel.

The grey bands extending from the "New (reprints)" node show where the 425 reprint-only articles went. The largest two grey bands flow into Education & Schools (153 reprints) and Chinese Educational Mission (126 reprints). Reprinting did not add new categories so much as it dramatically reinforced the two that were already largest. A smaller but striking grey flow goes to Diplomacy (43 reprints); diplomatic news, as we saw in the propagation chart, was wire-friendly content that gained heavily from the reprinting network.

The diagram also makes visible something the donuts hide: the cross-category flows. Some articles that registered as one category in the deduplicated corpus shifted into another category when reprinted. Daily Life & Urban Space sends 33 articles into Children & Family, 27 into Law, Politics & Exclusion and only 18 into its original category. This is the structural reason for Daily Life & Urban Space's collapse from 13.4% to 2.3% in the donut comparison: most articles classified as Daily Life in the deduplicated corpus were not reprinted at all, and the few that were got absorbed into adjacent categories with stronger reprint pull.

The Children & Family → Education & Schools flow (34 articles) is small but interesting. It captures a specific kind of article (about Chinese children at school) that the model could place in either category depending on which features (family, gender, schooling) it weighted in a given document.

What this diagram makes clearest of all is the asymmetry of growth. Education & Schools grows from 275 (deduped) to 470 (all), a gain of 195 articles. Chinese Educational Mission grows from 223 to 370, a gain of 147. By contrast, Daily Life & Urban Space shrinks from 147 to 41, and Violence & War shrinks from 61 to 38. The reprinting network pumped articles into the top of the distribution and drained them from the bottom.

## What the network preferred: examples

To make these patterns concrete, consider how individual stories actually behaved in the network.

The Tape v. Hurley decision generated short, copy-friendly reports like this one: "The Chinese Must Go — to School. Superior Judge Maguire decided today, in the case of Mamie Tape, a Chinese girl ten years of age, against Mrs. Jennie M. Hurley, principal of a public school of this city, that Chinese children born in this country are entitled to admission to the public schools."[^1]

<div class="clip-spread">
<figure class="clip">
<img src="/clips/wheeling-tape-1885.jpg" alt="Newspaper clipping: The Chinese Must Go — to School, The Wheeling Daily Intelligencer, January 10, 1885, page 1">
<figcaption>"The Chinese Must Go — to School," <em>The Wheeling Daily Intelligencer</em>, Jan. 10, 1885 (p. 1)</figcaption>
</figure>

<figure class="clip">
<img src="/clips/wheeling-tape-1885-2.jpg" alt="Newspaper clipping: The Chinese Must Go — to School, The Wheeling Daily Intelligencer, January 10, 1885, page 2">
<figcaption>"The Chinese Must Go — to School," <em>The Wheeling Daily Intelligencer</em>, Jan. 10, 1885 (p. 2)</figcaption>
</figure>
</div>

Compact, dramatic, headline-ready: this was exactly the kind of paragraph that small-town editors clipped and reset. Public School Admission's +7.72 percentage-point gain in the reprint chart is built from items like this one.

Diplomatic stories propagated for similar reasons. The story of the Chinese minister's daughter (quoted in the previous chapter) was circulated under multiple headlines because it had a single charming hook (the first Chinese child born in Washington) that any editor could place above the fold without further work.

By contrast, consider the kind of writing that the network suppressed. Missionary schools generated lengthy descriptive pieces grounded in specific local institutions, like this report from Charleston: "$280 was paid for seven Chinese scholarships, including Nandy Maria Wightman, supported by Trinity Sunday-school; Virginia Walker, by Mr. Walker's Bethel Clem; Trinity Sunday school."[^2]

Items like this (institutional, local, full of names that meant nothing outside their own community) almost never traveled. Missionary & Church Schools fell by 6.38 percentage points in the reprint comparison, the largest single drop in the corpus.

The disparity between Anti-Chinese Violence as a category (only +0.3 between the two corpora) and the magnitude of the events involved is also telling. Coverage of the Rock Springs massacre included sober, locally-detailed eyewitness accounts that did not propagate well. One example: "I stepped out of my house with my wife, and saw the first two houses that were set on fire. While we were standing there I could see a number of white men on the north end of Chinatown, and at the same time four Chinamen came out of a house on the southeast part of the town… The firing then commenced."[^3]

This is an extended testimony, not a wire paragraph. It was reprinted in some Western papers but rarely beyond. The horror was real; the format was difficult.

The reprinted versions of Rock Springs that did circulate widely tended to be the brief sworn-affidavit summaries, short enough to fit a column, dramatic enough to retain interest. One representative reprint: "Rock Springs, Wy., Oct. 5. — A report of a startling character is given to the grand jury today. Rev. Timothy Thirlow, a Congregational minister who resided at Rock Springs with his family during the riot, made a sworn statement showing that the Chinese set fire to their own houses in order to prevent white men from robbing them of their money."[^4]

Note how the text strips the eyewitness narrative down to a single arresting claim. The network amplified the version that fit the format.

Curiosity items propagated at extraordinary rates. The story of the Portland Chinese baby's head-shaving banquet appeared in dozens of papers in late 1884 and early 1885 in nearly identical form, often shortened to a paragraph. So did the foot-binding description: "The Chinese children undergo various stages of torture, commencing at the age of two years. First, the four toes are forced under the ball of the foot and bound in that position until they lose their articulation… The second part of the operation is a torture so terrible that sometimes the child dies under it."[^5]

<figure class="clip">
<img src="/clips/republican-footbinding-1881.jpg" alt="Newspaper clipping: How Chinese Feet Are Bound, The Republican, December 17, 1881">
<figcaption>"How Chinese Feet Are Bound," <em>The Republican</em>, Dec. 17, 1881</figcaption>
</figure>

The text is sensational, compact, and demands no follow-up reporting, a perfect specimen of what the reprint network amplified.

## Two corpora, two histories

The contrast between deduplicated and full corpora is more than a methodological detail. It is an argument about how the press worked as a system. Individual journalists, in cities and small towns, produced a relatively diverse body of writing about Chinese children, including substantial coverage of family life, missionary work, and local urban routines. The network through which these articles traveled, however, applied its own filter, favoring brevity, novelty, courtroom drama, diplomatic ceremony, and ethnographic curiosity.

When we read 1880s American newspapers today, we read what the network selected, not what individual reporters wrote. Topic modeling lets us see both layers separately, and the difference between them is part of the historical record.

The third chapter looks more closely at the largest of these themes: education itself, and how four distinct sub-discourses about Chinese children's schooling shifted across the period and across regions of the United States.

## Notes

[^1]: "The Chinese Must Go — to School," *The Wheeling Daily Intelligencer*, January 10, 1885, https://www.loc.gov/resource/sn84026844/1885-01-10/ed-1/?sp=1.
[^2]: *Southern Christian Advocate*, April 26, 1884, https://www.loc.gov/resource/sn87065702/1884-04-26/ed-1/?sp=3.
[^3]: "Restricting Chinese Immigration," *Helena Weekly Herald*, October 8, 1885, https://www.loc.gov/resource/sn84036143/1885-10-08/ed-1/?sp=3.
[^4]: "The Chinese War," *Daily Republican*, October 6, 1885, https://www.loc.gov/resource/sn84038114/1885-10-06/ed-1/?sp=4.
[^5]: "Suffering to be Beautiful," *The Republican*, December 17, 1881, https://www.loc.gov/resource/sn88065202/1881-12-17/ed-1/?sp=6.