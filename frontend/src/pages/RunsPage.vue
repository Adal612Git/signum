<template>
  <q-page class="q-pa-md">
    <div class="text-h4 neon-title q-mb-md">Runs</div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col-12 col-md-6">
        <q-input v-model="filter" filled label="Buscar / filtrar" debounce="200" />
      </div>
    </div>
    <q-table :rows="filtered" :columns="columns" row-key="id" flat class="card-dark">
      <template #body-cell-status="props">
        <q-td :props="props">
          <span :class="statusClass(props.row.status)" class="neon-tag">{{ props.row.status }}</span>
        </q-td>
      </template>
    </q-table>
  </q-page>
</template>

<script setup>
import { ref, computed } from 'vue'

const columns = [
  { name: 'id', label: 'ID', field: 'id', sortable: true },
  { name: 'name', label: 'Proyecto', field: 'name', sortable: true },
  { name: 'status', label: 'Estado', field: 'status', sortable: true },
]

const rows = ref([
  { id: 'a1', name: 'Alpha', status: 'PASSED' },
  { id: 'b2', name: 'Beta', status: 'FAILED' },
  { id: 'c3', name: 'Gamma', status: 'RUNNING' },
])

const filter = ref('')
const filtered = computed(() => {
  const q = filter.value.toLowerCase()
  return rows.value.filter((r) => JSON.stringify(r).toLowerCase().includes(q))
})

function statusClass(s) {
  if (s === 'PASSED') return 'neon-tag--passed'
  if (s === 'FAILED') return 'neon-tag--failed'
  return 'neon-tag--running'
}
</script>

<script>
export default { name: 'RunsPage' }
</script>

