---
title: Mapping the Discourse
---

# Mapping the Discourse
***What American Newspapers Wrote About Chinese Children, 1880–1885***

## Why topic modeling, and why this corpus

Between 1880 and 1885, American newspapers printed thousands of stories that mentioned Chinese children, students, boys, girls, and schools. Some of these stories were front-page political controversies. Many more were short paragraphs buried in the middle of a page, sandwiched between farm prices and theater notices. Reading them one by one would tell us what individual editors chose to print. But to see the *pattern* (what the press as a whole was talking about when it talked about Chinese children), we need a different kind of reading.

This study uses MALLET LDA topic modeling (K = 25, 10,000 iterations) on a corpus of 1,100 deduplicated articles drawn from the Library of Congress *Chronicling America* archive. The articles were retrieved using seven keyword queries: "Chinese student," "Chinese boy," "Chinese girl," "Chinese child," "Chinese children," "Chinese school," and "Chinese education." After removing OCR noise, advertising boilerplate, and three "junk" topics, the model surfaced **22 substantive topics**, which we grouped into **10 thematic categories**.

The result is a map. Not a perfect one (topic models never produce clean categories, and every label involves interpretive choices), but a map detailed enough to show which themes dominated the discourse, which sat at the margins, and how the seven search keywords pulled the conversation in very different directions.

## The thematic landscape

The scatter plot below places every article in the corpus on a single canvas, with publication year on the horizontal axis and topic category on the vertical. Each dot is one article.

::: tip
Click any dot to open a popup with the article's metadata. The popup includes a link to the original digitized page on the Library of Congress *Chronicling America* website.
:::

<DatawrapperChart chartId="Z2sCy" :minHeight="746" alt="Thematic Landscape of Chinese Children Coverage, 1880–1885" />

The picture that emerges is not balanced.

Three categories form thick horizontal bands across the entire 1880–1885 period: **Chinese Educational Mission**, **Education & Schools**, and **Children & Family**. These are the topics that journalists returned to month after month. Below them, **Law, Politics & Exclusion** appears as a steady but thinner stream. **Violence & War**, by contrast, is almost invisible in 1880 and 1881, then suddenly clusters in late 1884 and especially 1885, the visual signature of the Sino-French War's Foochow naval battle and the Rock Springs massacre.

The lower half of the chart shows much sparser dots: **Commerce & Material Culture**, **Daily Life & Urban Space**, **Land, Migration & Labor**, and **Culture, Perception & Acculturation**. These weren't absent themes, but they were minor ones. When American papers wrote about Chinese children, they were overwhelmingly writing about students, schools, and family scenes, with politics and violence as recurring secondary concerns.

## How prominent was each topic?

Counting the number of articles in which each topic has the highest weight gives us a more concrete sense of scale.

::: tip
Click any dot to open a popup with the article's metadata. The popup includes a link to the original digitized page on the Library of Congress *Chronicling America* website.
:::

<DatawrapperChart chartId="9StG6" :minHeight="743" alt="Topical Distribution of Chinese Children Coverage, 1880–1885" />

**Education & Schools** is the single largest category (408 articles), narrowly ahead of **Chinese Educational Mission** (356 articles). Together, these two education-centered categories account for 64% of the corpus.

The internal composition of each bar is also revealing. Chinese Educational Mission breaks down into four sub-topics, dominated by *CEM: Government Policy & Institutional Recall* (60% of CEM articles, 213 documents). This single sub-topic is by itself the largest theme in the entire corpus, a direct reflection of the 1881 recall of the Hartford students, which generated a sustained press storm. Education & Schools splits more evenly across *Public School Admission* (38%), *Missionary & Church Schools* (30%), and *Classroom Instruction* (18%), suggesting a more diffuse conversation about Chinese children's schooling.

Smaller categories like **Violence & War** (36 articles), **Daily Life & Urban Space** (38), and **Diplomacy** (79) each consist of a single dominant topic. **Commerce & Material Culture** is unique in splitting evenly (50/50) between *Trade in Chinese Goods* and *East Asian Consumer Goods*: the model is detecting two distinct registers of consumer-oriented writing.

## A view from above: the corpus by category

The two donuts below compare the deduplicated corpus (what journalists wrote) against the full corpus (what readers encountered), showing the overall composition of the discourse at the category level.

