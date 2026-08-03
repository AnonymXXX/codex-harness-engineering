<template>
  <AppModal />
</template>

<script setup lang="ts">
import { onLaunch, onShow } from '@dcloudio/uni-app'
import AppModal from './components/AppModal.vue'

onLaunch(() => {
  console.log('App Launch')
})

onShow(() => {
  console.log('App Show')
})
</script>

<style lang="scss">
@tailwind base;
@tailwind components;
@tailwind utilities;

page {
  background-color: #050505;
  color: #ffffff;
}

* {
  -webkit-tap-highlight-color: transparent;
}
</style>
