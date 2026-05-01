<script setup lang="ts">
import { computed } from 'vue'
import { useRecords } from './useRecords'
import type { RecordProperties, Topic } from './types'

const props = defineProps<{
  record: RecordProperties | null
  position: { x: number; y: number } | null
}>()

const emit = defineEmits<{ close: [] }>()

const { topicTree } = useRecords()

const popupTopics = computed<Topic[]>(() => {
  if (!props.record || !topicTree.value) return []
  for (const category of topicTree.value.categories) {
    const topic = category.topics.find(t => t.id === props.record?.topic_id)
    if (topic) return [topic]
  }
  return []
})

function formatDate(date: string): string {
  const parsed = new Date(`${date}T00:00:00`)
  if (Number.isNaN(parsed.getTime())) return date
  return new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC',
  }).format(parsed)
}

const locationLabel = computed(() => {
  if (!props.record) return ''
  return [props.record.pub_city, props.record.pub_state].filter(Boolean).join(', ')
})

const CARD_W = 280
const CARD_H = 260
const GAP = 10   // gap between dot and card edge
const EDGE = 12  // min distance from viewport edge

const popupStyle = computed(() => {
  if (!props.position) return {}
  const { x, y } = props.position
  const vw = typeof window === 'undefined' ? 9999 : window.innerWidth
  const vh = typeof window === 'undefined' ? 9999 : window.innerHeight

  // Prefer right of dot; flip left if not enough room
  const left = x + GAP + CARD_W + EDGE > vw
    ? Math.max(EDGE, x - GAP - CARD_W)
    : x + GAP

  // Vertically centre on the dot; clamp to viewport
  const top = Math.max(EDGE, Math.min(y - CARD_H / 2, vh - CARD_H - EDGE))

  return { left: `${left}px`, top: `${top}px` }
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="record && position"
      class="record-popup"
      :style="popupStyle"
      role="tooltip"
    >
      <button class="popup-close" aria-label="Close" @click="emit('close')">✕</button>

      <span class="popup-date">{{ formatDate(record.date) }}</span>
      <span class="popup-newspaper">{{ record.newspaper }}</span>
      <span class="popup-location">{{ locationLabel }}</span>

      <span v-if="popupTopics.length" class="popup-tags">
        <span
          v-for="topic in popupTopics"
          :key="topic.id"
          class="popup-tag"
          :style="{ background: topic.color }"
        >{{ topic.label }}</span>
      </span>

      <span class="popup-excerpt">{{ record.excerpt }}</span>

      <a
        class="popup-link"
        :href="record.page_url"
        target="_blank"
        rel="noreferrer"
      >View on Library of Congress &#8599;</a>
    </div>
  </Teleport>
</template>

<style scoped>
.record-popup {
  position: fixed;
  z-index: 1000;
  box-sizing: border-box;
  width: 280px;
  padding: 12px;
  border: 1px solid var(--ctp-surface0);
  border-radius: 12px;
  background: var(--ctp-base);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  color: var(--ctp-text);
  pointer-events: auto;
}

.popup-close {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  padding: 0;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--ctp-overlay1);
  font-size: 11px;
  line-height: 1;
  cursor: pointer;
}

.popup-close:hover {
  background: var(--ctp-surface0);
  color: var(--ctp-text);
}

.popup-date {
  display: block;
  margin-bottom: 4px;
  color: var(--ctp-overlay2);
  font-size: 0.72rem;
  font-weight: 600;
  line-height: 1.25;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.popup-newspaper {
  display: block;
  color: var(--ctp-subtext0);
  font-size: 16px;
  font-weight: 600;
  line-height: 1.25;
}

.popup-location {
  display: block;
  margin-top: 3px;
  color: var(--ctp-subtext1);
  font-size: 13px;
  line-height: 1.3;
}

.popup-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.popup-tag {
  padding: 2px 8px;
  border-radius: 999px;
  color: var(--ctp-base);
  font-size: 11px;
  font-weight: 700;
  line-height: 1.35;
}

.popup-excerpt {
  display: -webkit-box;
  margin-top: 10px;
  overflow: hidden;
  color: var(--ctp-text);
  font-size: 14px;
  line-height: 1.42;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 4;
  line-clamp: 4;
}

.popup-link {
  display: inline-block;
  margin-top: 10px;
  color: var(--ctp-sapphire);
  font-size: 12px;
  font-weight: 600;
  line-height: 1.3;
  text-decoration: none;
}
</style>
