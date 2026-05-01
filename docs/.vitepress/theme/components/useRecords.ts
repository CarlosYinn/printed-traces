import { ref, computed, onMounted } from 'vue'
import type { ComputedRef, Ref } from 'vue'
import type { TopicTree, HistoricalEvent, RecordFeature } from './types'
import {
  timeFilter,
  activeCategories,
  activeTopicSolo,
  activeEventId,
  monthRange,
  initActiveCategories,
  initActiveEvents,
} from './useFilters'

// ─── module-level shared state ────────────────────────────────────────────────

export const allRecords: Ref<RecordFeature[]> = ref([])
export const topicTree: Ref<TopicTree | null> = ref(null)
export const events: Ref<HistoricalEvent[]> = ref([])
export const counties: Ref<object | null> = ref(null)
export const states: Ref<object | null> = ref(null)

// ─── derived state ────────────────────────────────────────────────────────────

export const visibleRecords: ComputedRef<RecordFeature[]> = computed(() => {
  const records = allRecords.value
  if (!records.length) return []

  // Resolve the active time window once. Precedence: activeEventId > user
  // timeFilter > embed-only monthRange. We bake the chosen branch into a
  // small set of locals so the per-record loop branches on `===` checks
  // instead of re-deriving filter shape for every feature.
  let exactYm: string | null = null
  let prefix: string | null = null
  let lo: string | null = null
  let hi: string | null = null

  const evtId = activeEventId.value
  if (evtId) {
    const evt = events.value.find(e => e.id === evtId)
    if (evt) [lo, hi] = evt.month_range
  } else {
    const tf = timeFilter.value
    if (tf?.type === 'month') exactYm = tf.ym
    else if (tf?.type === 'year') prefix = String(tf.year)
    else if (monthRange.value) [lo, hi] = monthRange.value
  }

  const cats = activeCategories.value
  const solo = activeTopicSolo.value

  // One filter pass instead of up-to-three: each record is checked once and
  // a single array is allocated. Order the checks cheapest-first so most
  // rejections short-circuit before touching the Set.
  return records.filter(f => {
    const p = f.properties
    const ym = p.year_month
    if (exactYm !== null) { if (ym !== exactYm) return false }
    else if (prefix !== null) { if (!ym.startsWith(prefix)) return false }
    else if (lo !== null) { if (ym < lo || ym > hi!) return false }
    if (solo !== null && p.topic_id !== solo) return false
    return cats.has(p.category)
  })
})

// ─── jitter ───────────────────────────────────────────────────────────────────

// Spread points that share identical coordinates into a small circle so they
// remain individually clickable at high zoom. Offsets are deterministic (index-
// based) so the layout is stable across renders.
function applyJitter(features: RecordFeature[]): RecordFeature[] {
  // Group spatially-close points using a grid bucket (CELL ≈ 29 px at zoom 10).
  // Within each group spread points via a Fermat spiral whose radius scales
  // with sqrt(n) so larger groups get proportionally more room.
  // Base radius: 0.014° gives ~14 px gap for n=2 at zoom 10 (1° ≈ 728 px).
  const CELL = 0.04
  const BASE_R = 0.014
  const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5))

  const buckets = new Map<string, number[]>()
  features.forEach((f, i) => {
    const bx = Math.round(f.geometry.coordinates[0] / CELL)
    const by = Math.round(f.geometry.coordinates[1] / CELL)
    const key = `${bx},${by}`
    const g = buckets.get(key)
    if (g) g.push(i)
    else buckets.set(key, [i])
  })

  const out = features.map(f => ({
    ...f,
    geometry: { ...f.geometry, coordinates: [...f.geometry.coordinates] as [number, number] },
  }))

  for (const indices of buckets.values()) {
    if (indices.length < 2) continue
    const n = indices.length
    const radius = BASE_R * Math.sqrt(n) // scales so all n dots fit without overlap
    // Centre the spiral on the group's centroid
    const cx = indices.reduce((s, i) => s + features[i].geometry.coordinates[0], 0) / n
    const cy = indices.reduce((s, i) => s + features[i].geometry.coordinates[1], 0) / n
    indices.forEach((idx, i) => {
      const angle = i * GOLDEN_ANGLE
      const r = radius * Math.sqrt(i / (n - 1 || 1))
      out[idx].geometry.coordinates[0] = cx + r * Math.cos(angle)
      out[idx].geometry.coordinates[1] = cy + r * Math.sin(angle)
    })
  }

  return out
}

// ─── fetch ────────────────────────────────────────────────────────────────────

let _fetchInitiated = false

function dataUrl(filename: string): string {
  return `${import.meta.env.BASE_URL}data/${filename}`
}

async function loadAll(): Promise<void> {
  if (import.meta.env.SSR) return

  const [recordsRes, topicsRes, eventsRes, countiesRes, statesRes] =
    await Promise.all([
      fetch(dataUrl('records.json')),          // Chronicling America, Library of Congress: https://www.loc.gov/collections/chronicling-america/
      fetch(dataUrl('topics.json')),
      fetch(dataUrl('events.json')),
      fetch(dataUrl('counties_1882.geojson')), // Atlas of Historical County Boundaries, Newberry Library (2012): https://publications.newberry.org/ahcb/
      fetch(dataUrl('states_1882.geojson')),   // Atlas of Historical County Boundaries, Newberry Library (2012): https://publications.newberry.org/ahcb/
    ])

  const [recordsJson, topicsJson, eventsJson, countiesJson, statesJson] =
    await Promise.all([
      recordsRes.json(),
      topicsRes.json(),
      eventsRes.json(),
      countiesRes.json(),
      statesRes.json(),
    ])

  allRecords.value = applyJitter((recordsJson.features ?? []) as RecordFeature[])
  topicTree.value = topicsJson as TopicTree
  events.value = eventsJson as HistoricalEvent[]
  counties.value = countiesJson
  states.value = statesJson

  initActiveCategories(topicsJson as TopicTree)
  initActiveEvents((eventsJson as HistoricalEvent[]).map(event => event.id))
}

// ─── composable ───────────────────────────────────────────────────────────────

export function useRecords() {
  onMounted(async () => {
    if (_fetchInitiated) return
    _fetchInitiated = true
    await loadAll()
  })

  return {
    allRecords,
    topicTree,
    events,
    counties,
    states,
    visibleRecords,
  }
}
