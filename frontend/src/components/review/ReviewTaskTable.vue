<template>
  <div class="card overflow-hidden p-0">
    <table class="data-table">
      <thead>
        <tr>
          <th v-if="showStudent" class="w-[150px]">学生</th>
          <th class="w-[260px]">文件名</th>
          <th class="w-[110px]">状态</th>
          <th class="w-[220px]">问题摘要</th>
          <th class="w-[145px]">提交时间</th>
          <th class="w-[145px]">完成时间</th>
          <th class="w-[260px]">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="task in tasks" :key="task.id">
          <td v-if="showStudent">
            <div v-if="isTeacherTask(task)" class="min-w-0">
              <p class="truncate font-semibold text-slate-800" :title="task.student.name">
                {{ task.student.name || '-' }}
              </p>
              <p class="truncate text-xs text-slate-500" :title="task.student.student_no">
                {{ task.student.student_no }}
              </p>
            </div>
          </td>
          <td>
            <span class="block max-w-[250px] truncate" :title="task.original_filename">
              {{ task.original_filename }}
            </span>
          </td>
          <td><StatusBadge :status="task.status" /></td>
          <td>
            <span class="block truncate" :title="formatIssueSummary(task.summary)">
              {{ formatIssueSummary(task.summary) }}
            </span>
          </td>
          <td>{{ formatDate(task.submitted_at) }}</td>
          <td>{{ formatDate(task.finished_at) }}</td>
          <td>
            <div class="flex items-center gap-2">
              <RouterLink class="btn btn-secondary gap-2" :to="detailPath(task.id)">
                <Eye class="h-4 w-4" aria-hidden="true" />
                详情
              </RouterLink>
              <button
                class="icon-btn"
                type="button"
                title="下载原始 Word"
                :disabled="loadingKey === `${task.id}:source`"
                @click="download(task, 'source')"
              >
                <Download class="h-4 w-4" aria-hidden="true" />
              </button>
              <button
                class="icon-btn"
                type="button"
                title="下载标注 Word"
                :disabled="task.status !== 'succeeded' || loadingKey === `${task.id}:marked`"
                @click="download(task, 'marked')"
              >
                <FileText class="h-4 w-4" aria-hidden="true" />
              </button>
              <button
                class="icon-btn"
                type="button"
                title="下载问题清单 (JSON)"
                :disabled="task.status !== 'succeeded' || loadingKey === `${task.id}:issues`"
                @click="download(task, 'issues')"
              >
                <FileJson class="h-4 w-4" aria-hidden="true" />
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <slot name="pagination" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Download, Eye, FileJson, FileText } from '@lucide/vue'

import { studentArtifactPath } from '@/api/student'
import { teacherArtifactPath } from '@/api/teacher'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ReviewArtifact, ReviewTaskSummary } from '@/types/review'
import type { TeacherTaskSummary } from '@/types/teacher'
import {
  buildArtifactFilename,
  downloadAuthorizedFile,
  getDownloadErrorMessage,
} from '@/utils/download'
import { formatDate, formatIssueSummary } from '@/utils/format'

type TaskRow = ReviewTaskSummary | TeacherTaskSummary

const props = defineProps<{
  tasks: TaskRow[]
  scope: 'student' | 'teacher'
  showStudent?: boolean
}>()

const emit = defineEmits<{
  error: [message: string]
}>()

const loadingKey = ref('')

function isTeacherTask(task: TaskRow): task is TeacherTaskSummary {
  return 'student' in task
}

function detailPath(taskId: string) {
  return props.scope === 'student' ? `/student/tasks/${taskId}` : `/teacher/tasks/${taskId}`
}

async function download(task: TaskRow, artifact: ReviewArtifact) {
  if (artifact !== 'source' && task.status !== 'succeeded') {
    emit('error', '审核结果尚未生成')
    return
  }
  loadingKey.value = `${task.id}:${artifact}`
  try {
    const path =
      props.scope === 'student'
        ? studentArtifactPath(task.id, artifact)
        : teacherArtifactPath(task.id, artifact)
    await downloadAuthorizedFile(path, buildArtifactFilename(task.original_filename, artifact))
  } catch (error) {
    emit('error', getDownloadErrorMessage(error))
  } finally {
    loadingKey.value = ''
  }
}
</script>
