import { bbox, center, featureCollection } from '@turf/turf'
import type { Feature, FeatureCollection } from 'geojson'
import type { Map, StyleSpecification } from 'maplibre-gl'
import type { Category, HistoricalEvent, RecordFeature, TopicTree } from './types'

// ─── cluster helpers (internal) ───

function catKey(name: string) {
  return `n_${name.replace(/\W/g, '_')}`
}

function buildClusterProperties(cats: Category[]): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  for (const cat of cats) {
    out[catKey(cat.name)] = ['+', ['case', ['==', ['get', 'category'], cat.name], 1, 0]]
  }
  return out
}

// Builds a nested ['case', ...] expression that returns the color of whichever
// category has the highest per-cluster count.
function buildDominantColorExpr(cats: Category[]): unknown {
  let expr: unknown = cats[cats.length - 1].color
  for (let i = cats.length - 2; i >= 0; i--) {
    const key = catKey(cats[i].name)
    const beats = cats
      .slice(i + 1)
      .map(c => ['>=', ['get', key], ['get', catKey(c.name)]])
    const cond = beats.length === 1 ? beats[0] : ['all', ...beats]
    expr = ['case', cond, cats[i].color, expr]
  }
  return expr
}

// ─── style helpers ───

// Always registers BOTH tile sources so baseLayer can be toggled by setting
// layer visibility rather than calling setStyle() (which would flush all
// user-added sources and layers).
export interface BaseLayers {
  rand_mcnally: boolean
  modern: boolean
}

function buildStyle(baseLayers: BaseLayers, isDark = false): StyleSpecification {
  const randUrl =
    import.meta.env.VITE_RAND_MCNALLY_TILES ||
    `${import.meta.env.BASE_URL}tiles/{z}/{x}/{y}.png`
  const modernUrl =
    import.meta.env.VITE_MODERN_TILES ||
    'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
  const both = baseLayers.rand_mcnally && baseLayers.modern
  const modernOpacity = baseLayers.modern ? (both ? 0.92 : 1) : 0
  const randOpacity   = baseLayers.rand_mcnally ? (both ? 0.68 : 1) : 0

  return {
    version: 8,
    sources: {
      'rand_mcnally-src': {
        type: 'raster',
        tiles: [randUrl],
        tileSize: 256,
        maxzoom: 8,
      },
      'modern-src': {
        type: 'raster',
        tiles: [modernUrl],
        tileSize: 256,
      },
    },
    layers: [
      {
        id: 'background',
        type: 'background',
        paint: { 'background-color': isDark ? '#1a1a2e' : '#f0ebe0' },
      },
      {
        id: 'modern-layer',
        type: 'raster',
        source: 'modern-src',
        layout: { visibility: 'visible' },
        paint: {
          'raster-opacity': modernOpacity,
          'raster-opacity-transition': { duration: 350, delay: 0 },
          'raster-brightness-max': isDark ? 0.12 : 1,
          'raster-brightness-max-transition': { duration: 300, delay: 0 },
          'raster-contrast': isDark ? 0.6 : 0,
          'raster-contrast-transition': { duration: 300, delay: 0 },
          'raster-saturation': isDark ? -1 : 0,
          'raster-saturation-transition': { duration: 300, delay: 0 },
          // Default 300ms cross-fades each tile as it streams in. During a
          // long fly/ease the GPU spends most frames blending many fading
          // tiles at once and drops frames. 0 means tiles snap in instantly
          // — visually slightly snappier per tile, but the camera animation
          // stays at full framerate, which is the bigger smoothness win.
          'raster-fade-duration': 0,
        },
      },
      {
        id: 'rand_mcnally-layer',
        type: 'raster',
        source: 'rand_mcnally-src',
        layout: { visibility: 'visible' },
        paint: {
          'raster-opacity': randOpacity,
          'raster-opacity-transition': { duration: 350, delay: 0 },
          'raster-fade-duration': 0,
        },
      },
    ],
  }
}

// ─── public API ───

/** Dynamically imports MapLibre and mounts a new map on `container`. */
export async function createMap(
  container: HTMLElement,
  baseLayers: BaseLayers,
  isDark = false,
): Promise<Map> {
  if (import.meta.env.SSR) return null as unknown as Map

  const maplibregl = (await import('maplibre-gl')).default

  const map = new maplibregl.Map({
    container,
    style: buildStyle(baseLayers, isDark),
    center: [-96, 38.5],
    zoom: 4,
    maxZoom: 10,
    minZoom: 2,
    attributionControl: false,
  })

  return map
}

