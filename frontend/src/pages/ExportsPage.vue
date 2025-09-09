<template>
  <q-page class="q-pa-md">
    <div class="text-h4 neon-title q-mb-md">Exports</div>
    <div class="row q-col-gutter-md">
      <div class="col-12 col-md-6">
        <div class="card-dark q-pa-md">
          <div class="text-subtitle2 neon-subtitle q-mb-sm">Tokens</div>
          <q-input v-model="trelloKey" filled label="TRELLO_KEY" prepend-icon="vpn_key" />
          <q-input v-model="trelloToken" filled label="TRELLO_TOKEN" prepend-icon="key" class="q-mt-sm" />
          <q-input v-model="githubToken" filled label="GITHUB_TOKEN" prepend-icon="key" class="q-mt-sm" />
          <div class="q-mt-md">
            <q-btn class="neon-btn neon-btn--green" label="Guardar" @click="save" />
          </div>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'

const trelloKey = ref('')
const trelloToken = ref('')
const githubToken = ref('')

function save() {
  // Placeholder: persist to localStorage
  localStorage.setItem('TRELLO_KEY', trelloKey.value)
  localStorage.setItem('TRELLO_TOKEN', trelloToken.value)
  localStorage.setItem('GITHUB_TOKEN', githubToken.value)
}
</script>

<script>
export default { name: 'ExportsPage' }
</script>

