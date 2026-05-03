import { ref, computed, watch } from 'vue'
import type { TopicTree } from './types'
import { MONTHS } from './useMonthIndex'

// ─── time filter type ───

export type TimeFilter =
  | { type: 'year'; year: number }
  | { type: 'month'; ym: string }
  | null

// ─── opening state ───

export const DEFAULT_OPENING_STATE = {
  activeEventId: null as string | null,
  baseLayers: {
    rand_mcnally: false,
    modern: true,
  },
}

// ─── module-level shared state ───

export const timeFilter = ref<TimeFilter>(null)
export const activeCategories = ref<Set<string>>(new Set())
export const activeTopicSolo = ref<string | null>(null)
export const activeEventId = ref<string | null>(DEFAULT_OPENING_STATE.activeEventId)
export const baseLayers = ref({ ...DEFAULT_OPENING_STATE.baseLayers })
export const overlays = ref({ counties: true, states: true })

/** Embed-mode range constraint — never mutated by user interaction */
export const monthRange = ref<[string, string] | null>(null)

/** Read-only: the exact month string when a month filter is active, null otherwise */
export const selectedMonth = computed<string | null>(() =>
  timeFilter.value?.type === 'month' ? timeFilter.value.ym : null
)

// ─── public mutator ───

export function setTimeFilter(filter: TimeFilter): void {
  timeFilter.value = filter
}

/** Dismiss the active event card and the month-filter it set. */
export function dismissActiveEvent(): void {
  activeEventId.value = null
  timeFilter.value = null
}

// ─── internal helpers ───

let _topicTree: TopicTree | null = null
let _urlTimer: ReturnType<typeof setTimeout> | null = null
let _urlSyncStarted = false
let _syncingFromUrl = false
let _pendingCategoryNames: string[] | null = null
let _activeEventIds: Set<string> | null = null

function deriveActiveCategories(tree: TopicTree): Set<string> {
  return new Set(
    tree.categories
      .filter(cat => cat.topics.some(t => !t.exclude))
      .map(cat => cat.name),
  )
}

function getDefaultCategoryNames(): string[] {
  return _topicTree ? [...deriveActiveCategories(_topicTree)].sort() : []
}

function categorySlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/&/g, ' and ')
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
}

function categoriesAreDefault(names: string[]): boolean {
  const defaults = getDefaultCategoryNames()
  return defaults.length > 0 &&
    defaults.length === names.length &&
    defaults.every((name, index) => name === names[index])
}

