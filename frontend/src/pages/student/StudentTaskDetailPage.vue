<template>
  <PageHeader title="任务详情" description="查看任务进度、问题摘要、时间线和下载结果。">
    <template #actions>
      <RouterLink class="btn btn-secondary" to="/student/history">返回历史</RouterLink>
    </template>
  </PageHeader>

  <LoadingState v-if="loading && !task" />
  <ErrorState v-else-if="error" :message="error">
    <template #actions>
      <button class="btn btn-secondary" type="button" @click="load">重新加载</button>
    </template>
  </ErrorState>

  <div v-else-if="task" class="space-y-6">
    <ErrorState v-if="pollingWarning" :message="pollingWarning" title="自动刷新已停止" />

    <section class="card">
      <div class="flex items-start justify-between gap-6">
        <div class="min-w-0">
          <p class="text-sm font-semibold text-slate-500">文件名</p>
          <h3
            class="mt-2 truncate text-xl font-bold text-slate-950"
            :title="task.original_filename"
          >
            {{ task.original_filename }}
          </h3>
          <p class="mt-2 break-all text-xs text-slate-400">任务编号：{{ task.id }}</p>
        </div>
        <StatusBadge :status="task.status" />
      </div>
      <div class="mt-5">
        <ProgressBar
          :value="displayProgress"
          label="审核进度"
          :running="task.status === 'running'"
        />
      </div>
    </section>

    <SummaryStats :summary="task.summary" />

    <ReviewTaskTimeline
      :submitted-at="task.submitted_at"
      :started-at="task.started_at"
      :finished-at="task.finished_at"
    />

    <ErrorState
      v-if="task.status === 'failed'"
      :message="task.error_message || '审核失败，请稍后重试。'"
      title="审核失败"
    />

    <ReviewTaskDownloads
      scope="student"
      :task-id="task.id"
      :status="task.status"
      :original-filename="task.original_filename"
      @error="showToast($event, 'error')"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { getErrorMessage } from '@/api/client'
import { getStudentReviewTask } from '@/api/student'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import SummaryStats from '@/components/common/SummaryStats.vue'
import ReviewTaskDownloads from '@/components/review/ReviewTaskDownloads.vue'
import ReviewTaskTimeline from '@/components/review/ReviewTaskTimeline.vue'
import type { ReviewTaskDetail } from '@/types/review'
import { createTaskPoller, type TaskPoller } from '@/utils/polling'
import { getStatusMeta, isUnfinishedStatus } from '@/utils/format'
import { showToast } from '@/utils/toast'

const route = useRoute()
const taskId = computed(() => String(route.params.id))
const task = ref<ReviewTaskDetail | null>(null)
const loading = ref(false)
const error = ref('')
const pollingWarning = ref('')
const poller = ref<TaskPoller | null>(null)

const displayProgress = computed(() => {
  if (!task.value) return 0
  return task.value.progress || getStatusMeta(task.value.status).progress
})

onMounted(load)
onBeforeUnmount(() => poller.value?.stop())

async function load() {
  loading.value = true
  error.value = ''
  pollingWarning.value = ''
  poller.value?.stop()
  try {
    task.value = await getStudentReviewTask(taskId.value)
    if (isUnfinishedStatus(task.value.status)) {
      startPolling()
    }
  } catch (loadError) {
    error.value = getErrorMessage(loadError, '任务不存在或无权访问')
  } finally {
    loading.value = false
  }
}

function startPolling() {
  poller.value = createTaskPoller<ReviewTaskDetail>({
    fetchTask: () => getStudentReviewTask(taskId.value),
    onUpdate: (nextTask) => {
      task.value = nextTask
    },
    onError: (message) => {
      pollingWarning.value = message
    },
  })
  poller.value.start()
}
</script>
