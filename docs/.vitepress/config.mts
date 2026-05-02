import { defineConfig } from 'vitepress'
import footnote from 'markdown-it-footnote'

export default defineConfig({
  markdown: {
    config: (md) => {
      md.use(footnote)
    }
  },
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/printed-traces/favicon.svg' }],
  ],
  title: 'Printed Traces 1880–1885',
  description: 'A digital humanities project on Chinese immigrant children in the U.S. press, 1880–1885.',
  base: '/printed-traces/',
  appearance: true,
  lastUpdated: false,
  ignoreDeadLinks: true,

  themeConfig: {
    // Top nav — logo + date handled by NavTitle slot
    siteTitle: false,

    nav: [
      { text: 'Home Page', link: '/' },
      { text: 'Get Started', link: '/start/' },
      { text: 'Spatial Map', link: '/map/interactive' },
    ],

    // Left sidebar — Part / Chapter tree (mirrors TREE array from Docsify)
    sidebar: [
      {
        text: 'Get Started',
        link: '/start/',
        collapsed: false,
        items: [
          { text: 'Contents', link: '/start/contents' },
        ]
      },
      {
        text: 'Introduction',
        link: '/introduction/',
        collapsed: false,
        items: [
          { text: 'About the Project', link: '/introduction/about' },
          { text: 'Historical Context', link: '/introduction/context' },
        ]
      },
      {
        text: 'Methodology',
        link: '/methodology/',
        collapsed: true,
        items: [
          { text: 'Dataset Construction', link: '/methodology/dataset-construction' },
          { text: 'Analytical Methods', link: '/methodology/analytical-methods' },
          { text: 'Map Construction', link: '/methodology/map-construction' },
        ]
      },
      {
        text: 'Dataset',
        link: '/dataset/',
        collapsed: true,
        items: [
          { text: 'Browse the Dataset', link: '/dataset/browse' },
          { text: 'Dataset Reference', link: '/dataset/dataset-readme' },
        ]
      },
      {
        text: 'Analysis Results',
        link: '/analysis/',
        collapsed: true,
        items: [
          { text: 'Mapping the Discourse', link: '/analysis/mapping-discourse' },
          { text: 'The Reprint Effect', link: '/analysis/reprint-effect' },
          { text: 'Education at the Center', link: '/analysis/education-four-discourses' },
        ]
      },
      {
        text: 'Spatial Map',
        link: '/map/',
        collapsed: true,
        items: [
          { text: 'Overview', link: '/map/overview' },
          { text: 'Map References', link: '/map/references' },
        ]
      },
    ],

    // Right outline — "On This Page" (replaces custom TOC panel)
    outline: {
      level: [2, 3],
      label: 'On This Page'
    },

    // GitHub icon in top-right
    socialLinks: [
      { icon: 'github', link: 'https://github.com/CarlosYinn/printed-traces' }
    ],

    // Built-in local search with Ctrl+K
    search: {
      provider: 'local',
    },

    // Prev/Next pagination
    docFooter: {
      prev: 'Previous',
      next: 'Next'
    },

    // No edit link
    editLink: undefined,
  },
})
