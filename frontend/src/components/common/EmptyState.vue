<template>
  <div class="rounded-lg border border-slate-200 bg-slate-50/50 px-6 py-12 text-center shadow-sm">
    <component :is="icon" v-if="icon" class="mx-auto h-12 w-12 text-slate-300" aria-hidden="true" />
    <p class="mt-4 text-base font-semibold text-slate-900">{{ title }}</p>
    <p v-if="description" class="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-500">
      {{ description }}
    </p>
    <div v-if="$slots.actions" class="mt-5 flex justify-center gap-3">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  title: string
  description?: string
  icon?: Component
}>()
</script>