/**
 * Register GeoJSON sources for records (with clustering), counties, and
 * states. topicTree is used to compute per-category cluster counts.
 */
export function registerSources(
  map: Map,
  {
    records,
    counties,
    states,
    topicTree,
  }: {
    records: RecordFeature[]
    counties: object | null
    states: object | null
    topicTree: TopicTree | null
  },
): void {
  if (import.meta.env.SSR) return

  const cats = topicTree?.categories ?? []

  map.addSource('records', {
    type: 'geojson',
    data: { type: 'FeatureCollection', features: records },
    cluster: true,
    clusterRadius: 32,
    clusterMaxZoom: 8,
    clusterProperties: cats.length ? buildClusterProperties(cats) : undefined,
  } as never)

  if (counties) map.addSource('counties', { type: 'geojson', data: counties as never })
  if (states) map.addSource('states', { type: 'geojson', data: states as never })
}

/**
 * Add boundary and record layers.
 * Layer IDs exposed: counties-fill, counties-outline, states-outline,
 * records-clusters, records-cluster-count, records-unclustered.
 */
export function registerLayers(
  map: Map,
  topicTree: TopicTree,
  strokeColor = '#000000',
): void {
  if (import.meta.env.SSR) return

  const cats = topicTree.categories

  if (map.getSource('counties')) {
    map.addLayer({
      id: 'counties-fill',
      type: 'fill',
      source: 'counties',
      paint: { 'fill-color': 'transparent', 'fill-opacity': 0 },
    })
    map.addLayer({
      id: 'counties-outline',
      type: 'line',
      source: 'counties',
      paint: { 'line-color': '#aaa', 'line-width': 0.5, 'line-opacity': 0.7 },
    })
  }

  if (map.getSource('states')) {
    map.addLayer({
      id: 'states-outline',
      type: 'line',
      source: 'states',
      paint: { 'line-color': '#777', 'line-width': 1, 'line-opacity': 0.9 },
    })
  }

  // Highlight layers — always visible, controlled via opacity (not layout.visibility).
  // Using opacity avoids a one-frame flash that occurs when a hidden layer first
  // becomes visible before its filter has been applied by the GPU.
  if (map.getSource('counties')) {
    map.addLayer({
      id: 'event-highlight',
      type: 'fill',
      source: 'counties',
      filter: ['==', ['get', 'FIPS'], ''],
      paint: { 'fill-color': '#e74c3c', 'fill-opacity': 0.28 },
    })
    map.addLayer({
      id: 'event-highlight-outline',
      type: 'line',
      source: 'counties',
      filter: ['==', ['get', 'FIPS'], ''],
      paint: { 'line-color': '#c0392b', 'line-width': 1.2, 'line-opacity': 0.7 },
    })
  }

  if (map.getSource('records')) {
    map.addLayer({
      id: 'records-clusters',
      type: 'circle',
      source: 'records',
      filter: ['has', 'point_count'],
      paint: {
        'circle-color': cats.length
          ? (buildDominantColorExpr(cats) as never)
          : '#6e6e6e',
        'circle-radius': ['step', ['get', 'point_count'], 16, 10, 22, 50, 30],
        'circle-opacity': 0.85,
        'circle-stroke-width': 1.5,
        'circle-stroke-color': strokeColor,
      },
    })

    map.addLayer({
      id: 'records-cluster-count',
      type: 'symbol',
      source: 'records',
      filter: ['has', 'point_count'],
      layout: {
        'text-field': '{point_count_abbreviated}',
        'text-size': 12,
        'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
      },
      paint: { 'text-color': '#fff' },
    })

    map.addLayer({
      id: 'records-unclustered',
      type: 'circle',
      source: 'records',
      filter: ['!', ['has', 'point_count']],
      paint: {
        'circle-color': ['get', 'topic_color'],
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, 3, 8, 5, 10, 7],
        'circle-opacity': ['case', ['to-boolean', ['get', 'is_reprint']], 0.55, 1.0],
        'circle-stroke-width': 1.2,
        'circle-stroke-color': strokeColor,
      },
    })
  }
}

