<p align="center">
  <img src="docs/public/printed-traces.svg" alt="Printed Traces" width="400" />
</p>

<p align="center"><strong>Chinese Immigrant Children in the U.S. Press, 1880–1885</strong></p>

A digital humanities project that combines close historical analysis with corpus-based methods to study how Chinese children were represented in American newspapers during the Chinese exclusion era. The site brings together topic modeling, geographic visualization, and close reading of newspaper articles drawn from the Library of Congress's *Chronicling America* archive.

**Project website:** [carlosyinn.github.io/printed-traces](https://carlosyinn.github.io/printed-traces/)

## About the Project

This project examines how U.S. newspapers between 1880 and 1885 wrote about Chinese children: their schooling, their presence in American communities, and their place in national debates over race, citizenship, and belonging. The window is bracketed by the Chinese Exclusion Act of 1882 and the *Tape v. Hurley* school-access case of 1885, a contested period for how the press portrayed Chinese youth.

The underlying corpus is 1,535 newspaper pages drawn from the Library of Congress's *Chronicling America* archive across seven keyword searches ("Chinese student," "Chinese school," "Chinese girl," "Chinese children," "Chinese child," "Chinese boy," "Chinese education"), spanning 323 titles and 53 states and territories. Pages were OCR-extracted, classified into core/secondary relevance tiers, and passed through a reprint-detection pipeline that reconstructs propagation chains for telegraphically reprinted stories. Two LDA topic models were then trained with MALLET at K=25: S1 over 946 originals and S2 over a 161-document deduplicated subset. The resulting topics were labeled and grouped into ten thematic categories that drive filtering and color encoding across the site's interactive map and analysis pages.

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

- **Site:** built with [Vue.js](https://vuejs.org/) using [VitePress](https://vitepress.dev/)
- **Topic modeling:** [MALLET](https://mimno.github.io/Mallet/)
- **Data visualization:** [Datawrapper](https://www.datawrapper.de/) and [RAWGraphs](https://www.rawgraphs.io/)
- **Map:** [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/), [Allmaps](https://allmaps.org/), [QGIS](https://qgis.org/), and [Turf.js](https://turfjs.org/)
- **Typefaces:** Wordmark set in [Chomsky](https://github.com/ctrlcctrlv/Chomsky) typeface (converted to SVG paths)

## Data Sources

| Resource | Provider |
|---|---|
| Digitized newspaper records | [*Chronicling America*](https://www.loc.gov/collections/chronicling-america/about-this-collection/), Library of Congress |
| Historical county and state boundaries | [*Atlas of Historical County Boundaries*](https://publications.newberry.org/ahcb/), Newberry Library |
| OpenStreetMap basemap | [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), ODbL. |
| 1882 railroad and county map | [Rand McNally and Company](https://collections.leventhalmap.org/search/commonwealth:1257b834v), Norman B. Leventhal Map & Education Center at the Boston Public Library |

## License

The site code is released under the [MIT License](LICENSE). Newspaper clippings from *Chronicling America* are in the public domain. See [About the Project](https://carlosyinn.github.io/printed-traces/introduction/about#credits) and [Map References](https://carlosyinn.github.io/printed-traces/map/references)for full credits.
