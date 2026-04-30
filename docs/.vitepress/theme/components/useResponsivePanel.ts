import { ref, onMounted, onUnmounted } from 'vue'

const BREAKPOINT = 760

export function useResponsivePanel() {
  const isOpen = ref(true)

  function check() {
    isOpen.value = window.innerWidth > BREAKPOINT
  }

  onMounted(() => {
    if (typeof window === 'undefined') return
    check()
    window.addEventListener('resize', check)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', check)
  })

  return { isOpen }
}
