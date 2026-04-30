<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  activeCategories,
  activeTopicSolo,
  toggleCategory,
} from './useFilters'
import { useRecords } from './useRecords'
import { useResponsivePanel } from './useResponsivePanel'
import type { Topic } from './types'

const { isOpen } = useResponsivePanel('left')
const { topicTree, allRecords } = useRecords()

const categories = computed(
  () => topicTree.value?.categories.filter(cat => cat.topics.some(topic => !topic.exclude)) ?? [],
)

const categoryCounts = computed(() => {
  const counts = new Map<string, number>()
  for (const record of allRecords.value) {
    const category = record.properties.category
    counts.set(category, (counts.get(category) ?? 0) + 1)
  }
  return counts
})

function visibleTopics(topics: Topic[]): Topic[] {
  return topics.filter(topic => !topic.exclude)
}

const expandedCategories = ref<Set<string>>(new Set())
const activeCategorySolo = ref<string | null>(null)

function topicWeightWidth(topic: Topic): string {
  return `min(80px, ${topic.weight * 1000}%)`
}

function toggleExpand(name: string): void {
  const next = new Set(expandedCategories.value)
  next.has(name) ? next.delete(name) : next.add(name)
  expandedCategories.value = next
}

function handleCategoryClick(name: string): void {
  if (activeCategorySolo.value === name) {
    activeCategorySolo.value = null
    activeTopicSolo.value = null
    activeCategories.value = new Set(categories.value.map(c => c.name))
    return
  }
  activeCategorySolo.value = name
  activeTopicSolo.value = null
  activeCategories.value = new Set([name])
}

function resetCategories(): void {
  activeCategorySolo.value = null
  activeTopicSolo.value = null
  activeCategories.value = new Set(categories.value.map(c => c.name))
}

function handleTopicClick(categoryName: string, topicId: string): void {
  if (activeTopicSolo.value === topicId) {
    activeTopicSolo.value = null
    return
  }
  activeCategorySolo.value = null
  activeTopicSolo.value = topicId
  activeCategories.value = new Set([categoryName])
}

const noiseCategory = computed(
  () => topicTree.value?.categories.find(cat => cat.topics.every(t => t.exclude)) ?? null,
)

const allExpanded = computed(
  () => categories.value.length > 0 && categories.value.every(c => expandedCategories.value.has(c.name)),
)

function toggleAllExpanded(): void {
  expandedCategories.value = allExpanded.value
    ? new Set()
    : new Set(categories.value.map(c => c.name))
}
</script>

