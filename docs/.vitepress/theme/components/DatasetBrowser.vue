<template>
  <div class="db-root">

    <!-- Controls -->
    <div class="db-controls">
      <input
        v-model="query"
        class="db-search"
        type="search"
        placeholder="Search newspaper, keyword, tags…"
        autocomplete="off"
      />
      <div class="db-filters">
        <select v-model="filterKeyword">
          <option value="">All keywords</option>
          <option v-for="k in allKeywords" :key="k" :value="k">{{ k }}</option>
        </select>
        <select v-model="filterRegion">
          <option value="">All regions</option>
          <option v-for="r in allRegions" :key="r" :value="r">{{ r }}</option>
        </select>
        <select v-model="filterYear">
          <option value="">All years</option>
          <option v-for="y in allYears" :key="y" :value="y">{{ y }}</option>
        </select>
        <select v-model="filterReprint">
          <option value="">Original + reprints</option>
          <option value="false">Originals only</option>
          <option value="true">Reprints only</option>
        </select>
      </div>
      <div class="db-meta">
        {{ filtered.length.toLocaleString() }} of {{ records.length.toLocaleString() }} records
        <button class="db-reset" v-if="hasFilters" @click="reset">Reset</button>
      </div>
    </div>

    <!-- Loading / empty states -->
    <div v-if="loading" class="db-state">Loading dataset…</div>
    <div v-else-if="error" class="db-state db-error">{{ error }}</div>
    <div v-else-if="filtered.length === 0" class="db-state">No records match your filters.</div>

    <!-- Table -->
    <div v-else class="db-table-wrap">
      <table class="db-table">
        <thead>
          <tr>
            <th @click="setSort('Date')" :class="sortClass('Date')">Date</th>
            <th @click="setSort('Newspaper_Name')" :class="sortClass('Newspaper_Name')">Newspaper</th>
            <th @click="setSort('Pub_State')" :class="sortClass('Pub_State')">State</th>
            <th @click="setSort('region_bin')" :class="sortClass('region_bin')">Region</th>
            <th @click="setSort('Keyword')" :class="sortClass('Keyword')">Keyword</th>
            <th>Tags</th>
            <th @click="setSort('is_reprint')" :class="sortClass('is_reprint')">Reprint</th>
            <th>Excerpt</th>
            <th>Link</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in page" :key="row.doc_id">
            <td class="db-date">{{ row.Date }}</td>
            <td class="db-paper">{{ row.Newspaper_Name }}</td>
            <td>{{ row.Pub_State }}</td>
            <td>{{ row.region_bin }}</td>
            <td><span class="db-kw">{{ row.Keyword }}</span></td>
            <td class="db-tags">{{ row.topic_tags }}</td>
            <td class="db-bool" :class="row.is_reprint === 'true' ? 'is-yes' : 'is-no'">
              {{ row.is_reprint === 'true' ? 'yes' : 'no' }}
            </td>
            <td class="db-excerpt">{{ row.excerpt }}</td>
            <td>
              <a :href="row.Page_URL" target="_blank" rel="noopener" class="db-link" title="Open on Chronicling America">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
              </a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="db-pagination">
      <button @click="currentPage = 1" :disabled="currentPage === 1">«</button>
      <button @click="currentPage--" :disabled="currentPage === 1">‹</button>
      <span>Page {{ currentPage }} / {{ totalPages }}</span>
      <button @click="currentPage++" :disabled="currentPage === totalPages">›</button>
      <button @click="currentPage = totalPages" :disabled="currentPage === totalPages">»</button>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { withBase } from 'vitepress'

interface Row {
  doc_id: string
  Date: string
  Newspaper_Name: string
  Pub_City: string
  Pub_State: string
  region_bin: string
  Keyword: string
  relevance_tier: string
  topic_tags: string
  is_reprint: string
  reprint_count: string
  Page_URL: string
  excerpt: string
}

const records = ref<Row[]>([])
const loading = ref(true)
const error = ref('')

const query = ref('')
const filterKeyword = ref('')
const filterRegion = ref('')
const filterYear = ref('')
const filterReprint = ref('')

const sortKey = ref<keyof Row>('Date')
const sortAsc = ref(true)
const currentPage = ref(1)
const perPage = 50

onMounted(async () => {
  try {
    const res = await fetch(withBase('/data/dataset-browser.json'))
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    records.value = await res.json()
  } catch (e: any) {
    error.value = `Failed to load dataset: ${e.message}`
  } finally {
    loading.value = false
  }
})

const allKeywords = computed(() => [...new Set(records.value.map(r => r.Keyword))].sort())
const allRegions = computed(() => [...new Set(records.value.map(r => r.region_bin).filter(Boolean))].sort())
const allYears = computed(() => [...new Set(records.value.map(r => r.Date.slice(0,4)))].sort())

const hasFilters = computed(() =>
  query.value || filterKeyword.value || filterRegion.value || filterYear.value || filterReprint.value
)