<DatawrapperChart chartId="WdUwZ" :minHeight="592" alt="Corpus Composition by Topic Category" />

The four largest slices of the deduplicated corpus are Education & Schools (21.4%), Chinese Educational Mission (18.1%), Children & Family (13.8%), and Daily Life & Urban Space (13.4%). Together they fill more than two-thirds of the available discourse.

What is striking is how much smaller the other slices are. Violence & War occupies only 5.0% of the deduplicated corpus. Law, Politics & Exclusion (the category that historians often place at the center of 1880s Chinese-American history) accounts for only 8.6%. The Chinese Exclusion Act passed in May 1882, but in this keyword-driven corpus about Chinese children specifically, the law itself is a relatively small share of the conversation. Children appear more often as students than as legal subjects.

We will return to the right-hand donut in the next chapter, when we examine how reprinting reshaped these proportions.

## The discourse held remarkably steady

One way to measure whether the press's attention was concentrated or dispersed is to compute the Shannon entropy of the topic distribution each month: higher values mean coverage spread across many topics, lower values mean it narrowed onto a few.

<DatawrapperChart chartId="vnA97" :minHeight="462" alt="Discourse Diversity in Chinese Children Coverage" />

The entropy line hovers between 1.1 and 1.5 for almost the entire 1880–1885 window. There are small dips and small spikes (the spike around late 1880 corresponds to early CEM coverage, and the modest peak in mid-1882 falls near the passage of the Exclusion Act), but no dramatic collapse. The press maintained a fairly diverse menu of topics about Chinese children even when major events were unfolding. The system absorbed shocks rather than collapsing onto them.

This matters for interpretation. It means the dominance of education-themed coverage was not the artifact of one or two big news cycles. Education was a *steady* preoccupation. Even in October 1885, the month of the Rock Springs massacre, the entropy line dips only slightly. Violence intruded; it did not take over.

## Search terms shape what we see

This heatmap aggregates the topic categories down to seven rows, one per search keyword, showing how the choice of search term shaped the resulting discourse.

<DatawrapperChart chartId="fc3Oh" :minHeight="801" alt="Search Terms and Thematic Categories" />

The pattern of bright cells reveals something important about how the corpus was assembled, and about what each search term actually captured.

The keyword **"Chinese student" (n=339)** loads heavily on Chinese Educational Mission (42.78). This makes sense: in 1880s American usage, the word "student" attached to "Chinese" almost automatically pointed at the Hartford mission. The keyword **"Chinese school" (n=108)** loads on Education & Schools (37.72), and **"Chinese children" (n=177)** loads on the same category (32.98): schools dominate when schools are the search target.

But the keyword **"Chinese child" (singular, n=52)** behaves very differently. Its highest cell is *Children & Family* (27.07), and Education & Schools comes second (17.90). The shift from plural to singular drags the discourse from the institutional register of schools into the domestic register of family. Singular "child" appears in stories about specific children (the minister's daughter, the laundryman's son, the kidnapped girl) far more often than in coverage of school enrollments.

The keyword **"Chinese boy" (n=221)** is the only one with substantial weight on Violence & War (11.38). Why? Because "boy" was the term used in stories about laborers and victims, including the Rock Springs survivors. The grammar of "boy" in 1880s American English was racialized in ways "student" was not.

This dependency of topic on keyword is not a methodological problem to be eliminated. It is a finding. The vocabulary editors used to refer to Chinese young people was itself organized by social position: students were in the schools, boys were in the laundries and the mining camps, children appeared in the family scene.

## What we can illustrate: a few representative articles

Topic modeling produces statistical signatures. To make those signatures concrete, here are short examples drawn from the highest-probability documents in several of the major topics.

The Children & Family Life topic surfaces articles like the following meditation on Chinese marriage customs: "In China, parents, with the help of a 'go-between,' select husbands and wives for their children, and the parties often never see each other until the wedding is over. After marriage, instead of a wedding trip, the bride is shut up as a prisoner in her husband's home and does not go out for a month."[^1]

<figure class="clip">
<img src="/clips/dawson-marriage-1883.jpg" alt="Newspaper clipping: Chinese Marriage Customs, The Dawson Journal, April 12, 1883">
<figcaption>"Chinese Marriage Customs," <em>The Dawson Journal</em>, Apr. 12, 1883</figcaption>
</figure>

