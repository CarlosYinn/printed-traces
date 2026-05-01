import { ref, type Ref } from 'vue'

const MOBILE_BREAKPOINT_PX = 760
const MOBILE_QUERY = `(max-width: ${MOBILE_BREAKPOINT_PX}px)`

let mql: MediaQueryList | null = null
const isMobileRef = ref(false)
let initialized = false

function ensureInitialized() {
  if (initialized || typeof window === 'undefined') return
  initialized = true
  mql = window.matchMedia(MOBILE_QUERY)
  isMobileRef.value = mql.matches
  mql.addEventListener('change', e => {
    isMobileRef.value = e.matches
  })
}

/** Reactive flag — true when the viewport is at most 760 px wide. */
export function useIsMobile(): Ref<boolean> {
  ensureInitialized()
  return isMobileRef
}

/** Synchronous read of the current value (no Vue scope required). */
export function isMobileViewport(): boolean {
  if (typeof window === 'undefined') return false
  if (mql) return mql.matches
  return window.innerWidth <= MOBILE_BREAKPOINT_PX
}
