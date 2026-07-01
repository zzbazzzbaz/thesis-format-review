<template>
  <div class="mb-6 flex items-start justify-between gap-6">
    <div class="min-w-0">
      <h2 class="text-2xl font-bold text-slate-950">{{ title }}</h2>
      <p v-if="description" class="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
        {{ description }}
      </p>
    </div>
    <div v-if="$slots.actions" class="flex shrink-0 items-center gap-3">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>