/** Update the highlight overlay for a historical event by switching filter + visibility. */
export function highlightEvent(
  map: Map,
  event: HistoricalEvent,
): void {
  if (import.meta.env.SSR) return
  if (!event.highlight_fips.length) { clearHighlight(map); return }

  const filter: unknown[] =
    event.highlight_level === 'county'
      ? ['match', ['get', 'FIPS'], event.highlight_fips, true, false]
      : [
          'match',
          ['slice', ['to-string', ['get', 'FIPS']], 0, 2],
          [...new Set(event.highlight_fips.map(f => f.slice(0, 2)))],
          true,
          false,
        ]

  for (const id of ['event-highlight', 'event-highlight-outline'] as const) {
    if (map.getLayer(id)) map.setFilter(id, filter as never)
  }
}

/** Hide the highlight layers by resetting to the empty filter. */
export function clearHighlight(map: Map): void {
  if (import.meta.env.SSR) return
  const empty = ['==', ['get', 'FIPS'], ''] as never
  if (map.getLayer('event-highlight')) map.setFilter('event-highlight', empty)
  if (map.getLayer('event-highlight-outline')) map.setFilter('event-highlight-outline', empty)
}

/**
 * Compute the WGS-84 bounding box [minLng, minLat, maxLng, maxLat] for a
 * historical event's geographic extent, or null if no features are matched.
 *
 * County-level events: exact match on properties.FIPS.
 * State-level events:  highlight_fips are 5-digit county FIPS; we expand to
 *   every county sharing the same 2-char state prefix for a full-state bbox.
 *   The states layer carries no FIPS field, so county geometries source the
 *   bbox in both branches.
 */
export function computeEventBbox(
  event: HistoricalEvent,
  countiesGeojson: FeatureCollection,
): [number, number, number, number] | null {
  if (import.meta.env.SSR) return null
  if (!event.highlight_fips.length) return null

  const fipsSet = new Set(event.highlight_fips)
  let matched: Feature[]

  if (event.highlight_level === 'state') {
    const prefixes = new Set([...fipsSet].map(f => f.slice(0, 2)))
    matched = countiesGeojson.features.filter(f => {
      const fips = f.properties?.FIPS as string | null
      return fips != null && prefixes.has(fips.slice(0, 2))
    })
  } else {
    matched = countiesGeojson.features.filter(f =>
      fipsSet.has(f.properties?.FIPS as string),
    )
  }

  if (!matched.length) return null

  return bbox(featureCollection(matched)) as [number, number, number, number]
}

/** Derive state/territory abbreviations touched by an event's FIPS list. */
export function getEventStateAbbreviations(
  event: HistoricalEvent,
  countiesGeojson: FeatureCollection | null,
): string[] {
  if (!countiesGeojson || !event.highlight_fips.length) return []

  const fipsSet = new Set(event.highlight_fips)
  const statePrefixes =
    event.highlight_level === 'state'
      ? new Set(event.highlight_fips.map(f => f.slice(0, 2)))
      : null

  const abbreviations = new Set<string>()

  for (const feature of countiesGeojson.features) {
    const fips = feature.properties?.FIPS as string | null
    if (!fips) continue

    const matches =
      statePrefixes !== null
        ? statePrefixes.has(fips.slice(0, 2))
        : fipsSet.has(fips)

    if (!matches) continue

    const abbr = feature.properties?.state_abbr as string | null
    if (abbr) abbreviations.add(abbr)
  }

  return [...abbreviations].sort()
}

/** Return the geographic centre of an event's highlighted FIPS features,
 *  or null if the event has no location data.
 *
 *  Matches the same FIPS resolution rules as computeEventBbox /
 *  getEventStateAbbreviations: state-level events expand to all counties
 *  sharing the 2-digit prefix; county-level events match the full 5-digit FIPS. */
export function getAnchorForEvent(
  event: HistoricalEvent,
  countiesGeoJSON: FeatureCollection,
): [number, number] | null {
  if (!event.highlight_fips.length) return null

  const fipsSet = new Set(event.highlight_fips)
  const statePrefixes =
    event.highlight_level === 'state'
      ? new Set(event.highlight_fips.map(f => f.slice(0, 2)))
      : null

  const matched = countiesGeoJSON.features.filter(f => {
    const fips = f.properties?.FIPS as string | null
    if (!fips) return false
    return statePrefixes !== null
      ? statePrefixes.has(fips.slice(0, 2))
      : fipsSet.has(fips)
  })
  if (!matched.length) return null

  const c = center({ type: 'FeatureCollection', features: matched })
  return c.geometry.coordinates as [number, number]
}
