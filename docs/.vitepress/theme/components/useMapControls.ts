import { ref } from 'vue'

export const resetNorthSignal = ref(0)
export const resetCenterSignal = ref(0)

export function triggerResetNorth() {
  resetNorthSignal.value++
}

export function triggerResetCenter() {
  resetCenterSignal.value++
}