<template>
  <div
    class="legend-panel"
    :class="{ 'is-collapsed': !isOpen }"
    role="region"
    aria-label="Map legend and topic filters"
  >
    <div class="panel-bar">
      <button
        class="panel-toggle"
        :aria-expanded="isOpen"
        :aria-label="isOpen ? 'Collapse legend' : 'Expand legend'"
        @click="isOpen = !isOpen"
      >
        ⚏
      </button>
      <template v-if="isOpen">
        <span class="panel-label">Topics</span>
        <div class="header-actions">
          <button type="button" class="ctrl-btn" title="Show all categories" @click="resetCategories">All</button>
          <button type="button" class="ctrl-btn" :title="allExpanded ? 'Collapse all topics' : 'Expand all topics'" @click="toggleAllExpanded">
            {{ allExpanded ? 'Collapse' : 'Expand' }}
          </button>
        </div>
      </template>
    </div>

    <div class="panel-body" :class="{ 'is-hidden': !isOpen }">
      <div class="topic-groups">
        <div
          v-for="category in categories"
          :key="`${category.name}-topics`"
          class="topic-group"
          :class="{ 'is-muted': !activeCategories.has(category.name) }"
        >
          <div class="topic-group-header">
            <button
              type="button"
              role="switch"
              class="switch-btn"
              :class="{ 'is-on': activeCategories.has(category.name) }"
              :aria-checked="activeCategories.has(category.name)"
              :aria-label="`Toggle ${category.name} category`"
              @click="toggleCategory(category.name)"
              @keydown.space.prevent="toggleCategory(category.name)"
            >
              <span class="switch-track"><span class="switch-thumb" /></span>
            </button>
            <button
              type="button"
              class="topic-group-title"
              :aria-pressed="activeCategorySolo === category.name"
              :title="category.name"
              @click="handleCategoryClick(category.name)"
            >
              <span
                class="category-dot"
                :style="{ background: category.color }"
                :title="activeCategorySolo === category.name ? 'Click to exit solo mode' : 'Click to solo this category'"
              />
              <span class="category-name" :title="category.name">{{ category.name }}</span>
              <span class="category-count" :title="`${categoryCounts.get(category.name) ?? 0} records`">{{ categoryCounts.get(category.name) ?? 0 }}</span>
            </button>
            <button
              type="button"
              class="expand-btn"
              :aria-expanded="expandedCategories.has(category.name)"
              :aria-label="`${expandedCategories.has(category.name) ? 'Collapse' : 'Expand'} ${category.name} topics`"
              @click="toggleExpand(category.name)"
            >
              ›
            </button>
          </div>
          <div v-show="expandedCategories.has(category.name)" class="topic-list">
            <button
              v-for="topic in visibleTopics(category.topics)"
              :key="topic.id"
              type="button"
              class="topic-row"
              :class="{ 'is-active': activeTopicSolo === topic.id }"
              :aria-pressed="activeTopicSolo === topic.id"
              :aria-label="`Filter to ${topic.label} topic`"
              @click="handleTopicClick(category.name, topic.id)"
            >
              <span class="topic-dot" :style="{ background: topic.color }" />
              <span class="topic-label" :title="topic.label">{{ topic.label }}</span>
              <span
                class="topic-weight"
                :title="`Corpus weight: ${(topic.weight * 100).toFixed(1)}%`"
              >
                <span
                  class="topic-weight-bar"
                  :style="{ width: topicWeightWidth(topic), background: topic.color }"
                />
              </span>
            </button>
          </div>
        </div>
      </div>

      <template v-if="noiseCategory">
        <div class="noise-divider" />
        <div
          class="topic-group"
          :class="{ 'is-muted': !activeCategories.has(noiseCategory.name) }"
        >
          <div class="topic-group-header">
            <button
              type="button"
              role="switch"
              class="switch-btn"
              :class="{ 'is-on': activeCategories.has(noiseCategory.name) }"
              :aria-checked="activeCategories.has(noiseCategory.name)"
              :aria-label="`Toggle ${noiseCategory.name} category`"
              @click="toggleCategory(noiseCategory.name)"
              @keydown.space.prevent="toggleCategory(noiseCategory.name)"
            >
              <span class="switch-track"><span class="switch-thumb" /></span>
            </button>
            <button
              type="button"
              class="topic-group-title"
              :aria-pressed="activeCategorySolo === noiseCategory.name"
              :title="noiseCategory.name"
              @click="handleCategoryClick(noiseCategory.name)"
            >
              <span
                class="category-dot"
                :style="{ background: noiseCategory.color }"
                :title="activeCategorySolo === noiseCategory.name ? 'Click to exit solo mode' : 'Click to solo this category'"
              />
              <span class="category-name" :title="noiseCategory.name">{{ noiseCategory.name }}</span>
              <span class="category-count" :title="`${categoryCounts.get(noiseCategory.name) ?? 0} records`">{{ categoryCounts.get(noiseCategory.name) ?? 0 }}</span>
            </button>
            <span aria-hidden="true" />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
/* ── Panel shell ─────────────────────────────────────────────────────────── */

.legend-panel {
  position: relative;
  pointer-events: all;
  flex: 1 1 0;
  min-height: 0;
  width: 100%;
  max-height: calc(100vh - 32px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: color-mix(in oklch, var(--ctp-base), transparent 12%);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid var(--ctp-surface0);
  border-radius: 14px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.10);
  transition:
    width var(--dur-std) var(--ease-std),
    max-height var(--dur-std) var(--ease-std);
}

.legend-panel.is-collapsed {
  width: 48px;
  max-height: 48px;
}

/* ── Panel bar (non-scrolling) ───────────────────────────────────────────── */

.panel-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  height: 48px;
  gap: 4px;
  padding-right: 8px;
}

/* ── Toggle button ───────────────────────────────────────────────────────── */

.panel-toggle {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  color: var(--ctp-subtext1);
  transition: color var(--dur-std) var(--ease-std);
}

.panel-toggle:hover {
  color: var(--ctp-text);
}

/* ── Panel body ──────────────────────────────────────────────────────────── */

.panel-body {
  padding: 0 16px 16px;
  overflow-y: auto;
  flex: 1 1 0;
  min-height: 0;
  scrollbar-width: thin;
  scrollbar-color: var(--ctp-surface1) transparent;
  opacity: 1;
  pointer-events: all;
  transition: opacity var(--dur-std) var(--ease-std);
}

.panel-body.is-hidden {
  opacity: 0;
  pointer-events: none;
}

/* ── Header ──────────────────────────────────────────────────────────────── */

.panel-label {
  flex: 1;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--ctp-overlay2);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  white-space: nowrap;
  overflow: hidden;
}

.header-actions {
  display: flex;
  gap: 5px;
}

