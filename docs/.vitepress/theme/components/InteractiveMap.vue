<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

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
          <MapCanvas />
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
  touch-action: none;
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
</style>