The story is presented as ethnographic curiosity, but the children who appear in it are the future subjects of arranged marriages, offering a window into how American papers framed Chinese childhood as fundamentally unlike American childhood.

The Confucian Family Ethics topic surfaces a piece quoting from a returned CEM student's letter: "I went home to see my relations the last of March. When I first reached home you can imagine how glad my father and relatives were to see me looking so well and robust. They all flocked around me and asked me many questions."[^2]

<figure class="clip">
<img src="/clips/evening-star-student-1882.jpg" alt="Newspaper clipping: A Letter from a Returned Chinese Student, Evening Star, November 23, 1882">
<figcaption>"A Letter from a Returned Chinese Student," <em>Evening Star</em>, Nov. 23, 1882</figcaption>
</figure>

Notice how the same text could plausibly belong to either the family-ethics topic or the CEM topic: the model places it with family ethics because of words like *father*, *relations*, *home*. This blurring is real, and it is part of how the discourse worked: the recalled students were being *rewritten* into a Confucian family frame as soon as they returned.

The Diplomacy & Ceremonial Events topic includes one of the most charming small items in the corpus: "The Chinese minister recently celebrated the event of his little daughter reaching the age of four years, according to a Chinese custom, by a dinner served in American style. Covers were laid for twelve, and all those at the Chinese legation in Washington were present and toasted the youthful heroine. Miss Mi Ju is the first Chinese child born in Washington."[^3]

<figure class="clip">
<img src="/clips/morris-minister-1884.jpg" alt="Newspaper clipping: The Chinese Minister's Daughter, Morris Tribune, January 23, 1884">
<figcaption>"The Chinese Minister's Daughter," <em>Morris Tribune</em>, Jan. 23, 1884</figcaption>
</figure>

The diplomatic frame allowed Chinese children to appear as objects of celebration rather than concern, a register almost completely absent from coverage of Chinese laboring children.

Finally, the Physical Appearance & Curiosity Narratives topic captures stories like this one about a Portland merchant: "At Portland, Ore., recently, Ding Wing, a Chinese merchant, entertained a number of his brother merchants at a costly and elaborate banquet. The occasion was the shaving of the head of the infant son of Ding Wing, who was a month old the day before. When a Chinese boy is one month old his head is shaved and a bladder drawn over it."[^4]

<figure class="clip">
<img src="/clips/hand-county-baptism-1884.jpg" alt="Newspaper clipping: A Chinese Baptism, Hand County Press, November 20, 1884">
<figcaption>"A Chinese Baptism," <em>Hand County Press</em>, Nov. 20, 1884</figcaption>
</figure>

Such items treat Chinese childhood ritual as exotic spectacle, the body of the infant becoming an object of the curious gaze.

## What the map tells us

Reading these patterns together produces a tentative answer to the question: what did American newspapers between 1880 and 1885 talk about when they talked about Chinese children?

They talked about education, far more than about anything else. Within education, they talked about three things: the Hartford government students and their recall, the question of whether Chinese children could attend American public schools, and the missionary schools that were teaching English and Christianity to Chinese girls and boys. They talked about family in a culturally distancing register, foregrounding arranged marriage, foot-binding, female infanticide, and filial piety. They talked about politics and law, but less than we might expect given the period. They talked about violence only when violence forced its way onto the page: at Foochow in 1884, at Rock Springs in 1885.

The map shows where the press's attention was, but it does not yet show what readers in small-town newspapers actually encountered, or how the reprinting network amplified some of these themes and quietly suppressed others. That is the subject of the next chapter.

## Notes

[^1]: Selah Brown, "Chinese and Americans: A Chapter of Contrarities," *The Dawson Journal*, April 12, 1883, https://www.loc.gov/resource/sn89053287/1883-04-12/ed-1/?sp=4.
[^2]: "Marriage in China," *Evening Star*, November 23, 1882, https://www.loc.gov/resource/sn83045462/1882-11-23/ed-1/?sp=6.
[^3]: "Miss Mi Ju," *Morris Tribune*, January 23, 1884, https://www.loc.gov/resource/sn91059394/1884-01-23/ed-1/?sp=4.
[^4]: *Hand County Press*, November 20, 1884, https://www.loc.gov/resource/sn98062948/1884-11-20/ed-1/?sp=3.