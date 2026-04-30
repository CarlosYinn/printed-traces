import { ref, watch, onMounted, onUnmounted, type Ref } from 'vue'

const BREAKPOINT = 760

type Side = 'left' | 'right'

type PanelEntry = { side: Side; isOpen: Ref<boolean> }

const panels: PanelEntry[] = []

function isMobileViewport(): boolean {
  return typeof window !== 'undefined' && window.innerWidth <= BREAKPOINT
}

export function useResponsivePanel(side: Side = 'left') {
  const isOpen = ref(true)

  function check() {
    isOpen.value = window.innerWidth > BREAKPOINT
  }

  const entry: PanelEntry = { side, isOpen }
  panels.push(entry)

  // When this panel opens on mobile, collapse panels on the opposite side
  // so the left/right stacks do not overlap on narrow screens.
  const stopWatch = watch(isOpen, next => {
    if (!next) return
    if (!isMobileViewport()) return
    for (const p of panels) {
      if (p === entry) continue
      if (p.side !== side && p.isOpen.value) p.isOpen.value = false
    }
  })

  onMounted(() => {
    if (typeof window === 'undefined') return
    check()
    window.addEventListener('resize', check)
  })

  onUnmounted(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('resize', check)
    }
    stopWatch()
    const idx = panels.indexOf(entry)
    if (idx !== -1) panels.splice(idx, 1)
  })

  return { isOpen }
}
