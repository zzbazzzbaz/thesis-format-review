<template>
  <div class="grid grid-cols-4 gap-3">
    <div class="mini-stat">
      <p>总数</p>
      <strong>{{ summary.total }}</strong>
    </div>
    <div class="mini-stat mini-stat-danger">
      <p>错误</p>
      <strong>{{ summary.error }}</strong>
    </div>
    <div class="mini-stat mini-stat-warning">
      <p>警告</p>
      <strong>{{ summary.warning }}</strong>
    </div>
    <div class="mini-stat mini-stat-info">
      <p>提示</p>
      <strong>{{ summary.info }}</strong>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { IssueSummary } from '@/types/review'

defineProps<{
  summary: IssueSummary
}>()
</script>
