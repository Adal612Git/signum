<template>
  <q-page class="q-pa-md">
    <div class="q-gutter-md">
      <div class="text-h4 neon-title">Home</div>
      <div class="text-subtitle2 neon-subtitle">Editor JSON (validación en vivo)</div>

      <div class="card-dark q-pa-md">
        <q-input
          v-model="raw"
          filled
          type="textarea"
          autogrow
          :error="!isValid"
          :error-message="errorMsg"
          label="Proyecto (JSON)"
        />
        <div class="q-mt-md">
          <q-btn class="neon-btn neon-btn--pink" label="Subir" :disable="!isValid" @click="upload" />
          <q-badge v-if="isValid" class="q-ml-md neon-tag neon-tag--passed">VÁLIDO</q-badge>
          <q-badge v-else class="q-ml-md neon-tag neon-tag--failed">INVÁLIDO</q-badge>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const raw = ref('{\n  "id": "demo",\n  "name": "Demo",\n  "goals": ["Mejorar DX"]\n}')
const errorMsg = ref('')

const parsed = computed(() => {
  try {
    return JSON.parse(raw.value)
  } catch {
    return null
  }
})

watch(raw, (val) => {
  try {
    JSON.parse(val)
    errorMsg.value = ''
  } catch {
    errorMsg.value = 'JSON inválido'
  }
})

const isValid = computed(() => parsed.value !== null)

function upload() {
  // Placeholder: integrate with backend upload if desired
  console.log('uploaded', parsed.value)
}
</script>

<script>
export default { name: 'HomePage' }
</script>

