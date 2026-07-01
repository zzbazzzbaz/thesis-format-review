<template>
  <div class="flex items-center justify-between gap-4 border-t border-slate-200 bg-white px-4 py-3">
    <p class="text-sm text-slate-500">
      共 <span class="font-semibold text-slate-700">{{ total }}</span> 条，第
      <span class="font-semibold text-slate-700">{{ page }}</span> /
      <span class="font-semibold text-slate-700">{{ totalPages }}</span> 页
    </p>
    <div class="flex items-center gap-2">
      <button
        class="btn btn-secondary"
        type="button"
        :disabled="page <= 1"
        @click="emitPage(page - 1)"
      >
        上一页
      </button>
      <button
        class="btn btn-secondary"
        type="button"
        :disabled="page >= totalPages"
        @click="emitPage(page + 1)"
      >
        下一页
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  page: number
  pageSize: number
  total: number
}>()

const emit = defineEmits<{
  change: [page: number]
}>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))

function emitPage(page: number) {
  emit('change', page)
}
</script>
