<script setup lang="ts">
import { ref, shallowRef, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useData } from 'vitepress'
import type { GeoJSONSource, MapMouseEvent } from 'maplibre-gl'
import type { Map as MapLibreMap } from 'maplibre-gl'
import type { FeatureCollection } from 'geojson'

import RecordPopup from './RecordPopup.vue'
import LayerPanel from './LayerPanel.vue'
import Legend from './Legend.vue'
import TimelineAxis from './TimelineAxis.vue'
import MonthCalendar from './MonthCalendar.vue'
import EventMapCard from './EventMapCard.vue'
import { useEventColor } from './useEventColor'
import {
  createMap,
  registerSources,
  registerLayers,
  highlightEvent,
  clearHighlight,
  computeEventBbox,
  getAnchorForEvent,
} from './useMap'
import { useIsMobile, isMobileViewport } from './useIsMobile'
import {
  timeFilter,
  baseLayers,
  overlays,
  activeEventId,
  dismissActiveEvent,
} from './useFilters'
import { resetNorthSignal, resetCenterSignal } from './useMapControls'
import {
  useRecords,
  allRecords,
  topicTree,
  events,
  counties,
  states,
  visibleRecords,
} from './useRecords'
import type { HistoricalEvent, RecordProperties } from './types'

// ─── props ────────────────────────────────────────────────────────────────────

const props = withDefaults(defineProps<{
  height?: string
  showPopup?: boolean
  enableClusterZoom?: boolean
}>(), {
  height: '100%',
  showPopup: true,
  enableClusterZoom: true,
})

// ─── data loading ─────────────────────────────────────────────────────────────

useRecords()

// ─── dark mode ───────────────────────────────────────────────────────────────

const { isDark } = useData()

// ─── event colour helper ──────────────────────────────────────────────────────

const { getEventAccentColor } = useEventColor()

const activeEvent = computed(() =>
  activeEventId.value
    ? events.value.find(e => e.id === activeEventId.value) ?? null
    : null
)

// ─── map instance — must NOT be reactive (no Proxy wrapping MapLibre objects) ─

let map: MapLibreMap | null = null

// Shallow ref so the template can reactively gate on map availability without
// wrapping the MapLibre object in a deep Proxy.
const mapReady = shallowRef<MapLibreMap | null>(null)

// ─── template refs & popup state ─────────────────────────────────────────────

const containerRef = ref<HTMLDivElement>()
const hoveredRecord = ref<RecordProperties | null>(null)
const popupPosition = ref<{ x: number; y: number } | null>(null)
const popupPinned = ref(false) // true after clicking a point; suppresses hover-dismiss

const isMobileWidth = useIsMobile()

// True when the mobile bottom-sheet card is on screen — used by the layout
// to shorten the left/right stacks so they don't render under the card.
const hasEventCard = computed(() => isMobileWidth.value && !!activeEvent.value)

// Measured height of the EventMapCard, propagated to CSS as --mobile-card-h
// so the left/right stacks can end exactly above the card and fill the
// remaining vertical space — instead of reserving a hard-coded 45vh.
const cardHeight = ref(0)
let cardResizeObserver: ResizeObserver | null = null

function detachCardObserver() {
  cardResizeObserver?.disconnect()
  cardResizeObserver = null
}

watch([() => !!activeEvent.value, mapReady], ([hasEvt, ready]) => {
  detachCardObserver()
  if (!hasEvt || !ready) {
    cardHeight.value = 0
    return
  }
  nextTick(() => {
    const el = containerRef.value?.querySelector('.event-map-card') as HTMLElement | null
    if (!el) return
    cardResizeObserver = new ResizeObserver(entries => {
      const entry = entries[0]
      if (entry) cardHeight.value = Math.ceil(entry.contentRect.height)
    })
    cardResizeObserver.observe(el)
  })
})

function dismissPinnedPopup() {
  hoveredRecord.value = null
  popupPosition.value = null
  popupPinned.value = false
}

const activeEventIndex = computed(() =>
  activeEventId.value ? events.value.findIndex(e => e.id === activeEventId.value) : -1
)

