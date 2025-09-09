<template>
  <q-layout view="lHh Lpr lFf" class="fade-in">
    <q-header class="bg-dark" elevated>
      <q-toolbar>
        <q-toolbar-title class="neon-title"> SIGNUM </q-toolbar-title>
        <q-tabs v-model="tab" shrink stretch dense active-color="white" indicator-color="primary">
          <q-route-tab to="/" label="Home" />
          <q-route-tab to="/runs" label="Runs" />
          <q-route-tab to="/exports" label="Exports" />
          <q-route-tab to="/preview" label="Preview" />
        </q-tabs>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
  
</template>

<script setup>
import { ref } from 'vue'
const tab = ref('home')
</script>

<style scoped>
.bg-dark {
  background: linear-gradient(180deg, rgba(10,10,10,0.9), rgba(10,10,10,0.6));
}
</style>

