<template>
  <div class="grid grid-cols-6 gap-4">
    <article v-for="item in items" :key="item.label" class="panel">
      <p class="panel-label">{{ item.label }}</p>
      <h3 class="panel-value">{{ item.value }}</h3>
    </article>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { TeacherStats } from '@/types/teacher'

const props = defineProps<{
  stats: TeacherStats
}>()

const items = computed(() => [
  { label: '学生总数', value: props.stats.student_total },
  { label: '已提交学生', value: props.stats.submitted_student_total },
  { label: '任务总数', value: props.stats.task_total },
  { label: '成功任务', value: props.stats.succeeded_task_total },
  { label: '失败任务', value: props.stats.failed_task_total },
  { label: '平均问题数', value: props.stats.average_issue_total.toFixed(1) },
])
</script>
