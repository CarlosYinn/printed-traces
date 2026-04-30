<script setup lang="ts">
import { baseLayers, overlays } from './useFilters'
import { useResponsivePanel } from './useResponsivePanel'
import { triggerResetNorth, triggerResetCenter } from './useMapControls'

const { isOpen } = useResponsivePanel('left')

function toggleOverlay(key: 'counties' | 'states') {
  overlays.value = { ...overlays.value, [key]: !overlays.value[key] }
}

function toggleBaseLayer(key: 'rand_mcnally' | 'modern') {
  baseLayers.value = { ...baseLayers.value, [key]: !baseLayers.value[key] }
}
</script>

<template>
  <div
    class="layer-panel"
    :class="{ 'is-collapsed': !isOpen }"
    role="region"
    aria-label="Map layer controls"
  >
    <div class="panel-bar">
      <button
        class="panel-toggle"
        :aria-expanded="isOpen"
        :aria-label="isOpen ? 'Collapse layer panel' : 'Expand layer panel'"
        @click="isOpen = !isOpen"
      >
        ⊞
      </button>
      <template v-if="isOpen">
        <span class="panel-label">Basemap</span>
        <button
          class="reset-north-btn"
          aria-label="Reset map to center"
          title="Reset to center"
          @click="triggerResetCenter"
        >
          Central
        </button>
        <button
          class="reset-north-btn"
          aria-label="Reset map to north"
          title="Reset north"
          @click="triggerResetNorth"
        >
          N ↑
        </button>
      </template>
    </div>

    <div class="panel-body" :class="{ 'is-hidden': !isOpen }">
      <!-- ── Basemap ── -->
      <fieldset class="panel-fieldset">
        <div class="check-list">
          <label class="check-row">
            <input
              type="checkbox"
              class="check-input"
              :checked="baseLayers.modern"
              @change="toggleBaseLayer('modern')"
            />
            <span class="check-label">Modern overlay</span>
          </label>
          <label class="check-row">
            <input
              type="checkbox"
              class="check-input"
              :checked="baseLayers.rand_mcnally"
              @change="toggleBaseLayer('rand_mcnally')"
            />
            <span class="check-label">Rand McNally 1882</span>
          </label>
        </div>
      </fieldset>

      <hr class="panel-divider" />

      <!-- ── Boundaries ── -->
      <div class="panel-section">
        <span class="section-label">Boundaries</span>
        <div class="switch-list">
          <div class="switch-row">
            <button
              role="switch"
              class="switch-btn"
              :class="{ 'is-on': overlays.counties }"
              :aria-checked="overlays.counties"
              aria-label="Toggle county boundaries"
              @click="toggleOverlay('counties')"
              @keydown.space.prevent="toggleOverlay('counties')"
            >
              <span class="switch-track"><span class="switch-thumb" /></span>
            </button>
            <span class="switch-label">County boundaries</span>
          </div>

          <div class="switch-row">
            <button
              role="switch"
              class="switch-btn"
              :class="{ 'is-on': overlays.states }"
              :aria-checked="overlays.states"
              aria-label="Toggle state boundaries"
              @click="toggleOverlay('states')"
              @keydown.space.prevent="toggleOverlay('states')"
            >
              <span class="switch-track"><span class="switch-thumb" /></span>
            </button>
            <span class="switch-label">State boundaries</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── Panel shell ─────────────────────────────────────────────────────────── */

.layer-panel {
  position: relative;
  pointer-events: all;
  flex-shrink: 0;
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

.layer-panel.is-collapsed {
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
  flex: 1;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--ctp-overlay2);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  white-space: nowrap;
  overflow: hidden;
}

/* ── Section labels ──────────────────────────────────────────────────────── */

.section-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--ctp-overlay2);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  display: block;
  margin-bottom: 9px;
  padding: 0;
  white-space: nowrap;
  overflow: hidden;
}

.panel-divider {
  border: none;
  border-top: 1px solid var(--ctp-surface0);
  margin: 14px 0;
}

.panel-section {
  margin: 0;
}

/* ── Basemap fieldset ────────────────────────────────────────────────────── */

.panel-fieldset {
  border: none;
  padding: 0;
  margin: 0;
}

/* ── Checkbox ────────────────────────────────────────────────────────────── */

.check-list {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.check-row {
  display: flex;
  align-items: center;
  gap: 9px;
  cursor: pointer;
}

.check-input {
  flex-shrink: 0;
  width: 15px;
  height: 15px;
  margin: 0;
  cursor: pointer;
  accent-color: var(--ctp-sapphire);
}

.check-label {
  font-size: 0.88rem;
  color: var(--ctp-text);
  line-height: 1.3;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
}

/* ── Switch ──────────────────────────────────────────────────────────────── */

.switch-list {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.switch-row {
  display: flex;
  align-items: center;
  gap: 9px;
}


.switch-label {
  font-size: 0.88rem;
  color: var(--ctp-text);
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
}

.switch-btn {
  background: transparent;
  border: none;
  padding: 0;
  cursor: pointer;
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.switch-track {
  width: 32px;
  height: 18px;
  border-radius: 9px;
  background: var(--ctp-surface1);
  transition: background var(--dur-std) var(--ease-std);
  position: relative;
  display: block;
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

/* ── Reset north button ──────────────────────────────────────────────────── */

.reset-north-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  height: 28px;
  padding: 0 8px;
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
    color var(--dur-std) var(--ease-std);
}

.reset-north-btn:hover {
  background: color-mix(in oklch, var(--ctp-surface1), transparent 10%);
  color: var(--ctp-text);
}

/* ── Focus rings ─────────────────────────────────────────────────────────── */

button:focus-visible,
.check-input:focus-visible {
  outline: 2px solid var(--vp-c-brand-1);
  outline-offset: 2px;
}

@media (max-width: 760px) {
  .layer-panel {
    width: 100%;
  }
}
</style>
