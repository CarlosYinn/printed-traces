import { ref, watch, onUnmounted, type Ref } from 'vue'

import { activeEventId, dismissActiveEvent } from './useFilters'
import { useIsMobile, isMobileViewport } from './useIsMobile'

type PanelEntry = { isOpen: Ref<boolean> }

const panels: PanelEntry[] = []

// When the event card appears on mobile, collapse every panel so the card
// takes the spotlight (preserves the "tap event → timeline stows" UX).
if (typeof window !== 'undefined') {
  watch(activeEventId, id => {
    if (!id || !isMobileViewport()) return
    for (const p of panels) p.isOpen.value = false
  })
}

export function useResponsivePanel() {
  const isMobile = useIsMobile()
  const isOpen = ref(!isMobile.value)

  const entry: PanelEntry = { isOpen }
  panels.push(entry)

  // Collapse on entering mobile, expand on entering desktop.  matchMedia
  // only fires on breakpoint crossings, so this is much cheaper than a
  // window resize listener.
  const stopMobileWatch = watch(isMobile, mobile => {
    isOpen.value = !mobile
  })

  // On mobile, the four panels are mutually exclusive — opening any one
  // collapses any other that's still open.  This both prevents the left and
  // right stacks from visually overlapping on narrow phones AND enforces the
  // "≤ 1 panel open while the event card is showing" rule, in one stroke.
  //
  // If the bottom-sheet event card is up when a panel opens, dismiss it: on
  // short viewports the panel and the card both compete for vertical space
  // and the lower button gets squeezed.  Clearing activeEventId triggers the
  // existing card-sink Transition (translateY + fade) so the card glides out
  // the bottom on its own — no extra animation code or measurement needed.
  const stopOpenWatch = watch(isOpen, next => {
    if (!next || !isMobile.value) return
    for (const p of panels) {
      if (p !== entry && p.isOpen.value) p.isOpen.value = false
    }
    if (activeEventId.value !== null) dismissActiveEvent()
  })

  onUnmounted(() => {
    stopMobileWatch()
    stopOpenWatch()
    const idx = panels.indexOf(entry)
    if (idx !== -1) panels.splice(idx, 1)
  })

  return { isOpen }
}
