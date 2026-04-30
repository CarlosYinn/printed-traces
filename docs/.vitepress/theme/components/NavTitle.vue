<script setup lang="ts">
import { withBase } from 'vitepress'

const lightLogo = withBase('/favicon-light.svg')
const darkLogo = withBase('/favicon-dark.svg')
</script>

<template>
  <div class="nav-brand">
    <img :src="lightLogo" alt="Printed Traces" class="nav-logo nav-logo--light" />
    <img :src="darkLogo" alt="Printed Traces" class="nav-logo nav-logo--dark" />
    <div class="nav-title-meta">
      <span class="nav-dates">1880&ndash;1885</span>
      <span class="nav-era">Newspaper Archive</span>
    </div>
  </div>
</template>

<style scoped>
.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.nav-logo {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}

.nav-title-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.nav-dates {
  font-family: "Cambria", Georgia, serif;
  font-size: 15px;
  font-weight: 500;
  letter-spacing: 0.02em;
  color: var(--vp-c-text-1);
}

.nav-era {
  font-size: 10px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--vp-c-text-3);
  margin-top: 2px;
}
</style>