function navigateEvent(delta: -1 | 1) {
  const total = events.value.length
  if (total === 0) return
  const idx = activeEventIndex.value === -1 ? 0 : activeEventIndex.value
  activeEventId.value = events.value[(idx + delta + total) % total].id
}

// ─── empty-state computed ─────────────────────────────────────────────────────

const isEmptyState = computed(
  () => visibleRecords.value.length === 0 && timeFilter.value !== null,
)

const displayMonthLabel = computed(() => {
  const tf = timeFilter.value
  if (!tf) return 'this period'
  if (tf.type === 'year') return String(tf.year)
  return tf.ym
})

// ─── watcher teardown list ────────────────────────────────────────────────────

const stoppers: Array<() => void> = []

// Padding used when fitting the map to an event's bbox.  On mobile the
// EventMapCard renders as a bottom sheet, so we leave room at the bottom and
// shrink the side gutters; on desktop the card docks beside the anchor on the
// right, so we reserve 300 px on that side plus 320 px of historical lateral
// breathing room (the latter was previously contributed by map.setPadding,
// which had to be removed because it stacks on top of fitBounds padding and
// makes the available width negative on a 375 px mobile viewport).
//
// Padding is measured against the actual map container (not the window),
// because the map can be embedded in a constrained doc layout. MapLibre
// silently aborts fitBounds when top+bottom or left+right exceed the canvas,
// so we clamp each side to roughly one third of the container.
function eventFitPadding(): { top: number; bottom: number; left: number; right: number } {
  if (!isMobileViewport() || !map) {
    return { top: 60, bottom: 60, left: 380, right: 620 }
  }
  const container = map.getContainer()
  const h = container.offsetHeight || window.innerHeight
  const w = container.offsetWidth || window.innerWidth
  // Reserve up to a third of the map below the bbox for the bottom-sheet card,
  // capped at 260 px so the bbox still gets a reasonable target area on tall
  // screens. Other sides stay small.
  return {
    top: Math.min(28, Math.floor(h / 12)),
    bottom: Math.max(60, Math.min(260, Math.floor(h / 3))),
    left: Math.min(24, Math.floor(w / 16)),
    right: Math.min(24, Math.floor(w / 16)),
  }
}

// Fly to an event's view.  fitBounds always centres the *bbox* in the padded
// viewport, but the anchor pulse renders at the geometry centroid — and the
// two are not the same point.  On mobile this drift is visible (the dot
// lands off-centre in the upper map area).  To fix it we synthesise a bbox
// whose centre IS the centroid, expanded to fully contain the real bbox; the
// fitBounds zoom then derives from this synth extent and the centroid lands
// at the padded viewport centre (i.e. in the upper map area, above the
// bottom-sheet card).
function flyToEventView(
  m: MapLibreMap,
  evt: HistoricalEvent,
  box: [number, number, number, number] | null,
  duration: number,
): void {
  const padding = eventFitPadding()
  const mobile = isMobileViewport()

  if (mobile && box && counties.value) {
    const anchor = getAnchorForEvent(evt, counties.value as FeatureCollection)
    if (anchor) {
      const [west, south, east, north] = box
      const dx = Math.max(anchor[0] - west, east - anchor[0])
      const dy = Math.max(anchor[1] - south, north - anchor[1])
      const synth: [number, number, number, number] = [
        anchor[0] - dx,
        anchor[1] - dy,
        anchor[0] + dx,
        anchor[1] + dy,
      ]
      m.fitBounds(synth, { padding, duration })
      return
    }
  }

  if (box) {
    m.fitBounds(box, { padding, duration })
  } else if (!evt.highlight_fips.length) {
    m.fitBounds([-135, 24, -80, 50], { padding, duration })
  }
}