const filtered = computed(() => {
  const q = query.value.toLowerCase()
  let rows = records.value

  if (q) rows = rows.filter(r =>
    r.Newspaper_Name.toLowerCase().includes(q) ||
    r.Keyword.toLowerCase().includes(q) ||
    r.topic_tags.toLowerCase().includes(q) ||
    r.Pub_State.toLowerCase().includes(q) ||
    r.excerpt.toLowerCase().includes(q)
  )
  if (filterKeyword.value) rows = rows.filter(r => r.Keyword === filterKeyword.value)
  if (filterRegion.value) rows = rows.filter(r => r.region_bin === filterRegion.value)
  if (filterYear.value) rows = rows.filter(r => r.Date.startsWith(filterYear.value))
  if (filterReprint.value) rows = rows.filter(r => r.is_reprint === filterReprint.value)

  const key = sortKey.value
  rows = [...rows].sort((a, b) => {
    const av = a[key] ?? '', bv = b[key] ?? ''
    return sortAsc.value ? av.localeCompare(bv) : bv.localeCompare(av)
  })
  return rows
})

watch(filtered, () => { currentPage.value = 1 })

const totalPages = computed(() => Math.ceil(filtered.value.length / perPage))
const page = computed(() => {
  const start = (currentPage.value - 1) * perPage
  return filtered.value.slice(start, start + perPage)
})

function setSort(key: keyof Row) {
  if (sortKey.value === key) sortAsc.value = !sortAsc.value
  else { sortKey.value = key; sortAsc.value = true }
}

function sortClass(key: keyof Row) {
  if (sortKey.value !== key) return 'sortable'
  return sortAsc.value ? 'sortable sort-asc' : 'sortable sort-desc'
}

function reset() {
  query.value = ''
  filterKeyword.value = ''
  filterRegion.value = ''
  filterYear.value = ''
  filterReprint.value = ''
}
</script>

<style scoped>
.db-root {
  font-family: var(--vp-font-family-base);
  font-size: 0.85rem;
}

.db-controls {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-bottom: 1rem;
}

.db-search {
  width: 100%;
  padding: 0.45rem 0.7rem;
  border: 1px solid var(--vp-c-border);
  border-radius: 6px;
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
  font-size: 0.88rem;
}
.db-search:focus { outline: 2px solid var(--vp-c-brand-1); border-color: transparent; }

.db-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.db-filters select {
  padding: 0.35rem 0.6rem;
  border: 1px solid var(--vp-c-border);
  border-radius: 6px;
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
  font-size: 0.82rem;
  cursor: pointer;
}

.db-meta {
  font-size: 0.78rem;
  color: var(--vp-c-text-3);
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.db-reset {
  padding: 0.2rem 0.6rem;
  border: 1px solid var(--vp-c-border);
  border-radius: 4px;
  background: none;
  color: var(--vp-c-brand-1);
  cursor: pointer;
  font-size: 0.78rem;
}
.db-reset:hover { background: var(--vp-c-brand-soft); }

.db-state {
  padding: 2rem;
  text-align: center;
  color: var(--vp-c-text-2);
}
.db-error { color: #e53e3e; }

.db-table-wrap {
  overflow-x: auto;
  border: 1px solid var(--vp-c-border);
  border-radius: 8px;
}

.db-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.db-table thead tr {
  background: var(--vp-c-bg-soft);
  border-bottom: 1px solid var(--vp-c-border);
}

.db-table th {
  padding: 0.5rem 0.6rem;
  text-align: left;
  font-weight: 600;
  color: var(--vp-c-text-2);
  white-space: nowrap;
  user-select: none;
}

.db-table th.sortable { cursor: pointer; }
.db-table th.sortable:hover { color: var(--vp-c-brand-1); }
.db-table th.sort-asc::after { content: ' ↑'; color: var(--vp-c-brand-1); }
.db-table th.sort-desc::after { content: ' ↓'; color: var(--vp-c-brand-1); }

.db-table tbody tr {
  border-bottom: 1px solid var(--vp-c-divider);
  transition: background 0.1s;
}
.db-table tbody tr:hover { background: var(--vp-c-bg-soft); }

.db-table td {
  padding: 0.45rem 0.6rem;
  vertical-align: middle;
  color: var(--vp-c-text-1);
}

.db-date { white-space: nowrap; color: var(--vp-c-text-2); }
.db-paper { font-weight: 500; min-width: 140px; }
.db-kw {
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
  padding: 0.1em 0.4em;
  border-radius: 3px;
  font-size: 0.76rem;
  white-space: nowrap;
}
.db-tags {
  color: var(--vp-c-text-2);
  font-size: 0.75rem;
  max-width: 160px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.db-bool { text-align: center; font-size: 0.75rem; white-space: nowrap; }
.db-bool.is-yes { color: #b35f4d; }
.db-bool.is-no  { color: var(--vp-c-text-3); }
.db-excerpt {
  color: var(--vp-c-text-2);
  font-size: 0.76rem;
  max-width: 280px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
}
.db-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid var(--vp-c-border);
  color: var(--vp-c-text-2);
  text-decoration: none;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}
.db-link:hover {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
  background: var(--vp-c-brand-soft);
}

.db-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 1rem;
  font-size: 0.85rem;
  color: var(--vp-c-text-2);
}
.db-pagination button {
  padding: 0.25rem 0.6rem;
  border: 1px solid var(--vp-c-border);
  border-radius: 4px;
  background: none;
  cursor: pointer;
  color: var(--vp-c-text-1);
}
.db-pagination button:hover:not(:disabled) { background: var(--vp-c-bg-soft); }
.db-pagination button:disabled { opacity: 0.35; cursor: default; }
</style>
