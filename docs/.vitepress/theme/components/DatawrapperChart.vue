<script setup lang="ts">
import { onMounted, onBeforeUnmount, watch } from 'vue'
import { useData } from 'vitepress'

const props = defineProps<{
  chartId: string
  minHeight?: number
  alt?: string
}>()

const containerId = `datawrapper-vis-${props.chartId}`
const { isDark } = useData()

let messageHandler: ((e: MessageEvent) => void) | null = null

// Datawrapper's embed.js bakes in the OS-level prefers-color-scheme at load
// time and offers no runtime hook, so we manage the iframe ourselves and pass
// the current VitePress theme via the documented `?dark=true|false` URL param.
// Re-rendering on isDark change reloads the chart with matching colors,
// including text fills that don't switch via CSS variables alone.
const renderIframe = (dark: boolean) => {
  const container = document.getElementById(containerId)
  if (!container) return

  const src = `https://datawrapper.dwcdn.net/${props.chartId}/?dark=${dark ? 'true' : 'false'}`
  const existing = container.querySelector('iframe') as HTMLIFrameElement | null

  if (existing) {
    if (existing.src !== src) existing.src = src
    return
  }

  const iframe = document.createElement('iframe')
  iframe.src = src
  iframe.title = props.alt ?? 'Interactive chart'
  iframe.setAttribute('scrolling', 'no')
  iframe.setAttribute('frameborder', '0')
  iframe.setAttribute('aria-label', props.alt ?? 'Interactive chart')
  iframe.style.width = '100%'
  iframe.style.border = 'none'
  iframe.style.height = `${props.minHeight ?? 400}px`
  container.appendChild(iframe)
}

onMounted(() => {
  renderIframe(isDark.value)

  messageHandler = (event: MessageEvent) => {
    const data = event.data as Record<string, unknown> | undefined
    if (!data || typeof data !== 'object') return
    const heights = (data as { 'datawrapper-height'?: Record<string, number> })['datawrapper-height']
    if (!heights) return
    const container = document.getElementById(containerId)
    const iframe = container?.querySelector('iframe') as HTMLIFrameElement | null
    if (!iframe || iframe.contentWindow !== event.source) return
    for (const key in heights) {
      iframe.style.height = `${heights[key]}px`
    }
  }
  window.addEventListener('message', messageHandler)
})

watch(isDark, (val) => {
  renderIframe(val)
})

onBeforeUnmount(() => {
  if (messageHandler) {
    window.removeEventListener('message', messageHandler)
    messageHandler = null
  }
})
</script>

<template>
  <div :id="containerId" :style="{ minHeight: (minHeight ?? 400) + 'px' }">
    <noscript>
      <img
        :src="`https://datawrapper.dwcdn.net/${chartId}/full.png`"
        :alt="alt ?? 'Interactive chart'"
      />
    </noscript>
  </div>
</template>