.ctrl-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 68px;
  height: 28px;
  padding: 0;
  border: 1px solid transparent;
  border-radius: 5px;
  background: color-mix(in oklch, var(--ctp-surface1), transparent 40%);
  color: var(--ctp-subtext1);
  font-family: Cambria, Georgia, serif;
  font-size: 0.86rem;
  line-height: 1;
  cursor: pointer;
  transition:
    background var(--dur-std) var(--ease-std),
    border-color var(--dur-std) var(--ease-std),
    color var(--dur-std) var(--ease-std);
}

.ctrl-btn:hover {
  background: color-mix(in oklch, var(--ctp-surface1), transparent 10%);
  color: var(--ctp-text);
}

/* ── Switch ──────────────────────────────────────────────────────────────── */

.switch-btn {
  display: flex;
  align-items: center;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
}

.switch-track {
  position: relative;
  display: block;
  width: 32px;
  height: 18px;
  border-radius: 9px;
  background: var(--ctp-surface1);
  transition: background var(--dur-std) var(--ease-std);
}

.switch-btn.is-on .switch-track {
  background: var(--ctp-sapphire);
}

.switch-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--ctp-base);
  transition: transform var(--dur-std) var(--ease-std);
}

.switch-btn.is-on .switch-thumb {
  transform: translateX(14px);
}

/* ── Category groups ─────────────────────────────────────────────────────── */

.topic-groups {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.topic-group.is-muted .topic-row {
  opacity: 0.46;
}

.topic-group-header {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr) 18px;
  align-items: center;
  gap: 7px;
  min-height: 30px;
  margin-bottom: 2px;
}

.topic-group-title {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr) auto;
  align-items: center;
  gap: 7px;
  overflow: hidden;
  min-width: 0;
  padding: 7px 8px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--ctp-text);
  font-size: 0.82rem;
  font-weight: 700;
  line-height: 1.25;
  text-align: left;
  cursor: pointer;
  transition: background var(--dur-std) var(--ease-std);
}

.topic-group-title:hover {
  background: color-mix(in oklch, var(--ctp-surface0), transparent 50%);
}

.topic-group-title[aria-pressed='true'] {
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
}

.category-dot,
.topic-dot {
  flex-shrink: 0;
  border-radius: 50%;
}

.category-dot {
  width: 10px;
  height: 10px;
}

.category-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-count {
  color: var(--ctp-overlay1);
  font-family: var(--font-num-tabular);
  font-size: 0.72rem;
  font-weight: 600;
  line-height: 1.25;
  white-space: nowrap;
}

.expand-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 20px;
  padding: 0;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--ctp-overlay1);
  font-size: 1rem;
  line-height: 1;
  cursor: pointer;
  transition:
    background var(--dur-std) var(--ease-std),
    color var(--dur-std) var(--ease-std),
    transform var(--dur-std) var(--ease-std);
}

.expand-btn:hover {
  background: color-mix(in oklch, var(--ctp-surface0), transparent 50%);
  color: var(--ctp-text);
}

.expand-btn[aria-expanded='true'] {
  transform: rotate(90deg);
}

/* ── Topic rows ──────────────────────────────────────────────────────────── */

.topic-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin: 3px 0 5px;
}

.topic-row {
  display: grid;
  grid-template-columns: 8px minmax(0, 1fr) 80px;
  align-items: center;
  gap: 7px;
  width: 100%;
  min-height: 22px;
  padding: 3px 4px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--ctp-text);
  text-align: left;
  cursor: pointer;
  transition:
    background var(--dur-std) var(--ease-std),
    opacity var(--dur-std) var(--ease-std);
}

.topic-row:hover {
  background: color-mix(in oklch, var(--ctp-surface0), transparent 55%);
}

.topic-row.is-active {
  background: var(--vp-c-brand-soft);
}

.topic-dot {
  width: 8px;
  height: 8px;
}

.topic-label {
  overflow: hidden;
  color: var(--ctp-text);
  font-size: 13px;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.topic-weight {
  position: relative;
  width: 80px;
  height: 6px;
  overflow: hidden;
  border-radius: 3px;
  background: color-mix(in oklch, var(--ctp-surface0), transparent 35%);
}

.topic-weight-bar {
  position: absolute;
  inset: 0 auto 0 0;
  max-width: 80px;
  border-radius: 3px;
  opacity: 0.3;
}

/* ── Noise divider ───────────────────────────────────────────────────────── */

.noise-divider {
  margin: 6px 0 4px;
  border-top: 1px solid var(--ctp-surface0);
}

/* ── Focus rings ─────────────────────────────────────────────────────────── */

button:focus-visible {
  outline: 2px solid var(--vp-c-brand-1);
  outline-offset: 2px;
}

@media (max-width: 760px) {
  .legend-panel {
    width: 100%;
  }
}
</style>
