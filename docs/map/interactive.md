---
layout: page
pageClass: map-fullscreen-page
title: Spatial Map — Chinese Immigrant Children in the U.S. Press, 1880–1885
description: Explore the geographic and thematic distribution of newspaper coverage of Chinese children across the United States from 1880 to 1885. Filter by topic category, time period, and historical event.
head:
  - - meta
    - name: og:title
      content: Spatial Map — Chinese Immigrant Children in the U.S. Press
  - - meta
    - name: og:description
      content: An interactive map of newspaper records from the Chronicling America archive, plotted on 1882 county and state boundaries, filtered by topic and time.
---

<script setup>
import InteractiveMap from '../.vitepress/theme/components/InteractiveMap.vue'
</script>

<ClientOnly>
  <InteractiveMap />
</ClientOnly>
