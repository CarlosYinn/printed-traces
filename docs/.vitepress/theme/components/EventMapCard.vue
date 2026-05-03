<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import type { FeatureCollection } from 'geojson'
import type { Map } from 'maplibre-gl'
import type { HistoricalEvent } from './types'
import { getAnchorForEvent, getEventStateAbbreviations } from './useMap'
import { useIsMobile } from './useIsMobile'

const props = withDefaults(defineProps<{
  event: HistoricalEvent
  accentColor: string
  mapInstance: Map
  mapContainer: HTMLElement
  countiesGeoJSON: FeatureCollection
  cardHeight?: number
  eventIndex?: number
  eventTotal?: number
}>(), {
  cardHeight: 0,
  eventIndex: 0,
  eventTotal: 1,
})

const emit = defineEmits<{ close: [], prev: [], next: [] }>()

// ─── date formatting ───

function formatDate(date: string): string {
  const parsed = new Date(`${date}T00:00:00`)
  if (Number.isNaN(parsed.getTime())) return date
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(parsed)
}

// ─── anchor coordinate ───
// Delegates to useMap.getAnchorForEvent — same FIPS resolution rules
// (state prefix vs full county FIPS) shared with computeEventBbox /
// getEventStateAbbreviations, so all three stay in sync.

const anchorLngLat = computed<[number, number] | null>(() =>
  getAnchorForEvent(props.event, props.countiesGeoJSON),
)

// ─── pixel projection, kept current via map events ───

const anchorPixel = ref<{ x: number; y: number } | null>(null)

// MapLibre fires `move` for both pans AND zooms — the `zoom` event is a strict
// subset, so one listener suffices. Sub-pixel deltas are skipped
// to avoid triggering Vue reactivity for changes that wouldn't visibly move
// the card (the projection during inertial pan can wobble fractionally each
// frame even when the camera is at rest).
function updateAnchor() {
  const lngLat = anchorLngLat.value
  if (!lngLat) {
    if (anchorPixel.value !== null) anchorPixel.value = null
    return
  }
  const next = props.mapInstance.project(lngLat)
  const cur = anchorPixel.value
  if (cur && Math.abs(cur.x - next.x) < 0.5 && Math.abs(cur.y - next.y) < 0.5) return
  anchorPixel.value = { x: next.x, y: next.y }
}

// Project once now (immediate) and re-project whenever the selected event
// changes — the parent re-uses this component instead of remounting with a
// new key.
watch(anchorLngLat, updateAnchor, { immediate: true })

// ─── mobile detection (bottom-sheet layout) ───

const isMobile = useIsMobile()

onMounted(() => {
  props.mapInstance.on('move', updateAnchor)
})

onUnmounted(() => {
  props.mapInstance.off('move', updateAnchor)
})

// ─── card position & side ───

const CARD_WIDTH = 290
const CONNECTOR_OFFSET = 20

const isGlobal = computed(() => props.event.highlight_fips.length === 0)

const cardSide = computed<'left' | 'right'>(() => {
  if (!anchorPixel.value) return 'right'
  return anchorPixel.value.x + 80 + CARD_WIDTH > props.mapContainer.offsetWidth
    ? 'left'
    : 'right'
})

// Centre the card vertically on the anchor using the live-measured card
// height; clamp so the card never extends past the top of the map.  The
// connector hairline therefore always sits at the card's vertical middle.
const cardTop = computed(() =>
  anchorPixel.value
    ? Math.max(8, anchorPixel.value.y - props.cardHeight / 2)
    : 8,
)

// Vertical offset of the connector within the card = anchor y − card top.
const connectorTop = computed(() =>
  anchorPixel.value ? anchorPixel.value.y - cardTop.value : props.cardHeight / 2,
)

const cardStyle = computed(() => {
  if (isMobile.value) {
    return {
      position: 'absolute' as const,
      left: '12px',
      right: '12px',
      bottom: '12px',
      width: 'auto',
      zIndex: 10,
    }
  }
  if (isGlobal.value) {
    return {
      position: 'absolute' as const,
      top: '72px',
      left: '50%',
      transform: 'translateX(-50%)',
      width: `${CARD_WIDTH}px`,
      zIndex: 10,
    }
  }
  // v-if="isGlobal || anchorPixel" guarantees anchorPixel is set here.
  const { x } = anchorPixel.value!
  return {
    position: 'absolute' as const,
    top: `${cardTop.value}px`,
    left: cardSide.value === 'right'
      ? `${x + CONNECTOR_OFFSET}px`
      : `${x - CARD_WIDTH - CONNECTOR_OFFSET}px`,
    width: `${CARD_WIDTH}px`,
    zIndex: 10,
  }
})

