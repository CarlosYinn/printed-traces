<script setup lang="ts">
import { computed, watch, onUnmounted } from 'vue'
import { timeFilter, setTimeFilter, activeEventId, activeCategories } from './useFilters'
import { allRecords } from './useRecords'
import { MONTHS, monthToIndex } from './useMonthIndex'
import { useResponsivePanel } from './useResponsivePanel'
import { isPlaying } from './usePlayback'

const { isOpen } = useResponsivePanel()

const categoryFilteredRecords = computed(() =>
  allRecords.value.filter(f => activeCategories.value.has(f.properties.category))
)

const densityMap = computed<Map<string, number>>(() => {
  const map = new Map<string, number>()
  for (const f of categoryFilteredRecords.value) {
    const ym = f.properties.year_month
    map.set(ym, (map.get(ym) ?? 0) + 1)
  }
  return map
})

function getCount(ym: string): number {
  return densityMap.value.get(ym) ?? 0
}

const YEARS = [1880, 1881, 1882, 1883, 1884, 1885]
const MONTH_NUMBERS = Array.from({ length: 12 }, (_, i) => i + 1)
const currentMonth = computed(() => {
  const tf = timeFilter.value
  if (tf?.type === 'month') return tf.ym
  if (tf?.type === 'year') return `${tf.year}-01`
  return '1880-01'
})
const currentYear = computed(() => Number(currentMonth.value.slice(0, 4)))
const currentMonthNumber = computed(() => Number(currentMonth.value.slice(5, 7)))
const currentCount = computed(() =>
  timeFilter.value ? getCount(currentMonth.value) : categoryFilteredRecords.value.length
)

const displayLabel = computed(() => {
  const tf = timeFilter.value
  if (!tf) return 'All months'
  if (tf.type === 'year') return String(tf.year)
  return tf.ym
})

function wheelItemStyle(offset: number): Record<string, number> {
  const distance = Math.abs(offset)
  return {
    '--offset': offset,
    '--fade': Math.max(0.18, 1 - distance * 0.24),
    '--scale': Math.max(0.72, 1 - distance * 0.08),
  }
}

const yearItems = computed(() =>
  YEARS.map(year => ({
    value: year,
    style: wheelItemStyle(year - currentYear.value),
  })),
)

const monthItems = computed(() =>
  MONTH_NUMBERS.map(month => ({
    value: month,
    style: wheelItemStyle(month - currentMonthNumber.value),
  })),
)

let timer: ReturnType<typeof setInterval> | null = null

watch(isPlaying, playing => {
  if (!playing && timer) { clearInterval(timer); timer = null }
})
let dragState: {
  kind: 'year' | 'month'
  startY: number
  lastStep: number
  pointerId: number
  moved: boolean
} | null = null

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}

function setPickerMonth(year = currentYear.value, month = currentMonthNumber.value): void {
  const y = clamp(year, YEARS[0], YEARS[YEARS.length - 1])
  const m = clamp(month, 1, 12)
  const ym = `${y}-${String(m).padStart(2, '0')}`
  setTimeFilter({ type: 'month', ym })
  activeEventId.value = null
}

function shiftYear(delta: number): void {
  setPickerMonth(currentYear.value + delta, currentMonthNumber.value)
}

function shiftMonth(delta: number): void {
  setPickerMonth(currentYear.value, currentMonthNumber.value + delta)
}

function clearMonthFilter(): void {
  setTimeFilter(null)
  activeEventId.value = null
}

function handleWheel(kind: 'year' | 'month', event: WheelEvent): void {
  event.preventDefault()
  const magnitude = Math.abs(event.deltaY)
  const steps = magnitude > 120 ? Math.round(magnitude / 80) : 1
  const delta = event.deltaY > 0 ? steps : -steps
  kind === 'year' ? shiftYear(delta) : shiftMonth(delta)
}

function shiftWheel(kind: 'year' | 'month', delta: number): void {
  kind === 'year' ? shiftYear(delta) : shiftMonth(delta)
}

function handlePointerDown(kind: 'year' | 'month', event: PointerEvent): void {
  if (event.button !== 0) return
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
  dragState = {
    kind,
    startY: event.clientY,
    lastStep: 0,
    pointerId: event.pointerId,
    moved: false,
  }
}

function handlePointerMove(event: PointerEvent): void {
  if (!dragState || dragState.pointerId !== event.pointerId) return
  const rowHeight = 36
  const step = Math.trunc((event.clientY - dragState.startY) / rowHeight)
  if (step === dragState.lastStep) return
  const delta = dragState.lastStep - step
  dragState.lastStep = step
  dragState.moved = true
  shiftWheel(dragState.kind, delta)
}

