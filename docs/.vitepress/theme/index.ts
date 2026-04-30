import DefaultTheme from 'vitepress/theme'
import { withBase, useData } from 'vitepress'
import { h, watchEffect } from 'vue'
import NavTitle from './components/NavTitle.vue'
import DatawrapperChart from './components/DatawrapperChart.vue'
import DatasetBrowser from './components/DatasetBrowser.vue'
import MapCanvas from './components/MapCanvas.vue'
import InteractiveMap from './components/InteractiveMap.vue'
import MapFullscreen from './components/MapFullscreen.vue'
import './style.css'

export default {
  extends: DefaultTheme,
  setup() {
    const { isDark } = useData()
    watchEffect(() => {
      if (typeof document === 'undefined') return

      document.documentElement.style.colorScheme = isDark.value ? 'dark' : 'light'
    })
  },
  enhanceApp({ app }: { app: import('vue').App }) {
    app.component('DatawrapperChart', DatawrapperChart)
    app.component('DatasetBrowser', DatasetBrowser)
    app.component('MapCanvas', MapCanvas)
    app.component('InteractiveMap', InteractiveMap)
    app.component('MapFullscreen', MapFullscreen)
  },
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'nav-bar-title-after': () => h(NavTitle),
      // Inject Printed Traces SVG before the hero heading
      'home-hero-info-before': () => h('img', {
        src: withBase('/printed-traces-light.svg'),
        class: 'hero-paper-mark',
        alt: 'Printed Traces',
      }),
    })
  },
}