function parseHashParams(): URLSearchParams | null {
  if (typeof window === 'undefined') return null
  const raw = window.location.hash.replace(/^#/, '')
  return raw ? new URLSearchParams(raw) : new URLSearchParams()
}

function isValidMonth(value: string | null): value is string {
  return value !== null && MONTHS.includes(value)
}



function isValidEventId(value: string | null): value is string {
  if (!value || !/^[a-z0-9_-]+$/i.test(value)) return false
  return _activeEventIds === null || _activeEventIds.has(value)
}

function sanitizeCategories(raw: string | null): string[] | null {
  if (!raw) return null
  const tokens = raw
    .split(',')
    .map(name => name.trim())
    .filter(Boolean)

  if (!tokens.length) return null

  if (!_topicTree) return [...new Set(tokens)].sort()

  const validNames = getDefaultCategoryNames()
  const valid = new Map<string, string>()
  for (const name of validNames) {
    valid.set(name, name)
    valid.set(categorySlug(name), name)
  }

  const filtered = [...new Set(tokens.map(token => valid.get(token)).filter(Boolean) as string[])].sort()
  return filtered.length ? filtered : null
}

// ─── public API ───

/** Called by useRecords after topics.json is loaded. */
export function initActiveCategories(tree: TopicTree): void {
  _topicTree = tree
  const categories = sanitizeCategories(_pendingCategoryNames?.join(',') ?? null)
  activeCategories.value = categories ? new Set(categories) : deriveActiveCategories(tree)
  _pendingCategoryNames = null
}

export function initActiveEvents(eventIds: string[]): void {
  _activeEventIds = new Set(eventIds)
  if (activeEventId.value && !_activeEventIds.has(activeEventId.value)) {
    activeEventId.value = DEFAULT_OPENING_STATE.activeEventId
  }
}

/** Toggle a category filter, assigning a fresh Set so Vue subscribers update. */
export function toggleCategory(name: string): void {
  const next = new Set(activeCategories.value)
  next.has(name) ? next.delete(name) : next.add(name)
  activeCategories.value = next
}

/** Reset all filters to their initial defaults. */
export function resetFilters(): void {
  timeFilter.value = null
  activeTopicSolo.value = null
  activeEventId.value = DEFAULT_OPENING_STATE.activeEventId
  baseLayers.value = { ...DEFAULT_OPENING_STATE.baseLayers }
  overlays.value = { counties: true, states: true }
  monthRange.value = null
  if (_topicTree) activeCategories.value = deriveActiveCategories(_topicTree)
}

export interface InitialProps {
  initialMonth?: string
  monthRange?: [string, string]
  initialCategories?: string[]
  initialEventId?: string
  initialBaseLayer?: 'rand_mcnally' | 'modern' | 'blank'
}

/** Apply embed-mode overrides before the map mounts. */
export function applyInitialProps(props: InitialProps): void {
  timeFilter.value = props.initialMonth
    ? { type: 'month', ym: props.initialMonth }
    : null
  activeEventId.value = props.initialEventId ?? DEFAULT_OPENING_STATE.activeEventId
  baseLayers.value =
    props.initialBaseLayer === 'modern'
      ? { rand_mcnally: false, modern: true }
      : props.initialBaseLayer === 'blank'
        ? { rand_mcnally: false, modern: false }
        : { ...DEFAULT_OPENING_STATE.baseLayers }
  if (props.monthRange !== undefined) monthRange.value = props.monthRange
  if (props.initialCategories !== undefined)
    activeCategories.value = new Set(props.initialCategories)
}

export function syncFromUrl(): void {
  if (typeof window === 'undefined') return

  const params = parseHashParams()
  if (!params) return

  _syncingFromUrl = true

  const t = params.get('t')
  if (t && /^\d{4}$/.test(t)) {
    const y = Number(t)
    const minY = Number(MONTHS[0].slice(0, 4))
    const maxY = Number(MONTHS[MONTHS.length - 1].slice(0, 4))
    if (y >= minY && y <= maxY) timeFilter.value = { type: 'year', year: y }
  } else if (isValidMonth(t)) {
    timeFilter.value = { type: 'month', ym: t }
  }

  const eventId = params.get('e')
  if (isValidEventId(eventId)) activeEventId.value = eventId

  const categories = sanitizeCategories(params.get('c'))
  if (categories) {
    _pendingCategoryNames = categories
    activeCategories.value = new Set(categories)
  }

  _syncingFromUrl = false
}

export function syncToUrl(): void {
  if (typeof window === 'undefined') return

  const params = new URLSearchParams()
  const tf = timeFilter.value
  if (tf?.type === 'year') params.set('t', String(tf.year))
  else if (tf?.type === 'month') params.set('t', tf.ym)

  const categoryNames = [...activeCategories.value].sort()
  if (categoryNames.length && !categoriesAreDefault(categoryNames)) {
    params.set('c', categoryNames.map(categorySlug).join(','))
  }

  if (activeEventId.value) params.set('e', activeEventId.value)

  const nextHash = params.toString()
  const nextUrl = `${window.location.pathname}${window.location.search}${nextHash ? `#${nextHash}` : ''}`
  window.history.replaceState(window.history.state, '', nextUrl)
}

export function startUrlSync(): () => void {
  if (typeof window === 'undefined' || _urlSyncStarted) return () => {}

  _urlSyncStarted = true

  const stop = watch(
    [timeFilter, activeCategories, activeEventId],
    () => {
      if (_syncingFromUrl) return
      if (_urlTimer) clearTimeout(_urlTimer)
      _urlTimer = setTimeout(() => {
        _urlTimer = null
        syncToUrl()
      }, 150)
    },
    { deep: false },
  )

  return () => {
    stop()
    _urlSyncStarted = false
    if (_urlTimer) {
      clearTimeout(_urlTimer)
      _urlTimer = null
    }
  }
}