const cardClasses = computed(() => {
  if (isMobile.value) return 'is-mobile'
  if (isGlobal.value) return ''
  return `side-${cardSide.value}`
})

const anchorStyle = computed(() => {
  if (!anchorPixel.value) return { display: 'none' as const }
  return {
    position: 'absolute' as const,
    left: `${anchorPixel.value.x}px`,
    top: `${anchorPixel.value.y}px`,
    transform: 'translate(-50%, -50%)',
    zIndex: 9,
  }
})

// ─── state abbreviation tags ───

const stateAbbrs = computed(() =>
  getEventStateAbbreviations(props.event, props.countiesGeoJSON),
)

function handleNavClick(event: MouseEvent, direction: 'prev' | 'next'): void {
  if (direction === 'prev') {
    emit('prev')
  } else {
    emit('next')
  }
  ;(event.currentTarget as HTMLButtonElement | null)?.blur()
}
</script>

<template>
  <Transition name="card">
    <div
      v-if="isGlobal || anchorPixel"
      class="event-map-card"
      :class="cardClasses"
      :style="cardStyle"
    >
      <div class="card-accent" :style="{ background: accentColor }" />

      <button class="card-close" aria-label="Close event" @click="emit('close')">✕</button>

      <div class="card-body">
        <div class="card-date">{{ formatDate(event.date) }}</div>
        <div class="card-title">{{ event.title }}</div>
        <div class="card-desc">{{ event.description }}</div>
        <div class="card-footer">
          <div class="card-tags">
            <span class="card-tag">{{ event.highlight_level }}</span>
            <span v-for="abbr in stateAbbrs" :key="abbr" class="card-tag">{{ abbr }}</span>
          </div>
          <div v-if="eventTotal > 1" class="card-nav">
            <button class="nav-btn" aria-label="Previous event" @click.stop="handleNavClick($event, 'prev')">&#8592;</button>
            <span class="nav-counter">{{ eventIndex + 1 }}&thinsp;/&thinsp;{{ eventTotal }}</span>
            <button class="nav-btn" aria-label="Next event" @click.stop="handleNavClick($event, 'next')">&#8594;</button>
          </div>
        </div>
      </div>

      <div v-if="!isGlobal && !isMobile" class="card-connector" :style="{ top: `${connectorTop}px` }" />
    </div>
  </Transition>

  <div
    v-if="!isGlobal && anchorPixel"
    class="anchor-pulse"
    :style="{ ...anchorStyle, background: accentColor }"
  />
</template>

<style scoped>
/* ── Card shell ── */

.event-map-card {
  position: relative; /* containing block for .card-connector */
  display: flex;
  flex-direction: column;
  overflow: visible;  /* connector ::before must extend outside the card */
  border-radius: 10px;
  background: var(--ctp-base); /* fallback if color-mix unsupported */
  background: color-mix(in oklch, var(--ctp-base), transparent 4%);
  border: 1px solid color-mix(in oklch, var(--ctp-surface1), transparent 40%);
  box-shadow:
    inset 0 1px 0 color-mix(in oklch, white, transparent 88%),
    0 8px 32px rgba(0, 0, 0, 0.22);
  color: var(--ctp-text);
  pointer-events: all;
}

/* ── Accent bar ── */

/* overflow: visible on the card means we can't rely on clip for corner rounding;
   give the accent bar its own matching top border-radius instead. */
.card-accent {
  flex-shrink: 0;
  width: 100%;
  height: 12px;
  border-radius: 9px 9px 0 0;
}

/* ── Close button ── */

.card-close {
  position: absolute;
  top: 20px;
  right: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  padding: 0;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--ctp-overlay1);
  font-size: 11px;
  line-height: 1;
  cursor: pointer;
  z-index: 1;
}

.card-close:hover {
  background: var(--ctp-surface0);
  color: var(--ctp-text);
}

/* ── Card body ── */

.card-body {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  gap: 5px;
  padding: 12px 14px 14px;
}

