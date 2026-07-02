<template>
  <div class="flex items-center justify-between gap-4 border-t border-slate-200 bg-white px-4 py-3">
    <p class="text-sm text-slate-500">
      共 <span class="font-semibold text-slate-700">{{ total }}</span> 条
    </p>
    <div class="flex items-center gap-1">
      <button
        class="btn btn-secondary btn-sm"
        type="button"
        :disabled="page <= 1"
        @click="emitPage(page - 1)"
      >
        上一页
      </button>
      <template v-for="(p, i) in pageList" :key="i">
        <span v-if="p === null" class="px-1 text-sm text-slate-400">…</span>
        <button
          v-else
          type="button"
          class="inline-flex h-8 min-w-[32px] items-center justify-center rounded-md px-2 text-sm font-medium transition-colors"
          :class="p === page ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-100'"
          @click="emitPage(p)"
        >
          {{ p }}
        </button>
      </template>
      <button
        class="btn btn-secondary btn-sm"
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

const pageList = computed<(number | null)[]>(() => {
  const total = totalPages.value
  const current = props.page
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }
  const pages: (number | null)[] = [1]
  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)
  if (start > 2) pages.push(null)
  for (let i = start; i <= end; i++) pages.push(i)
  if (end < total - 1) pages.push(null)
  pages.push(total)
  return pages
})

function emitPage(page: number) {
  emit('change', page)
}
</script>
