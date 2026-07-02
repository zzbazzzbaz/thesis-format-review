<template>
  <PageHeader title="学生工作台" description="查看个人审核次数、最近任务和当前审核进度。">
    <template #actions>
      <RouterLink class="btn btn-primary gap-2" to="/student/upload">
        <Upload class="h-4 w-4" aria-hidden="true" />
        上传论文
      </RouterLink>
    </template>
  </PageHeader>

  <LoadingState v-if="tasks.loading && !tasks.profile" />
  <ErrorState v-else-if="error" :message="error">
    <template #actions>
      <button class="btn btn-secondary" type="button" @click="load">重新加载</button>
    </template>
  </ErrorState>

  <div v-else class="space-y-6">
    <section class="grid grid-cols-3 gap-4">
      <article class="panel">
        <p class="panel-label">姓名</p>
        <h3 class="panel-value">{{ profile?.name || '—' }}</h3>
      </article>
      <article class="panel">
        <p class="panel-label">学号</p>
        <h3 class="panel-value">{{ profile?.student_no || '—' }}</h3>
      </article>
      <article class="panel">
        <p class="panel-label">专业 / 班级</p>
        <h3
          class="panel-value truncate"
          :title="`${profile?.major || '—'} / ${profile?.class_name || '—'}`"
        >
          {{ profile?.major || '—' }} / {{ profile?.class_name || '—' }}
        </h3>
      </article>
      <article class="panel">
        <p class="panel-label">指导教师</p>
        <h3 class="panel-value">{{ profile?.teacher || '—' }}</h3>
      </article>
      <article class="panel col-span-2 border-l-4 border-l-indigo-500">
        <p class="panel-label">剩余审核次数</p>
        <h3 class="panel-value">{{ profile?.remaining_reviews ?? '—' }}</h3>
      </article>
    </section>

    <ErrorState v-if="pollingWarning" :message="pollingWarning" title="自动刷新已停止" />

    <section>
      <div class="mb-3 flex items-center justify-between">
        <h3 class="text-lg font-semibold text-slate-950">最近任务</h3>
        <RouterLink class="btn btn-secondary" to="/student/history">查看历史</RouterLink>
      </div>
      <EmptyState
        v-if="tasks.recentTasks.length === 0"
        title="暂无审核记录"
        description="上传 .docx 文件后，审核任务会显示在这里。"
        :icon="FileClock"
      >
        <template #actions>
          <RouterLink class="btn btn-primary" to="/student/upload">去上传</RouterLink>
        </template>
      </EmptyState>
      <ReviewTaskTable
        v-else
        :tasks="tasks.recentTasks"
        scope="student"
        @error="showToast($event, 'error')"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { FileClock, Upload } from '@lucide/vue'

import { listStudentReviewTasks } from '@/api/student'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import ReviewTaskTable from '@/components/review/ReviewTaskTable.vue'
import { useTasksStore } from '@/stores/tasks'
import type { ReviewTaskSummary, ReviewTaskStatus } from '@/types/review'
import { getErrorMessage } from '@/api/client'
import { createTaskPoller, type TaskPoller } from '@/utils/polling'
import { isUnfinishedStatus } from '@/utils/format'
import { showToast } from '@/utils/toast'

interface OverviewPollResult {
  status: ReviewTaskStatus
  items: ReviewTaskSummary[]
}

const tasks = useTasksStore()
const error = ref('')
const pollingWarning = ref('')
const poller = ref<TaskPoller | null>(null)
const profile = computed(() => tasks.profile)

onMounted(load)
onBeforeUnmount(() => poller.value?.stop())

async function load() {
  error.value = ''
  pollingWarning.value = ''
  poller.value?.stop()
  try {
    await tasks.loadStudentOverview()
    startPollingIfNeeded()
  } catch (loadError) {
    error.value = getErrorMessage(loadError)
  }
}

function startPollingIfNeeded() {
  if (!tasks.recentTasks.some((task) => isUnfinishedStatus(task.status))) {
    return
  }
  poller.value = createTaskPoller<OverviewPollResult>({
    fetchTask: async () => {
      const response = await listStudentReviewTasks({ page: 1, page_size: 5 })
      const hasUnfinished = response.items.some((task) => isUnfinishedStatus(task.status))
      return { status: hasUnfinished ? 'running' : 'succeeded', items: response.items }
    },
    onUpdate: (result) => {
      tasks.recentTasks = result.items
    },
    onError: (message) => {
      pollingWarning.value = message
    },
  })
  poller.value.start()
}
</script>
