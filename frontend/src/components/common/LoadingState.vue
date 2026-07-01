<template>
  <div
    class="flex min-h-48 items-center justify-center rounded-lg border border-slate-200 bg-white"
  >
    <div class="flex items-center gap-3 text-sm font-semibold text-slate-500">
      <LoaderCircle class="h-5 w-5 animate-spin" aria-hidden="true" />
      {{ label || '加载中' }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { LoaderCircle } from '@lucide/vue'

defineProps<{
  label?: string
}>()
</script>
