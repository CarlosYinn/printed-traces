export interface TopicTree {
  categories: Category[]
}

export interface Category {
  name: string
  color: string
  hue: string
  topics: Topic[]
}

export interface Topic {
  id: string
  label: string
  color: string
  deduped_topic_id: string | null
  all_topic_id: string | null
  weight: number
  exclude: boolean
}

export interface HistoricalEvent {
  id: string
  title: string
  date: string
  month_range: [string, string]
  description: string
  highlight_fips: string[]
  highlight_level: 'global' | 'state' | 'county'
  related_topic_ids?: string[]
}

export interface RecordProperties {
  doc_id: string
  date: string
  year_month: string
  topic_id: string
  topic_label: string
  category: string
  category_color: string
  topic_color: string
  topic_source: 's2_direct' | 's2_inherited' | 'topic_tags_fallback'
  newspaper: string
  pub_city: string
  pub_state: string
  coverage_counties: Array<[string, string]>
  page_url: string
  is_reprint: boolean
  reprint_count: number
  excerpt: string
  location_tier: 1 | 2 | 3
}

export interface RecordFeature {
  type: 'Feature'
  geometry: { type: 'Point'; coordinates: [number, number] }
  properties: RecordProperties
}
