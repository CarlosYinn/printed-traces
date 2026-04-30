import { topicTree } from './useRecords'
import type { HistoricalEvent } from './types'

export function useEventColor() {
  function topicKeySuffix(id: string): string {
    const i = id.indexOf('_')
    return i === -1 ? id : id.slice(i + 1)
  }

  function getEventAccentColor(event: HistoricalEvent): string {
    const ids = event.related_topic_ids
    const categories = topicTree.value?.categories
    if (!ids?.length || !categories?.length) return 'var(--ctp-peach)'

    const idSet = new Set(ids)
    const suffixSet = new Set(ids.map(topicKeySuffix))

    for (const category of categories) {
      for (const topic of category.topics) {
        if (idSet.has(topic.id) || suffixSet.has(topicKeySuffix(topic.id))) {
          return topic.color || category.color || 'var(--ctp-peach)'
        }
      }
    }
    return 'var(--ctp-peach)'
  }

  return { getEventAccentColor }
}