function handlePointerUp(event: PointerEvent): void {
  if (!dragState || dragState.pointerId !== event.pointerId) return
  const target = event.currentTarget as HTMLElement
  if (target.hasPointerCapture(event.pointerId)) target.releasePointerCapture(event.pointerId)
  window.setTimeout(() => { dragState = null }, 0)
}

function handlePointerCancel(event: PointerEvent): void {
  if (!dragState || dragState.pointerId !== event.pointerId) return
  dragState = null
}

function handleItemClick(kind: 'year' | 'month', value: number): void {
  if (dragState?.moved) return
  kind === 'year'
    ? setPickerMonth(value, currentMonthNumber.value)
    : setPickerMonth(currentYear.value, value)
}

function handleColumnClick(kind: 'year' | 'month', event: MouseEvent): void {
  if (dragState?.moved) return
  if ((event.target as HTMLElement).closest('.wheel-item')) return

  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const center = rect.top + rect.height / 2
  const deadZone = 21
  const delta = event.clientY < center - deadZone ? -1 : event.clientY > center + deadZone ? 1 : 0
  if (delta === 0) return

  shiftWheel(kind, delta)
}

function handleKeydown(kind: 'year' | 'month', e: KeyboardEvent): void {
  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault()
      kind === 'year' ? shiftYear(1) : shiftMonth(1)
      break
    case 'ArrowUp':
      e.preventDefault()
      kind === 'year' ? shiftYear(-1) : shiftMonth(-1)
      break
    case 'Home':
      e.preventDefault()
      kind === 'year' ? setPickerMonth(YEARS[0]) : setPickerMonth(currentYear.value, 1)
      break
    case 'End':
      e.preventDefault()
      kind === 'year'
        ? setPickerMonth(YEARS[YEARS.length - 1])
        : setPickerMonth(currentYear.value, 12)
      break
  }
}

function stopPlay(): void {
  isPlaying.value = false
  if (timer) { clearInterval(timer); timer = null }
}

function startPlay(): void {
  isPlaying.value = true
  activeEventId.value = null
  const tf = timeFilter.value
  const currentYm = tf?.type === 'month' ? tf.ym : null
  if (!currentYm || currentYm === '1885-12') {
    setPickerMonth(1880, 1)
  }
  timer = setInterval(() => {
    const cur = timeFilter.value
    const ym = cur?.type === 'month' ? cur.ym : null
    const idx = monthToIndex(ym)
    if (idx === -1 || idx >= MONTHS.length - 1) { stopPlay(); return }
    const next = MONTHS[idx + 1]
    setTimeFilter({ type: 'month', ym: next })
  }, 600)
}

function togglePlay(): void {
  isPlaying.value ? stopPlay() : startPlay()
}

onUnmounted(stopPlay)
</script>

