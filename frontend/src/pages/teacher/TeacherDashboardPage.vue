<template>
  <PageHeader title="统计概览" description="查看自己指导学生的提交与审核结果统计。">
    <template #actions>
      <RouterLink class="btn btn-primary" to="/teacher/tasks">查看全部提交</RouterLink>
    </template>
  </PageHeader>

  <LoadingState v-if="loading" />
  <ErrorState v-else-if="error" :message="error">
    <template #actions>
      <button class="btn btn-secondary" type="button" @click="load">重新加载</button>
    </template>
  </ErrorState>

  <div v-else-if="stats" class="space-y-6">
    <TeacherStatsCards :stats="stats" />

    <section>
      <div class="mb-3 flex items-center justify-between">
        <h3 class="text-lg font-semibold text-slate-950">最近提交</h3>
        <RouterLink class="btn btn-secondary" to="/teacher/tasks">全部任务</RouterLink>
      </div>
      <EmptyState
        v-if="stats.recent_tasks.length === 0"
        title="暂无学生提交"
        description="学生上传审核任务后会显示在这里。"
        :icon="ClipboardList"
      />
      <ReviewTaskTable
        v-else
        :tasks="stats.recent_tasks"
        scope="teacher"
        show-student
        @error="showToast($event, 'error')"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ClipboardList } from '@lucide/vue'

import { getTeacherStats } from '@/api/teacher'
import { getErrorMessage } from '@/api/client'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import ReviewTaskTable from '@/components/review/ReviewTaskTable.vue'
import TeacherStatsCards from '@/components/stats/TeacherStatsCards.vue'
import type { TeacherStats } from '@/types/teacher'
import { showToast } from '@/utils/toast'

const stats = ref<TeacherStats | null>(null)
const loading = ref(false)
const error = ref('')

onMounted(load)

async function load() {
  loading.value = true
  error.value = ''
  try {
    stats.value = await getTeacherStats()
  } catch (loadError) {
    error.value = getErrorMessage(loadError)
  } finally {
    loading.value = false
  }
}
</script>
