<template>
  <div class="card p-0">
    <div class="border-b border-slate-200 px-5 py-4">
      <h3 class="text-base font-semibold text-slate-950">文件下载</h3>
    </div>
    <div class="grid grid-cols-3 gap-3 p-5">
      <button
        class="btn btn-secondary gap-2"
        type="button"
        :disabled="loadingArtifact === 'source'"
        @click="download('source')"
      >
        <Download class="h-4 w-4" aria-hidden="true" />
        原始 Word
      </button>
      <button
        class="btn btn-secondary gap-2"
        type="button"
        :disabled="!canDownloadResult || loadingArtifact === 'marked'"
        @click="download('marked')"
      >
        <FileText class="h-4 w-4" aria-hidden="true" />
        标注 Word
      </button>
      <button
        class="btn btn-secondary gap-2"
        type="button"
        :disabled="!canDownloadResult || loadingArtifact === 'issues'"
        @click="download('issues')"
      >
        <FileJson class="h-4 w-4" aria-hidden="true" />
        问题清单 (JSON)
      </button>
    </div>
    <p v-if="!canDownloadResult" class="border-t border-slate-200 px-5 py-3 text-sm text-slate-500">
      审核完成后可下载标注 Word 和问题清单。
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Download, FileJson, FileText } from '@lucide/vue'

import { studentArtifactPath } from '@/api/student'
import { teacherArtifactPath } from '@/api/teacher'
import type { ReviewArtifact, ReviewTaskStatus } from '@/types/review'
import {
  buildArtifactFilename,
  downloadAuthorizedFile,
  getDownloadErrorMessage,
} from '@/utils/download'
import { canDownloadResults } from '@/utils/format'

const props = defineProps<{
  scope: 'student' | 'teacher'
  taskId: string
  status: ReviewTaskStatus
  originalFilename: string
}>()

const emit = defineEmits<{
  error: [message: string]
}>()

const loadingArtifact = ref<ReviewArtifact | null>(null)
const canDownloadResult = computed(() => canDownloadResults(props.status))

async function download(artifact: ReviewArtifact) {
  if (artifact !== 'source' && !canDownloadResult.value) {
    emit('error', '审核结果尚未生成')
    return
  }
  loadingArtifact.value = artifact
  try {
    const path =
      props.scope === 'student'
        ? studentArtifactPath(props.taskId, artifact)
        : teacherArtifactPath(props.taskId, artifact)
    await downloadAuthorizedFile(path, buildArtifactFilename(props.originalFilename, artifact))
  } catch (error) {
    emit('error', getDownloadErrorMessage(error))
  } finally {
    loadingArtifact.value = null
  }
}
</script>