<template>
  <div
    class="cal-panel"
    :class="{ 'is-collapsed': !isOpen }"
    role="region"
    aria-label="Month calendar controls"
  >
    <button
      class="panel-toggle"
      :aria-expanded="isOpen"
      :aria-label="isOpen ? 'Collapse date filter' : 'Expand date filter'"
      @click="isOpen = !isOpen"
    >
      ⊡
    </button>
    <div class="panel-bar">
      <span v-if="isOpen" class="panel-label">Date filter</span>
    </div>

    <div class="panel-body" :class="{ 'is-hidden': !isOpen }">
      <div class="cal-top-row">
        <div class="cal-status">
          <span class="cal-title">{{ displayLabel }}</span>
          <span class="cal-sep" aria-hidden="true">·</span>
          <span class="cal-count">{{ currentCount }} records</span>
        </div>

        <div class="cal-actions">
          <button
            type="button"
            class="ctrl-btn"
            :class="{ 'is-active': !timeFilter }"
            aria-label="Show records from all months"
            @click="clearMonthFilter"
          >
            All
          </button>
          <button
            type="button"
            class="ctrl-btn"
            :aria-label="isPlaying ? 'Pause playback' : 'Play month-by-month'"
            @click="togglePlay"
          >
            {{ isPlaying ? 'Pause' : 'Play' }}
          </button>
        </div>
      </div>

      <div class="wheel-picker" aria-label="Month selector 1880-1885">
        <div
          class="wheel-column"
          tabindex="0"
          role="listbox"
          aria-label="Select year"
          :aria-activedescendant="`year-${currentYear}`"
          @wheel="handleWheel('year', $event)"
          @keydown="handleKeydown('year', $event)"
          @pointerdown="handlePointerDown('year', $event)"
          @pointermove="handlePointerMove"
          @pointerup="handlePointerUp"
          @pointercancel="handlePointerCancel"
          @click="handleColumnClick('year', $event)"
        >
          <button
            v-for="item in yearItems"
            :id="`year-${item.value}`"
            :key="item.value"
            type="button"
            role="option"
            class="wheel-item"
            :class="{ 'is-selected': item.value === currentYear }"
            :aria-selected="item.value === currentYear"
            :style="item.style"
            @click.stop="handleItemClick('year', item.value)"
          >
            {{ item.value }}
          </button>
        </div>

        <div
          class="wheel-column"
          tabindex="0"
          role="listbox"
          aria-label="Select month"
          :aria-activedescendant="`month-${currentMonthNumber}`"
          @wheel="handleWheel('month', $event)"
          @keydown="handleKeydown('month', $event)"
          @pointerdown="handlePointerDown('month', $event)"
          @pointermove="handlePointerMove"
          @pointerup="handlePointerUp"
          @pointercancel="handlePointerCancel"
          @click="handleColumnClick('month', $event)"
        >
          <button
            v-for="item in monthItems"
            :id="`month-${item.value}`"
            :key="item.value"
            type="button"
            role="option"
            class="wheel-item"
            :class="{ 'is-selected': item.value === currentMonthNumber }"
            :aria-selected="item.value === currentMonthNumber"
            :style="item.style"
            :title="`${currentYear}-${String(item.value).padStart(2, '0')} · ${getCount(`${currentYear}-${String(item.value).padStart(2, '0')}`)} records`"
            @click.stop="handleItemClick('month', item.value)"
          >
            {{ String(item.value).padStart(2, '0') }}
          </button>
        </div>

        <div class="wheel-highlight" aria-hidden="true" />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── Panel shell ─────────────────────────────────────────────────────────── */

.cal-panel {
  position: relative;
  pointer-events: all;
  flex-shrink: 0;
  width: 100%;
  max-height: calc(100vh - 32px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: color-mix(in oklch, var(--ctp-base), transparent 6%);
  border: 1px solid var(--ctp-surface0);
  border-radius: 14px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.10);
  transition:
    width var(--dur-std) var(--ease-std),
    max-height var(--dur-std) var(--ease-std);
}

.cal-panel.is-collapsed {
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
  opacity: 1;
  pointer-events: all;
  transition: opacity var(--dur-std) var(--ease-std);
}

.panel-body.is-hidden {
  opacity: 0;
  pointer-events: none;
}

/* ── Header label ────────────────────────────────────────────────────────── */

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

/* ── Status row ──────────────────────────────────────────────────────────── */

.cal-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 28px;
  margin-bottom: 10px;
  padding-left: 3px;
}

.cal-status {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  height: 28px;
}

.cal-title {
  overflow: hidden;
  color: var(--ctp-text);
  font-family: Cambria, Georgia, serif;
  font-size: 0.98rem;
  font-weight: 700;
  line-height: 28px;
  font-variant-numeric: tabular-nums;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cal-sep,
.cal-count {
  color: var(--ctp-overlay1);
  font-size: 0.7rem;
  font-weight: 600;
  line-height: 28px;
  white-space: nowrap;
}

/* ── Action buttons ──────────────────────────────────────────────────────── */

.cal-actions {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
  gap: 5px;
  height: 28px;
}

.ctrl-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 45px;
  height: 28px;
  padding: 0 9px;
  white-space: nowrap;
  border: 1px solid transparent;
  border-radius: 5px;
  background: color-mix(in oklch, var(--ctp-surface1), transparent 40%);
  color: var(--ctp-subtext1);
  font-family: Cambria, Georgia, serif;
  font-size: 0.86rem;
  line-height: 1;
  text-align: center;
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

.ctrl-btn.is-active {
  border-color: var(--vp-c-brand-1);
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
}

/* ── Wheel picker ────────────────────────────────────────────────────────── */

.wheel-picker {
  --wheel-row: 30px;
  --wheel-height: 138px;
  position: relative;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  height: var(--wheel-height);
  padding: 10px;
  overflow: hidden;
  border: 1px solid color-mix(in oklch, var(--ctp-surface2), transparent 18%);
  border-radius: 10px;
  background:
    linear-gradient(
      135deg,
      color-mix(in oklch, var(--ctp-surface2), transparent 70%),
      transparent 24% 72%,
      color-mix(in oklch, var(--ctp-crust), transparent 35%)
    ),
    color-mix(in oklch, var(--ctp-mantle), transparent 8%);
  box-shadow:
    inset 0 1px 0 color-mix(in oklch, var(--ctp-text), transparent 88%),
    0 1px 0 color-mix(in oklch, var(--ctp-base), transparent 35%);
  cursor: grab;
}

.wheel-picker::before,
.wheel-picker::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  z-index: 3;
  height: 34%;
  pointer-events: none;
}

