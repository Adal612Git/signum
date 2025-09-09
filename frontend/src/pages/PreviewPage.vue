<template>
  <q-page class="q-pa-md">
    <div class="text-h4 neon-title q-mb-md">Preview</div>
    <q-tabs v-model="tab" dense class="text-grey-5">
      <q-tab name="docs" label="Docs" />
      <q-tab name="uml" label="UML" />
      <q-tab name="gantt" label="Gantt" />
    </q-tabs>
    <q-separator dark />
    <q-tab-panels v-model="tab" animated>
      <q-tab-panel name="docs">
        <div class="card-dark q-pa-md">
          <div class="text-subtitle2 neon-subtitle">Markdown</div>
          <div v-html="renderedMd" class="q-mt-sm"></div>
        </div>
      </q-tab-panel>
      <q-tab-panel name="uml">
        <div class="card-dark q-pa-md">
          <div class="text-subtitle2 neon-subtitle">Mermaid UML</div>
          <div ref="umlEl" class="q-mt-sm"></div>
        </div>
      </q-tab-panel>
      <q-tab-panel name="gantt">
        <div class="card-dark q-pa-md">
          <div class="text-subtitle2 neon-subtitle">Gantt</div>
          <div ref="ganttEl" class="q-mt-sm"></div>
        </div>
      </q-tab-panel>
    </q-tab-panels>
  </q-page>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'

const tab = ref('docs')
const md = ref('# Título\n\n## Subtítulo\n\nContenido...')
const renderedMd = computed(() => {
  // naive markdown -> HTML fallback
  return md.value
    .replace(/^### (.*$)/gim, '<h3 class="neon-subtitle">$1</h3>')
    .replace(/^## (.*$)/gim, '<h2 class="neon-subtitle">$1</h2>')
    .replace(/^# (.*$)/gim, '<h1 class="neon-title">$1</h1>')
    .replace(/\n$/gim, '<br/>')
})

const umlEl = ref(null)
const ganttEl = ref(null)

onMounted(async () => {
  // Mermaid render (if mermaid is available globally)
  try {
    const mermaid = window.mermaid
    const code = `classDiagram\nA <|-- B\nA : +foo()\nB : +bar()`
    if (mermaid && umlEl.value) {
      mermaid.initialize({ startOnLoad: false, theme: 'dark', themeVariables: { lineColor: '#00f0ff', primaryTextColor: '#e5e7eb' } })
      const { svg } = await mermaid.render('uml-svg', code)
      umlEl.value.innerHTML = svg
    } else if (umlEl.value) {
      umlEl.value.innerText = code
    }
  } catch { /* ignored */ }

  // Simple gantt placeholder
  if (ganttEl.value) {
    ganttEl.value.innerHTML = '<div style="color:#00ff7f">[Gantt here]</div>'
  }
})
</script>

<script>
export default { name: 'PreviewPage' }
</script>

