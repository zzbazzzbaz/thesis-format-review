<template>
  <PageHeader title="任务详情" description="查看学生提交任务的状态、问题摘要和下载入口。">
    <template #actions>
      <RouterLink class="btn btn-secondary" to="/teacher/tasks">返回列表</RouterLink>
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

    <section class="grid grid-cols-[1fr_360px] gap-6">
      <article class="card">
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
      </article>

      <article class="card">
        <h3 class="text-base font-semibold text-slate-950">学生信息</h3>
        <dl class="mt-4 space-y-3">
          <div class="flex justify-between gap-4">
            <dt class="text-sm text-slate-500">姓名</dt>
            <dd class="truncate text-sm font-semibold text-slate-900">
              {{ task.student.name || '-' }}
            </dd>
          </div>
          <div class="flex justify-between gap-4">
            <dt class="text-sm text-slate-500">学号</dt>
            <dd class="truncate text-sm font-semibold text-slate-900">
              {{ task.student.student_no }}
            </dd>
          </div>
          <div class="flex justify-between gap-4">
            <dt class="text-sm text-slate-500">班级</dt>
            <dd class="truncate text-sm font-semibold text-slate-900">
              {{ task.student.class_name || '-' }}
            </dd>
          </div>
        </dl>
      </article>
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
      scope="teacher"
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
import { getTeacherReviewTask } from '@/api/teacher'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import SummaryStats from '@/components/common/SummaryStats.vue'
import ReviewTaskDownloads from '@/components/review/ReviewTaskDownloads.vue'
import ReviewTaskTimeline from '@/components/review/ReviewTaskTimeline.vue'
import type { TeacherTaskDetail } from '@/types/teacher'
import { getStatusMeta, isUnfinishedStatus } from '@/utils/format'
import { createTaskPoller, type TaskPoller } from '@/utils/polling'
import { showToast } from '@/utils/toast'

const route = useRoute()
const taskId = computed(() => String(route.params.id))
const task = ref<TeacherTaskDetail | null>(null)
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
    task.value = await getTeacherReviewTask(taskId.value)
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
  poller.value = createTaskPoller<TeacherTaskDetail>({
    fetchTask: () => getTeacherReviewTask(taskId.value),
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