.wheel-picker::before {
  top: 0;
  background: linear-gradient(
    to bottom,
    color-mix(in oklch, var(--ctp-mantle), transparent 0%) 0%,
    color-mix(in oklch, var(--ctp-mantle), transparent 18%) 42%,
    transparent 100%
  );
}

.wheel-picker::after {
  bottom: 0;
  background: linear-gradient(
    to top,
    color-mix(in oklch, var(--ctp-mantle), transparent 0%) 0%,
    color-mix(in oklch, var(--ctp-mantle), transparent 18%) 42%,
    transparent 100%
  );
}

.wheel-highlight {
  position: absolute;
  left: 16px;
  right: 16px;
  top: 50%;
  z-index: 5;
  height: 42px;
  transform: translateY(-50%);
  pointer-events: none;
  border: 1px solid color-mix(in oklch, var(--vp-c-brand-1), transparent 44%);
  border-radius: 6px;
  background:
    linear-gradient(
      to bottom,
      color-mix(in oklch, var(--ctp-base), transparent 84%),
      transparent 46% 54%,
      color-mix(in oklch, var(--ctp-crust), transparent 72%)
    );
  box-shadow:
    inset 0 1px 0 color-mix(in oklch, var(--ctp-text), transparent 86%),
    inset 0 -1px 0 color-mix(in oklch, var(--ctp-crust), transparent 20%),
    0 0 0 1px color-mix(in oklch, var(--vp-c-brand-1), transparent 76%);
}

/* ── Wheel columns ───────────────────────────────────────────────────────── */

.wheel-column {
  position: relative;
  z-index: 2;
  overflow: hidden;
  outline: none;
  cursor: grab;
  touch-action: none;
  border: 1px solid color-mix(in oklch, var(--ctp-surface1), transparent 16%);
  border-radius: 8px;
  background:
    radial-gradient(
      ellipse at 50% 50%,
      color-mix(in oklch, var(--ctp-base), transparent 68%) 0 18%,
      transparent 48%
    ),
    linear-gradient(
      to right,
      color-mix(in oklch, var(--ctp-crust), transparent 18%),
      color-mix(in oklch, var(--ctp-mantle), transparent 28%) 18% 82%,
      color-mix(in oklch, var(--ctp-crust), transparent 18%)
    );
  box-shadow:
    inset 0 0 0 1px color-mix(in oklch, var(--ctp-base), transparent 72%);
}

.wheel-item {
  position: absolute;
  top: 50%;
  left: 12px;
  width: calc(100% - 24px);
  height: var(--wheel-row);
  padding: 0;
  border: none;
  background: transparent;
  color: color-mix(in oklch, var(--ctp-overlay2), transparent 8%);
  font-family: Cambria, Georgia, serif;
  font-size: 1rem;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  line-height: var(--wheel-row);
  text-align: center;
  cursor: grab;
  opacity: var(--fade);
  transform:
    translateY(calc((var(--offset) * var(--wheel-row)) - 50%))
    scale(var(--scale));
  transition:
    color var(--dur-std) var(--ease-std),
    opacity var(--dur-std) var(--ease-std),
    transform var(--dur-std) var(--ease-std);
}

.wheel-picker:active,
.wheel-picker:active .wheel-column,
.wheel-picker:active .wheel-item {
  cursor: grabbing;
}

.wheel-item.is-selected {
  z-index: 7;
  color: var(--ctp-text);
  font-size: 1.42rem;
  font-weight: 700;
  opacity: 1;
}

/* ── Focus rings ─────────────────────────────────────────────────────────── */

button:focus-visible,
.wheel-column:focus-visible {
  outline: 2px solid var(--vp-c-brand-1);
  outline-offset: -2px;
  border-radius: 6px;
}

@media (max-width: 760px) {
  .cal-panel {
    width: 100%;
  }
}
</style>
