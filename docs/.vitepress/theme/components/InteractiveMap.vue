<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'

import MapCanvas from './MapCanvas.vue'
import { applyInitialProps, startUrlSync, syncFromUrl } from './useFilters'

const props = withDefaults(defineProps<{
  initialMonth?: string
  monthRange?: [string, string]
  initialEventId?: string
  height?: string
}>(), {
  initialMonth: undefined,
  monthRange: undefined,
  initialEventId: undefined,
  height: '100%',
})

const canvasHeight = computed(() => '100%')
let stopUrlSync: (() => void) | null = null

onMounted(() => {
  applyInitialProps({
    initialMonth: props.initialMonth,
    monthRange: props.monthRange,
    initialEventId: props.initialEventId,
  })
  syncFromUrl()
  stopUrlSync = startUrlSync()
})

onUnmounted(() => {
  stopUrlSync?.()
  stopUrlSync = null
})
</script>

<template>
  <div class="interactive-map-root" :style="{ '--interactive-map-height': height }">
    <ClientOnly>
      <div class="interactive-map-shell">
        <div class="interactive-map-canvas">
          <MapCanvas :height="canvasHeight" />
        </div>

      </div>
    </ClientOnly>
  </div>
</template>

<style scoped>
.interactive-map-root {
  position: relative;
  width: 100%;
  height: var(--interactive-map-height, 100%);
  min-height: 0;
  overflow: hidden;
  background: var(--ctp-base);
}

.interactive-map-shell {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
}

.interactive-map-canvas {
  position: relative;
  flex: 1 1 auto;
  min-height: 0;
}

.map-timeline-controls {
  position: absolute;
  left: 16px;
  right: 16px;
  bottom: 16px;
  z-index: 6;
  padding: 8px 14px 6px;
  border: 1px solid var(--ctp-surface0);
  border-radius: 14px;
  background: color-mix(in oklch, var(--ctp-base), transparent 12%);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.10);
  box-sizing: border-box;
  transition: right var(--dur-std) var(--ease-std);
}

/* Leave room for the 340px sidebar + 16px margin + 8px gap */
.map-timeline-controls.has-sidebar {
  right: 372px;
}

@media (max-width: 900px) {
  .map-timeline-controls.has-sidebar {
    right: 16px;
  }
}

@media (max-width: 760px) {
  .map-timeline-controls {
    left: 12px;
    right: 12px;
    bottom: 12px;
    padding: 7px 10px 5px;
  }
}
</style>
