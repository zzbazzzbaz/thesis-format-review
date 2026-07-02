<template>
  <div v-if="variant === 'skeleton'" class="card overflow-hidden">
    <div
      v-for="i in rows"
      :key="i"
      class="flex items-center gap-4 border-b border-slate-100 py-4"
      :class="{ 'border-b-0': i === rows }"
    >
      <div class="skeleton h-4 flex-1 rounded" :style="{ maxWidth: `${60 + ((i * 7) % 30)}%` }" />
      <div class="skeleton h-4 w-20 rounded" />
      <div class="skeleton h-4 w-16 rounded" />
    </div>
  </div>
  <div
    v-else
    class="flex min-h-48 items-center justify-center rounded-lg border border-slate-200 bg-white shadow-sm"
  >
    <div class="flex items-center gap-3 text-sm font-medium text-slate-500">
      <LoaderCircle class="h-5 w-5 animate-spin" aria-hidden="true" />
      {{ label || '加载中' }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { LoaderCircle } from '@lucide/vue'

withDefaults(
  defineProps<{
    label?: string
    variant?: 'spinner' | 'skeleton'
    rows?: number
  }>(),
  {
    variant: 'spinner',
    rows: 5,
  },
)
</script>
