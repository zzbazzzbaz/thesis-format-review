<template>
  <PageHeader title="历史记录" description="分页查看自己的审核任务，并下载已生成的审核结果。" />

  <section class="mb-4 card">
    <div class="flex items-end gap-3">
      <label class="form-field w-56">
        <span>状态筛选</span>
        <select v-model="status" class="input" @change="applyFilter">
          <option value="">全部状态</option>
          <option v-for="option in statusOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </label>
      <button class="btn btn-secondary" type="button" @click="reset">重置</button>
    </div>
  </section>

  <LoadingState v-if="loading" variant="skeleton" :rows="8" />
  <ErrorState v-else-if="error" :message="error">
    <template #actions>
      <button class="btn btn-secondary" type="button" @click="load">重新加载</button>
    </template>
  </ErrorState>
  <EmptyState
    v-else-if="tasks.length === 0"
    title="暂无审核记录"
    description="上传 .docx 文件后，历史记录会显示在这里。"
    :icon="History"
  >
    <template #actions>
      <RouterLink class="btn btn-primary" to="/student/upload">上传论文</RouterLink>
    </template>
  </EmptyState>

  <div v-else>
    <ReviewTaskTable :tasks="tasks" scope="student" @error="showToast($event, 'error')">
      <template #pagination>
        <Pagination :page="page" :page-size="pageSize" :total="total" @change="changePage" />
      </template>
    </ReviewTaskTable>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { History } from '@lucide/vue'

import { listStudentReviewTasks } from '@/api/student'
import { getErrorMessage } from '@/api/client'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import Pagination from '@/components/common/Pagination.vue'
import ReviewTaskTable from '@/components/review/ReviewTaskTable.vue'
import type { ReviewTaskStatus, ReviewTaskSummary } from '@/types/review'
import { statusOptions } from '@/utils/format'
import { showToast } from '@/utils/toast'

const page = ref(1)
const pageSize = 20
const total = ref(0)
const status = ref<ReviewTaskStatus | ''>('')
const tasks = ref<ReviewTaskSummary[]>([])
const loading = ref(false)
const error = ref('')

onMounted(load)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const response = await listStudentReviewTasks({
      page: page.value,
      page_size: pageSize,
      status: status.value,
    })
    tasks.value = response.items
    total.value = response.count
  } catch (loadError) {
    error.value = getErrorMessage(loadError)
  } finally {
    loading.value = false
  }
}

function applyFilter() {
  page.value = 1
  load()
}

function reset() {
  status.value = ''
  page.value = 1
  load()
}

function changePage(nextPage: number) {
  page.value = nextPage
  load()
}
</script>
