<template>
  <div class="w-full">
    <div class="flex items-center justify-between text-xs font-semibold text-slate-500">
      <span>{{ label }}</span>
      <span>{{ safeValue }}%</span>
    </div>
    <div class="mt-2 h-2 overflow-hidden rounded-full bg-slate-200">
      <div
        class="h-full rounded-full bg-blue-600 transition-all"
        :style="{ width: `${safeValue}%` }"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  value: number
  label?: string
}>()

const safeValue = computed(() => Math.min(100, Math.max(0, Math.round(props.value || 0))))
</script>
