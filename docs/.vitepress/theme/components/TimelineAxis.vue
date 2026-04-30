<script setup lang="ts">
import { computed } from 'vue'
import { activeEventId, timeFilter, setTimeFilter } from './useFilters'
import { isPlaying } from './usePlayback'
import { useRecords } from './useRecords'
import { useEventColor } from './useEventColor'
import { useResponsivePanel } from './useResponsivePanel'

const { events } = useRecords()
const { getEventAccentColor } = useEventColor()
const { isOpen } = useResponsivePanel()

const YEARS = [1880, 1881, 1882, 1883, 1884, 1885]

const yearNodes = computed(() =>
  YEARS.map(year => {
    const yearEvents = events.value.filter(e => e.date.startsWith(String(year)))
    const hasActive = yearEvents.some(e => e.id === activeEventId.value)
    const isYearSelected = timeFilter.value?.type === 'year' && timeFilter.value.year === year
    return { year, events: yearEvents, hasActive, isYearSelected }
  })
)

function handleYearClick(node: { year: number; isYearSelected: boolean }) {
  isPlaying.value = false
  activeEventId.value = null
  setTimeFilter(node.isYearSelected ? null : { type: 'year', year: node.year })
}

function handleEventDotClick(evt: { id: string; date: string }) {
  isPlaying.value = false
  if (activeEventId.value === evt.id) {
    activeEventId.value = null
    setTimeFilter(null)
    return
  }
  activeEventId.value = evt.id
  setTimeFilter({ type: 'month', ym: evt.date.slice(0, 7) })
}
</script>

<template>
  <div
    class="timeline-panel"
    :class="{ 'is-collapsed': !isOpen }"
    role="navigation"
    aria-label="Timeline navigation"
  >
    <button
      class="panel-toggle"
      :aria-expanded="isOpen"
      :aria-label="isOpen ? 'Collapse timeline' : 'Expand timeline'"
      @click="isOpen = !isOpen"
    >
      ≡
    </button>
    <div class="panel-bar">
      <span v-if="isOpen" class="panel-label">Events</span>
    </div>

    <div class="panel-body" :class="{ 'is-hidden': !isOpen }">
      <div class="timeline-track">
        <div v-for="node in yearNodes" :key="node.year" class="year-node-wrapper">
          <button
            class="year-node"
            :class="{
              'is-active': node.isYearSelected || node.hasActive,
              'has-events': node.events.length > 0,
            }"
            :aria-label="`Jump to ${node.year}`"
            :title="node.isYearSelected ? `Showing all records for ${node.year} — click to clear` : `Show all records for ${node.year}`"
            @click="handleYearClick(node)"
          >
            <div class="node-dot" />
            <div class="node-label">
              <span class="node-year">{{ node.year }}</span>
              <span v-if="node.events.length > 0" class="node-event-count">
                {{ node.events.length }} event{{ node.events.length > 1 ? 's' : '' }}
              </span>
            </div>
          </button>

          <div v-if="node.events.length > 0" class="event-dots">
            <button
              v-for="evt in node.events"
              :key="evt.id"
              class="event-dot"
              :class="{ 'is-active': evt.id === activeEventId }"
              :style="{ '--dot-color': getEventAccentColor(evt) }"
              :title="evt.title"
              @click="handleEventDotClick(evt)"
            >
              <span class="dot-mark" />
              <span class="dot-title">{{ evt.title }}</span>
            </button>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* ── Panel shell ─────────────────────────────────────────────────────────── */

.timeline-panel {
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

.timeline-panel.is-collapsed {
  width: 48px;
  max-height: 48px;
}

/* ── Panel bar (non-scrolling) ───────────────────────────────────────────── */

.panel-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  height: 48px;
  padding: 0 48px 0 6px;
}

/* ── Toggle button ───────────────────────────────────────────────────────── */

.panel-toggle {
  position: absolute;
  top: 0;
  right: 0;
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
  z-index: 2;
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
  padding-left: 16px;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--ctp-overlay2);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  white-space: nowrap;
  overflow: hidden;
}

/* ── Timeline track ──────────────────────────────────────────────────────── */

.timeline-track {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.year-node-wrapper {
  display: flex;
  flex-direction: column;
}

.year-node {
  display: grid;
  grid-template-columns: 18px minmax(0, 1fr);
  align-items: center;
  gap: 9px;
  width: 100%;
  min-height: 30px;
  padding: 3px 6px;
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
  border-radius: 5px;
  transition:
    background var(--dur-std) var(--ease-std),
    color var(--dur-std) var(--ease-std);
}

.year-node:hover {
  background: color-mix(in oklch, var(--ctp-surface0), transparent 50%);
}

.node-dot {
  width: 15px;
  height: 15px;
  border-radius: 3px;
  flex-shrink: 0;
  border: 1px solid var(--ctp-surface1);
  background: color-mix(in oklch, var(--ctp-base), transparent 35%);
  box-shadow: inset 0 0 0 2px color-mix(in oklch, var(--ctp-base), transparent 10%);
  transition:
    background var(--dur-std) var(--ease-std),
    border-color var(--dur-std) var(--ease-std),
    box-shadow var(--dur-std) var(--ease-std);
}

.year-node.has-events .node-dot {
  border-color: var(--ctp-sapphire);
  background: color-mix(in oklch, var(--ctp-sapphire), transparent 78%);
}

.year-node.is-active .node-dot {
  border-color: var(--vp-c-brand-1);
  background: var(--vp-c-brand-1);
  box-shadow: 0 0 0 3px color-mix(in oklch, var(--vp-c-brand-1), transparent 72%);
}

.node-label {
  display: flex;
  align-items: baseline;
  gap: 7px;
  min-width: 0;
}

.node-year {
  font-size: 0.86rem;
  font-weight: 700;
  color: var(--ctp-text);
  font-variant-numeric: tabular-nums;
  line-height: 1.35;
  white-space: nowrap;
  overflow: hidden;
}

.year-node.is-active .node-year {
  color: var(--vp-c-brand-1);
}

.node-event-count {
  display: block;
  overflow: hidden;
  color: var(--ctp-overlay1);
  font-size: 0.72rem;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Event dots ──────────────────────────────────────────────────────────── */

.event-dots {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin: 3px 0 5px 27px;
}

.event-dot {
  display: flex;
  align-items: center;
  gap: 7px;
  width: 100%;
  min-height: 24px;
  padding: 3px 6px;
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
  border-radius: 5px;
  transition: background var(--dur-std) var(--ease-std);
}

.event-dot:hover {
  background: color-mix(in oklch, var(--ctp-surface0), transparent 60%);
}

.dot-mark {
  width: 7px;
  height: 7px;
  border-radius: 2px;
  flex-shrink: 0;
  background: var(--dot-color, var(--ctp-peach));
  opacity: 0.75;
  transition: all 0.15s;
}

.event-dot.is-active .dot-mark {
  opacity: 1;
  transform: scale(1.4);
  box-shadow: 0 0 0 3px color-mix(in oklch, var(--dot-color, var(--ctp-peach)), transparent 60%);
}

.dot-title {
  font-size: 0.79rem;
  color: var(--ctp-subtext1);
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.event-dot.is-active .dot-title {
  color: var(--ctp-text);
  font-weight: 600;
}

/* ── Global event card ───────────────────────────────────────────────────── */

/* ── Focus rings ─────────────────────────────────────────────────────────── */

button:focus-visible {
  outline: 2px solid var(--vp-c-brand-1);
  outline-offset: 2px;
}

@media (max-width: 760px) {
  .timeline-panel {
    width: 100%;
  }
}
</style>