.card-date {
  color: var(--ctp-overlay2);
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.card-title {
  color: var(--ctp-text);
  font-size: 0.98rem;
  font-weight: 600;
  line-height: 1.3;
}

.card-desc {
  color: var(--ctp-subtext0);
  font-size: 0.82rem;
  line-height: 1.48;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 3px;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.card-nav {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: auto;
  height: auto;
  padding: 5px 10px;
  border: 1px solid var(--ctp-surface1);
  border-radius: 5px;
  background: transparent;
  color: var(--ctp-subtext0);
  font-size: 11px;
  line-height: 1;
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-std), border-color var(--dur-fast) var(--ease-std), color var(--dur-fast) var(--ease-std);
  -webkit-tap-highlight-color: transparent;
}

.nav-btn:hover,
.nav-btn:active {
  background: color-mix(in oklch, var(--ctp-surface1), transparent 40%);
  border-color: var(--ctp-overlay0);
  color: var(--ctp-text);
}

@media (hover: none) {
  .nav-btn:hover {
    background: transparent;
    border-color: var(--ctp-surface1);
    color: var(--ctp-subtext0);
  }

  .nav-btn:active {
    background: color-mix(in oklch, var(--ctp-surface1), transparent 40%);
    border-color: var(--ctp-overlay0);
    color: var(--ctp-text);
  }
}

.nav-counter {
  min-width: 36px;
  text-align: center;
  color: var(--ctp-overlay2);
  font-size: 0.72rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.04em;
  pointer-events: none;
}

.card-tag {
  padding: 1px 6px;
  border-radius: 999px;
  background: color-mix(in oklch, var(--ctp-surface1), transparent 30%);
  color: var(--ctp-overlay2);
  font-size: 0.6rem;
  font-weight: 600;
  line-height: 1.5;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* ── Connector hairline ── */
/*
  .card-connector is a zero-size div whose `top` is set inline to the exact
  pixel row of the anchor dot within the card.  CSS positions it against the
  correct card edge (left for side-right, right for side-left) so that ::before
  draws a 20 px horizontal line bridging the card boundary to the anchor dot.
*/

.card-connector {
  position: absolute;
  width: 0;
  height: 0;
  pointer-events: none;
}

/* side-right: card is to the right of the anchor → connector exits left edge */
.event-map-card.side-right .card-connector {
  left: 0;
}

.event-map-card.side-right .card-connector::before {
  content: '';
  position: absolute;
  top: 0;
  left: -20px;
  width: 20px;
  height: 1px;
  background: color-mix(in oklch, var(--ctp-overlay0), transparent 50%);
}

/* side-left: card is to the left of the anchor → connector exits right edge */
.event-map-card.side-left .card-connector {
  right: 0;
  left: auto;
}

.event-map-card.side-left .card-connector::before {
  content: '';
  position: absolute;
  top: 0;
  left: auto;
  right: -20px;
  width: 20px;
  height: 1px;
  background: color-mix(in oklch, var(--ctp-overlay0), transparent 50%);
}

/* ── Anchor pulse dot ── */

.anchor-pulse {
  position: relative; /* containing block for ::after inset */
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid var(--ctp-base);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.20);
  pointer-events: none;
}

.anchor-pulse::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  background: inherit;
  opacity: 0.35;
  animation: anchor-ring 2s ease-out infinite;
}

@keyframes anchor-ring {
  0%   { transform: scale(1);   opacity: 0.35; }
  100% { transform: scale(2.8); opacity: 0;    }
}

/* ── Card enter / leave transition ── */

@keyframes card-rise {
  0%   { opacity: 0; transform: translateY(14px) scale(0.96); }
  45%  { opacity: 1; transform: translateY(-8px) scale(1.01); }
  100% { opacity: 1; transform: translateY(0)    scale(1);    }
}

@keyframes card-sink {
  0%   { opacity: 1; transform: translateY(0)   scale(1);    }
  100% { opacity: 0; transform: translateY(10px) scale(0.96); }
}

.card-enter-active {
  animation: card-rise 1000ms cubic-bezier(0.34, 1.36, 0.64, 1) forwards;
}

.card-leave-active {
  animation: card-sink 1000ms ease-in forwards;
}

/* ── Mobile bottom-sheet variant ── */

.event-map-card.is-mobile {
  max-height: 45vh;
}

.event-map-card.is-mobile .card-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--ctp-surface1) transparent;
}

@media (max-width: 760px) {
  .card-enter-active,
  .card-leave-active {
    animation-duration: 320ms;
  }
}
</style>
