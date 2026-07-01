<template>
  <div class="rounded-lg border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-800">
    <div class="flex items-start gap-3">
      <AlertTriangle class="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
      <div class="min-w-0">
        <p class="font-semibold">{{ title || '操作失败' }}</p>
        <p class="mt-1 break-words">{{ message }}</p>
        <div v-if="$slots.actions" class="mt-3 flex gap-2">
          <slot name="actions" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { AlertTriangle } from '@lucide/vue'

defineProps<{
  message: string
  title?: string
}>()
</script>
