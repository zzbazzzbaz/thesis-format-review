<template>
  <div class="grid grid-cols-3 gap-4">
    <article v-for="item in items" :key="item.label" class="panel flex items-center gap-4">
      <div
        class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg"
        :class="item.iconBg"
      >
        <component :is="item.icon" class="h-6 w-6" :class="item.iconColor" aria-hidden="true" />
      </div>
      <div class="min-w-0">
        <p class="panel-label">{{ item.label }}</p>
        <h3 class="panel-value">{{ item.value }}</h3>
      </div>
    </article>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Users, UserCheck, ClipboardList, CircleCheck, CircleX, CircleAlert } from '@lucide/vue'

import type { TeacherStats } from '@/types/teacher'

const props = defineProps<{
  stats: TeacherStats
}>()

const items = computed(() => [
  {
    label: '学生总数',
    value: props.stats.student_total,
    icon: Users,
    iconBg: 'bg-indigo-50',
    iconColor: 'text-indigo-600',
  },
  {
    label: '已提交学生',
    value: props.stats.submitted_student_total,
    icon: UserCheck,
    iconBg: 'bg-blue-50',
    iconColor: 'text-blue-600',
  },
  {
    label: '任务总数',
    value: props.stats.task_total,
    icon: ClipboardList,
    iconBg: 'bg-slate-100',
    iconColor: 'text-slate-600',
  },
  {
    label: '成功任务',
    value: props.stats.succeeded_task_total,
    icon: CircleCheck,
    iconBg: 'bg-emerald-50',
    iconColor: 'text-emerald-600',
  },
  {
    label: '失败任务',
    value: props.stats.failed_task_total,
    icon: CircleX,
    iconBg: 'bg-red-50',
    iconColor: 'text-red-600',
  },
  {
    label: '平均问题数',
    value: props.stats.average_issue_total.toFixed(1),
    icon: CircleAlert,
    iconBg: 'bg-amber-50',
    iconColor: 'text-amber-600',
  },
])
</script>
