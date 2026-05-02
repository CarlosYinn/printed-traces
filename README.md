<p align="center">
  <img src="docs/public/printed-traces.svg" alt="Printed Traces" width="400" />
</p>

<p align="center"><strong>Chinese Immigrant Children in the U.S. Press, 1880–1885</strong></p>

A digital humanities project that combines close historical analysis with corpus-based methods to study how Chinese children were represented in American newspapers during the Chinese exclusion era. The site brings together topic modeling, geographic visualization, and close reading of newspaper articles drawn from the Library of Congress's *Chronicling America* archive.

**Project website:** [carlosyinn.github.io/printed-traces](https://carlosyinn.github.io/printed-traces/)

## About the Project

This project examines how U.S. newspapers between 1880 and 1885 wrote about Chinese children: their schooling, their presence in American communities, and their place in national debates over race, citizenship, and belonging. The window is bracketed by the Chinese Exclusion Act of 1882 and the *Tape v. Hurley* school-access case of 1885, a contested period for how the press portrayed Chinese youth.

The underlying corpus is 1,535 newspaper pages drawn from the Library of Congress's *Chronicling America* archive across seven keyword searches (*Chinese student*, *Chinese school*, *Chinese girl*, *Chinese children*, *Chinese child*, *Chinese boy*, *Chinese education*), spanning 323 titles and 53 states and territories. Pages were OCR-extracted, classified into core/secondary relevance tiers, and passed through a reprint-detection pipeline that reconstructs propagation chains for telegraphically reprinted stories. Two LDA topic models were then trained with MALLET at K=25: S1 over 946 originals and S2 over a 161-document deduplicated subset. The resulting topics were labeled and grouped into ten thematic categories that drive filtering and color encoding across the site's interactive map and analysis pages.

## Repository Layout

- `docs/`: VitePress source for the site (Markdown content, theme, components)
  - `introduction/`, `methodology/`, `dataset/`, `analysis/`, `map/`: site sections
  - `.vitepress/theme/`: custom theme, components, and styles
  - `public/`: static assets (favicons, images, tiles)
- `data/`: supporting data (raw Newberry Atlas source data is gitignored due to size)
- `scripts/`: scripts used to construct the dataset and prepare visualizations
- `.github/workflows/deploy.yml`: GitHub Actions workflow that builds and deploys to GitHub Pages

## Local Development

Requires Node.js 20+.

```bash
npm install
npm run dev      # start dev server
npm run build    # build static site to docs/.vitepress/dist
npm run preview  # preview the built site locally
```

## Methods & Tools

- **Site:** [VitePress](https://vitepress.dev/)
- **Topic modeling:** [MALLET](https://mimno.github.io/Mallet/)
- **Map:** [MapLibre GL JS](https://maplibre.org/) with 1882 county and state boundaries from the Newberry Library's *Atlas of Historical County Boundaries*
- **Charts:** [Datawrapper](https://www.datawrapper.de/) and [RAWGraphs](https://www.rawgraphs.io/), with chart data prepared by Python scripts in [`scripts/build_datawrapper_data/`](scripts/build_datawrapper_data/)
- **Typefaces:** Wordmark set in [Chomsky](https://github.com/ctrlcctrlv/Chomsky) typeface by Fredrick R. Brennan (converted to SVG paths)

## Data Sources

| Resource | Provider |
|---|---|
| Corpus of digitized newspaper articles | [*Chronicling America*](https://chroniclingamerica.loc.gov/), Library of Congress |
| Historical county and state boundaries | [*Atlas of Historical County Boundaries*](https://publications.newberry.org/ahcb/), Newberry Library |
| Topic model | [MALLET 2.0](https://mimno.github.io/Mallet/) (Andrew McCallum, UMass Amherst) |

## License

The site code is released under the [MIT License](LICENSE). Newspaper clippings from *Chronicling America* are in the public domain. See [About the Project](https://carlosyinn.github.io/printed-traces/introduction/about#credits) for full credits.