function setupWatchers() {
  stoppers.push(
    // Push filtered feature array into the records GeoJSON source
    watch(
      visibleRecords,
      features => {
        ;(map?.getSource('records') as GeoJSONSource | undefined)
          ?.setData({ type: 'FeatureCollection', features })
      },
      { immediate: true },
    ),

    // Toggle basemap tile-layer opacity (opacity-transition in the style animates the change).
    // baseLayers is reassigned (LayerPanel spreads into a fresh object) so a shallow watch suffices.
    watch(baseLayers, layers => {
      const both = layers.rand_mcnally && layers.modern
      map?.setPaintProperty('rand_mcnally-layer', 'raster-opacity', layers.rand_mcnally ? (both ? 0.68 : 1) : 0)
      map?.setPaintProperty('modern-layer', 'raster-opacity', layers.modern ? (both ? 0.92 : 1) : 0)
    }),

    // Adjust modern tile appearance when dark mode toggles
    watch(isDark, dark => {
      map?.setPaintProperty('background', 'background-color', dark ? '#1a1a2e' : '#f0ebe0')
      map?.setPaintProperty('modern-layer', 'raster-brightness-max', dark ? 0.12 : 1)
      map?.setPaintProperty('modern-layer', 'raster-contrast', dark ? 0.6 : 0)
      map?.setPaintProperty('modern-layer', 'raster-saturation', dark ? -1 : 0)
      const stroke = dark ? '#ffffff' : '#000000'
      map?.setPaintProperty('records-clusters', 'circle-stroke-color', stroke)
      map?.setPaintProperty('records-unclustered', 'circle-stroke-color', stroke)
    }),

    // Toggle boundary layer visibility. overlays is reassigned wholesale, so a
    // shallow watch on the ref picks up every change without deep traversal.
    watch(overlays, ({ counties: c, states: s }) => {
      map?.setLayoutProperty('counties-outline', 'visibility', c ? 'visible' : 'none')
      map?.setLayoutProperty('states-outline', 'visibility', s ? 'visible' : 'none')
    }),

    // Reset map bearing and pitch to north/flat
    watch(resetNorthSignal, () => {
      map?.easeTo({ bearing: 0, pitch: 0, duration: 600 })
    }),

    // Reset map to default center and zoom
    watch(resetCenterSignal, () => {
      map?.easeTo({ center: [-96, 38.5], zoom: 4, duration: 1200 })
    }),

    // Highlight event and fly to its bounding box
    watch(activeEventId, id => {
      if (!map) return
      if (!id) { clearHighlight(map); return }
      const evt = events.value.find(e => e.id === id)
      if (evt) focusEvent(evt, 600)
    }),
  )
}

// Apply the highlight overlay and fly the camera to an event. Shared by the
// activeEventId watcher (animated) and post-load init (instant).
function focusEvent(evt: HistoricalEvent, duration: number): void {
  if (!map) return
  highlightEvent(map, evt)
  const box = computeEventBbox(evt, counties.value as never)
  flyToEventView(map, evt, box, duration)
}

// ─── map mouse / click handlers ───────────────────────────────────────────────

function setupMapEvents() {
  if (!map) return

  function updatePopupPosition(e: MapMouseEvent): void {
    const original = e.originalEvent
    if (original instanceof MouseEvent) {
      popupPosition.value = { x: original.clientX, y: original.clientY }
      return
    }

    const rect = map!.getCanvas().getBoundingClientRect()
    popupPosition.value = { x: rect.left + e.point.x, y: rect.top + e.point.y }
  }

  map.on('mouseenter', 'records-unclustered', e => {
    map!.getCanvas().style.cursor = 'pointer'
    if (isMobileViewport() || popupPinned.value) return
    const feat = e.features?.[0]
    if (!feat) return
    hoveredRecord.value = feat.properties as RecordProperties
    updatePopupPosition(e)
  })

  map.on('mousemove', 'records-unclustered', e => {
    if (isMobileViewport() || popupPinned.value) return
    const feat = e.features?.[0]
    if (feat) hoveredRecord.value = feat.properties as RecordProperties
    updatePopupPosition(e)
  })

  map.on('mouseleave', 'records-unclustered', () => {
    map!.getCanvas().style.cursor = ''
    if (popupPinned.value) return
    hoveredRecord.value = null
    popupPosition.value = null
  })

  map.on('click', 'records-clusters', async e => {
    if (!props.enableClusterZoom) return
    const feat = e.features?.[0]
    const clusterId = feat?.properties?.cluster_id
    if (clusterId == null) return
    const src = map!.getSource('records') as GeoJSONSource
    const expansionZoom = await src.getClusterExpansionZoom(clusterId)
    // expansionZoom > clusterMaxZoom means the cluster's children are all
    // individual points — this is the final break, so zoom all the way in.
    const isLastBreak = expansionZoom > 8
    const targetZoom = isLastBreak
      ? map!.getMaxZoom()
      : Math.min(map!.getMaxZoom(), Math.max(expansionZoom, Math.floor(map!.getZoom()) + 1))
    map!.easeTo({
      center: (feat!.geometry as GeoJSON.Point).coordinates as [number, number],
      zoom: targetZoom,
      duration: 700,
    })
  })

  map.on('click', 'records-unclustered', e => {
    const feat = e.features?.[0]
    if (!feat) return
    hoveredRecord.value = feat.properties as RecordProperties
    const rect = map!.getCanvas().getBoundingClientRect()
    popupPosition.value = { x: rect.left + e.point.x, y: rect.top + e.point.y }
    popupPinned.value = true
  })

  // Click on empty map area dismisses pinned popup
  map.on('click', e => {
    if (!popupPinned.value) return
    const hits = map!.queryRenderedFeatures(e.point, {
      layers: ['records-unclustered', 'records-clusters'],
    })
    if (!hits.length) dismissPinnedPopup()
  })

  // Pointer cursor on cluster hover
  map.on('mouseenter', 'records-clusters', () => {
    map!.getCanvas().style.cursor = 'pointer'
  })
  map.on('mouseleave', 'records-clusters', () => {
    map!.getCanvas().style.cursor = ''
  })
}

