<script setup lang="ts">
import { ref, shallowRef, computed, watch, onMounted, onUnmounted } from 'vue'
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
} from './useMap'
import {
  timeFilter,
  setTimeFilter,
  baseLayers,
  overlays,
  activeEventId,
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
import type { RecordProperties } from './types'

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
const popupPinned = ref(false) // true when opened by tap on mobile

function isMobile(): boolean {
  return window.matchMedia('(pointer: coarse)').matches || window.innerWidth < 768
}

function dismissPinnedPopup() {
  hoveredRecord.value = null
  popupPosition.value = null
  popupPinned.value = false
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

    // Toggle basemap tile-layer opacity (opacity-transition in the style animates the change)
    watch(baseLayers, layers => {
      const dark = isDark.value
      const both = layers.rand_mcnally && layers.modern
      map?.setPaintProperty('rand_mcnally-layer', 'raster-opacity', layers.rand_mcnally ? (both ? 0.68 : 1) : 0)
      map?.setPaintProperty('modern-layer', 'raster-opacity', layers.modern ? (both ? 0.92 : 1) : 0)
      map?.setPaintProperty('modern-layer', 'raster-brightness-max', dark ? 0.06 : 1)
      map?.setPaintProperty('modern-layer', 'raster-contrast', dark ? 0.6 : 0)
      map?.setPaintProperty('modern-layer', 'raster-saturation', dark ? -1 : 0)
    }, { deep: true }),

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

    // Toggle boundary layer visibility
    watch(
      overlays,
      ({ counties: c, states: s }) => {
        map?.setLayoutProperty('counties-outline', 'visibility', c ? 'visible' : 'none')
        map?.setLayoutProperty('states-outline', 'visibility', s ? 'visible' : 'none')
      },
      { deep: true },
    ),

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
      if (!evt) return
      highlightEvent(map, evt)
      const box = computeEventBbox(
        evt,
        counties.value as never,
        states.value as never,
      )
      if (box) {
        map.fitBounds(box, { padding: { top: 60, bottom: 60, left: 60, right: 300 }, duration: 600 })
      } else if (!evt.highlight_fips.length) {
        map.fitBounds([-135, 24, -80, 50], { padding: { top: 60, bottom: 60, left: 60, right: 300 }, duration: 600 })
      }
    }),
  )
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
    if (isMobile() || popupPinned.value) return
    const feat = e.features?.[0]
    if (!feat) return
    hoveredRecord.value = feat.properties as RecordProperties
    updatePopupPosition(e)
  })

  map.on('mousemove', 'records-unclustered', e => {
    if (isMobile() || popupPinned.value) return
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
    if (evt) {
      highlightEvent(map!, evt)
      const box = computeEventBbox(evt, counties.value as never, states.value as never)
      if (box) map!.fitBounds(box, { padding: 60, duration: 0 })
    }
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
  stoppers.forEach(s => s())
  map?.remove()
  map = null
  mapReady.value = null
})
</script>

<template>
  <div ref="containerRef" class="map-canvas" :style="{ '--map-h': height }">
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
      @close="activeEventId = null; setTimeFilter(null)"
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
    width: min(310px, calc(100vw - 24px));
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
    width: min(310px, calc(100vw - 24px));
  }
}

.empty-pill {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  padding: 8px 16px;
  background: color-mix(in oklch, var(--ctp-base), transparent 20%);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
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
    max-width: 60%;
    text-align: right;
    font-size: 10px;
    line-height: 1.5;
  }

  .map-attribution .attr-sep {
    display: none;
  }

  .map-attribution span:not(.attr-sep) {
    display: block;
  }
}
</style>
