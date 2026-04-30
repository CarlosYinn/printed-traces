<p align="center">
  <img src="docs/public/printed-traces.svg" alt="Printed Traces" width="400" />
</p>

<p align="center"><strong>Chinese Immigrant Children in the U.S. Press, 1880–1885</strong></p>

A digital humanities project that combines close historical analysis with corpus-based methods to study how Chinese children were represented in American newspapers during the Chinese exclusion era. The site brings together topic modeling, geographic visualization, and close reading of newspaper articles drawn from the Library of Congress's *Chronicling America* archive.

**Project website:** [carlosyinn.github.io/printed-traces](https://carlosyinn.github.io/printed-traces/)

## About the Project

During the 1880s, Chinese children were demographically rare in the United States, yet they appeared with striking frequency in press coverage, legal proceedings, and political debate. Their scarcity, paradoxically, made them hyper-visible. As the only members of Chinese communities who could claim unambiguous birthright citizenship under the Fourteenth Amendment, they occupied a uniquely contested legal position, and newspapers played an active role in shaping how that position was understood by the public.

The project traces a discursive shift across the study period: early coverage tended to frame Chinese children through missionary narratives and cultural curiosity, while by the mid-1880s, newspapers increasingly emphasized public schooling, legal rights, and racial conflict. This shift coincided with landmark cases such as *In re Look Tin Sing* (1884) and *Tape v. Hurley* (1885).

## What's in This Repo

- `docs/` — VitePress source for the site (Markdown content, theme, components)
  - `introduction/`, `methodology/`, `dataset/`, `analysis/`, `map/` — site sections
  - `.vitepress/theme/` — custom theme, components, and styles
  - `public/` — static assets (favicons, images, tiles)
- `data/` — supporting data (raw Newberry Atlas source data is gitignored due to size)
- `scripts/` — scripts used to construct the dataset and prepare visualizations
- `.github/workflows/deploy.yml` — GitHub Actions workflow that builds and deploys to GitHub Pages

## Local Development

Requires Node.js 20+.

```bash
npm install
npm run dev      # start dev server
npm run build    # build static site to docs/.vitepress/dist
npm run preview  # preview the built site locally
```

## Deployment

The site is deployed automatically to GitHub Pages on every push to `main` via [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml). The `base` path is set to `/printed-traces/` in [`docs/.vitepress/config.mts`](docs/.vitepress/config.mts).

## Methods & Tools

- **Site:** [VitePress](https://vitepress.dev/)
- **Topic modeling:** [MALLET](https://mimno.github.io/Mallet/)
- **Map:** [MapLibre GL JS](https://maplibre.org/) with 1882 county and state boundaries from the Newberry Library's *Atlas of Historical County Boundaries*
- **Charts:** Datawrapper embeds and D3-based visualizations
- **Typefaces:** Wordmark set in [Chomsky](https://github.com/ctrlcctrlv/chomsky) by Fredrick R. Brennan; body text in Cambria; monospace in IBM Plex Mono and JetBrains Mono

## Data Sources

| Resource | Provider |
|---|---|
| Corpus of digitized newspaper articles | *Chronicling America*, Library of Congress |
| Historical county and state boundaries | *Atlas of Historical County Boundaries*, Newberry Library |
| Topic model | MALLET 2.0 (Andrew McCallum, UMass Amherst) |

All newspaper clippings reproduced on the site are drawn from *Chronicling America: Historic American Newspapers* and are in the public domain.

## License

The site code (theme, components, build configuration) is released under the MIT License. Newspaper clippings and historical materials reproduced from *Chronicling America* are in the public domain. Other third-party assets retain their original licenses; see [About the Project](https://carlosyinn.github.io/printed-traces/introduction/about) for credits.