// ─── one-time map-content initialization (called after both map + data ready) ─

function initMapContent() {
  if (!map || !topicTree.value || !counties.value || !states.value) return

  registerSources(map, {
    records: visibleRecords.value,
    counties: counties.value,
    states: states.value,
    topicTree: topicTree.value,
  })

  registerLayers(map, topicTree.value, isDark.value ? '#ffffff' : '#000000')

  setupMapEvents()
  setupWatchers()

  // Apply any initial activeEventId
  if (activeEventId.value) {
    const evt = events.value.find(e => e.id === activeEventId.value)
    if (evt) focusEvent(evt, 0)
  }
}

// ─── lifecycle ────────────────────────────────────────────────────────────────

onMounted(async () => {
  if (import.meta.env.SSR) return
  if (!containerRef.value) return

  map = await createMap(containerRef.value, baseLayers.value, isDark.value)
  mapReady.value = map

  map.on('load', () => {
    // Data may already be loaded (fast connections) or still in flight
    const allReady = () =>
      allRecords.value.length > 0 &&
      topicTree.value !== null &&
      counties.value !== null &&
      states.value !== null

    if (allReady()) {
      initMapContent()
      return
    }

    // Wait for all data refs to become non-null/non-empty
    const stop = watch(
      [allRecords, topicTree, counties, states],
      () => {
        if (!allReady()) return
        stop()
        initMapContent()
      },
    )
  })
})

onUnmounted(() => {
  detachCardObserver()
  stoppers.forEach(s => s())
  map?.remove()
  map = null
  mapReady.value = null
})
</script>

<template>
  <div
    ref="containerRef"
    class="map-canvas"
    :class="{ 'has-event-card': hasEventCard }"
    :style="{ '--map-h': height, '--mobile-card-h': cardHeight + 'px' }"
  >
    <div
      class="map-focus-anchor"
      tabindex="0"
      aria-label="Interactive historical newspaper map"
    />
    <div class="left-stack">
      <LayerPanel />
      <Legend />
    </div>

    <!-- EventMapCard: shown for all active events -->
    <EventMapCard
      v-if="activeEvent && mapReady && containerRef"
      :event="activeEvent"
      :accent-color="getEventAccentColor(activeEvent)"
      :map-instance="mapReady"
      :map-container="containerRef"
      :counties-geo-j-s-o-n="(counties as FeatureCollection)"
      :card-height="cardHeight"
      :event-index="activeEventIndex"
      :event-total="events.length"
      @close="dismissActiveEvent"
      @prev="navigateEvent(-1)"
      @next="navigateEvent(1)"
    />

    <div class="right-stack">
      <MonthCalendar />
      <TimelineAxis />
    </div>

    <RecordPopup
      :record="showPopup ? hoveredRecord : null"
      :position="showPopup ? popupPosition : null"
      @close="dismissPinnedPopup"
    />
    <div v-if="isEmptyState" class="empty-pill">
      No records in {{ displayMonthLabel }} for the selected categories.
    </div>

    <div class="map-attribution">
      <span>© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors</span>
      <span class="attr-sep"> · </span>
      <span><a href="https://collections.leventhalmap.org/search/commonwealth:1257b834v" target="_blank" rel="noopener">Rand McNally (1882)</a>, Leventhal Map & Education Center</span>
    </div>
  </div>
