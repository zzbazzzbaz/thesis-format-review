<template>
  <PageHeader title="学生提交" description="按学号、姓名、状态和提交日期筛选自己学生的审核任务。" />

  <TeacherTaskFilters v-model="filters" class="mb-4" @submit="applyFilters" />

  <LoadingState v-if="loading" />
  <ErrorState v-else-if="error" :message="error">
    <template #actions>
      <button class="btn btn-secondary" type="button" @click="load">重新加载</button>
    </template>
  </ErrorState>
  <EmptyState
    v-else-if="tasks.length === 0"
    title="暂无任务"
    description="当前筛选条件下没有学生提交记录。"
    :icon="ClipboardList"
  />

  <div v-else>
    <ReviewTaskTable :tasks="tasks" scope="teacher" show-student @error="downloadError = $event">
      <template #pagination>
        <Pagination
          :page="filters.page || 1"
          :page-size="pageSize"
          :total="total"
          @change="changePage"
        />
      </template>
    </ReviewTaskTable>
    <ErrorState v-if="downloadError" class="mt-4" :message="downloadError" title="下载失败" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ClipboardList } from '@lucide/vue'

import { listTeacherReviewTasks } from '@/api/teacher'
import { getErrorMessage } from '@/api/client'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import Pagination from '@/components/common/Pagination.vue'
import ReviewTaskTable from '@/components/review/ReviewTaskTable.vue'
import TeacherTaskFilters from '@/components/stats/TeacherTaskFilters.vue'
import type { TeacherTaskListParams, TeacherTaskSummary } from '@/types/teacher'

const pageSize = 20
const filters = ref<TeacherTaskListParams>({ page: 1, page_size: pageSize })
const total = ref(0)
const tasks = ref<TeacherTaskSummary[]>([])
const loading = ref(false)
const error = ref('')
const downloadError = ref('')

onMounted(load)

async function load() {
  loading.value = true
  error.value = ''
  downloadError.value = ''
  try {
    const response = await listTeacherReviewTasks(filters.value)
    tasks.value = response.items
    total.value = response.count
  } catch (loadError) {
    error.value = getErrorMessage(loadError)
  } finally {
    loading.value = false
  }
}

function applyFilters(value: TeacherTaskListParams) {
  filters.value = { ...value, page_size: pageSize }
  load()
}

function changePage(page: number) {
  filters.value = { ...filters.value, page, page_size: pageSize }
  load()
}
</script>
