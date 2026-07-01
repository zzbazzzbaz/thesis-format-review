<template>
  <div class="rounded-lg border border-slate-200 bg-white p-5">
    <h3 class="text-base font-semibold text-slate-950">时间信息</h3>
    <dl class="mt-4 grid grid-cols-3 gap-4">
      <div class="timeline-item">
        <dt>提交时间</dt>
        <dd>{{ formatDate(submittedAt) }}</dd>
      </div>
      <div class="timeline-item">
        <dt>开始时间</dt>
        <dd>{{ formatDate(startedAt) }}</dd>
      </div>
      <div class="timeline-item">
        <dt>完成时间</dt>
        <dd>{{ formatDate(finishedAt) }}</dd>
      </div>
    </dl>
  </div>
</template>

<script setup lang="ts">
import { formatDate } from '@/utils/format'

defineProps<{
  submittedAt: string
  startedAt: string | null
  finishedAt: string | null
}>()
</script>