</template>

<style scoped>
.map-canvas {
  position: relative;
  width: 100%;
  height: var(--map-h, 100%);
  overflow: hidden;
  font-family: var(--vp-font-family-base);
}

.map-focus-anchor {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
}

.map-focus-anchor:focus-visible {
  outline: 2px solid var(--vp-c-brand-1);
  outline-offset: -4px;
}

.left-stack {
  position: absolute;
  top: 16px;
  left: 16px;
  bottom: 16px;
  z-index: 5;
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 310px;
  pointer-events: none;
}

@media (max-width: 760px) {
  .left-stack {
    top: 12px;
    left: 12px;
    bottom: 12px;
    /* Cap so an expanded left panel never slides under the right side's
       collapsed 48 px toggle. Reserve: 12 own margin + 48 opposite button +
       12 gap = 72 px on the far side, plus 12 own margin already at left. */
    width: min(310px, calc(100vw - 84px));
  }
}

.right-stack {
  position: absolute;
  top: 16px;
  right: 16px;
  bottom: 16px;
  z-index: 5;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  width: 310px;
  pointer-events: none;
}

@media (max-width: 760px) {
  .right-stack {
    top: 12px;
    right: 12px;
    bottom: 12px;
    /* See .left-stack — same reservation for the left side's collapsed toggle. */
    width: min(310px, calc(100vw - 84px));
  }

  /* When the mobile bottom-sheet event card is on screen, end both stacks
     exactly above the card so expanding Legend / Timeline fills the remaining
     vertical space.  --mobile-card-h is set from a ResizeObserver on the
     card, so this adapts to the card's actual rendered height (capped by
     max-height: 45vh).  The +24px = 12 (card's own bottom margin) + 12 (gap
     between card top and stack bottom). */
  .map-canvas.has-event-card .left-stack,
  .map-canvas.has-event-card .right-stack {
    bottom: calc(var(--mobile-card-h, 0px) + 24px);
  }
}

.empty-pill {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  padding: 8px 16px;
  /* Solid-ish bg instead of backdrop-filter — this badge is small and the
     blur is barely visible, but each backdrop-filter forces a compositing
     layer the GPU has to re-blur on every map redraw. */
  background: color-mix(in oklch, var(--ctp-base), transparent 8%);
  border: 1px solid var(--ctp-surface0);
  border-radius: 999px;
  box-shadow: var(--shadow-1);
  font-size: 13px;
  color: var(--ctp-overlay1);
  pointer-events: none;
  z-index: 4;
}

.map-attribution {
  position: absolute;
  bottom: 0;
  right: 0;
  z-index: 6;
  padding: 0 5px;
  background: rgba(255, 255, 255, 0.7);
  color: #333;
  font-family: system-ui, -apple-system, Arial, sans-serif;
  font-size: 11px;
  line-height: 1.8;
  white-space: nowrap;
  pointer-events: all;
}

.dark .map-attribution {
  background: rgba(0, 0, 0, 0.5);
  color: #ccc;
}

.map-attribution a {
  color: rgba(0, 80, 160, 0.85);
  text-decoration: none;
}

.dark .map-attribution a {
  color: rgba(120, 180, 255, 0.85);
}

.map-attribution a:hover {
  text-decoration: underline;
}

@media (max-width: 760px) {
  .map-attribution {
    white-space: normal;
    font-size: 10px;
    line-height: 1.5;
    text-align: right;
  }

  .map-attribution .attr-sep {
    display: none;
  }

  .map-attribution span:not(.attr-sep) {
    display: block;
    white-space: nowrap;
  }
}
</style>
