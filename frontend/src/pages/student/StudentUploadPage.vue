<template>
  <PageHeader
    title="上传论文"
    description="仅支持上传 .docx 文件；上传成功后由后端扣减一次审核次数。"
  >
    <template #actions>
      <RouterLink class="btn btn-secondary" to="/student/history">查看历史</RouterLink>
    </template>
  </PageHeader>

  <LoadingState v-if="loadingProfile" />
  <ErrorState v-else-if="profileError" :message="profileError" />

  <div v-else class="grid grid-cols-[1fr_360px] gap-6">
    <section class="rounded-lg border border-slate-200 bg-white p-6">
      <div
        class="flex h-64 flex-col items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50 text-center"
        :class="{ 'border-blue-400 bg-blue-50': dragging }"
        @dragenter.prevent="dragging = true"
        @dragover.prevent="dragging = true"
        @dragleave.prevent="dragging = false"
        @drop.prevent="handleDrop"
      >
        <UploadCloud class="h-12 w-12 text-slate-400" aria-hidden="true" />
        <p class="mt-4 text-base font-semibold text-slate-950">选择或拖拽 Word 文件</p>
        <p class="mt-2 text-sm text-slate-500">仅支持 .docx 文件</p>
        <input
          ref="fileInput"
          class="hidden"
          type="file"
          accept=".docx"
          @change="handleFileInput"
        />
        <button
          class="btn btn-secondary mt-5"
          type="button"
          :disabled="!canUpload"
          @click="fileInput?.click()"
        >
          选择文件
        </button>
      </div>

      <div v-if="selectedFile" class="mt-5 rounded-lg border border-slate-200 bg-white p-4">
        <p class="text-sm font-semibold text-slate-950">{{ selectedFile.name }}</p>
        <p class="mt-1 text-sm text-slate-500">{{ formatFileSize(selectedFile.size) }}</p>
      </div>

      <ErrorState v-if="error" class="mt-5" :message="error" />

      <div class="mt-6 flex justify-end">
        <button
          class="btn btn-primary gap-2"
          type="button"
          :disabled="!selectedFile || submitting || !canUpload"
          @click="submit"
        >
          <LoaderCircle v-if="submitting" class="h-4 w-4 animate-spin" aria-hidden="true" />
          提交审核
        </button>
      </div>
    </section>

    <aside class="space-y-4">
      <article class="panel">
        <p class="panel-label">当前剩余次数</p>
        <h3 class="panel-value">{{ profile?.remaining_reviews ?? 0 }}</h3>
        <p v-if="!canUpload" class="mt-3 text-sm text-red-600">剩余审核次数不足，请联系管理员。</p>
      </article>

      <article v-if="uploadedTask" class="rounded-lg border border-emerald-200 bg-emerald-50 p-5">
        <p class="text-sm font-semibold text-emerald-900">上传成功</p>
        <p class="mt-2 break-all text-sm text-emerald-800">任务 ID：{{ uploadedTask.id }}</p>
        <RouterLink class="btn btn-primary mt-4" :to="`/student/tasks/${uploadedTask.id}`"
          >查看任务</RouterLink
        >
      </article>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { LoaderCircle, UploadCloud } from '@lucide/vue'

import { uploadReviewTask } from '@/api/student'
import { getErrorMessage } from '@/api/client'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { useTasksStore } from '@/stores/tasks'
import type { ReviewUploadResponse } from '@/types/review'
import { formatFileSize } from '@/utils/format'

const tasks = useTasksStore()
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const uploadedTask = ref<ReviewUploadResponse | null>(null)
const dragging = ref(false)
const submitting = ref(false)
const loadingProfile = ref(false)
const profileError = ref('')
const error = ref('')
const profile = computed(() => tasks.profile)
const canUpload = computed(() => (profile.value?.remaining_reviews ?? 0) > 0)

onMounted(loadProfile)

async function loadProfile() {
  loadingProfile.value = true
  profileError.value = ''
  try {
    await tasks.refreshStudentProfile()
  } catch (loadError) {
    profileError.value = getErrorMessage(loadError)
  } finally {
    loadingProfile.value = false
  }
}

function handleFileInput(event: Event) {
  const input = event.target as HTMLInputElement
  setFile(input.files?.[0] || null)
}

function handleDrop(event: DragEvent) {
  dragging.value = false
  if (!canUpload.value) return
  setFile(event.dataTransfer?.files?.[0] || null)
}

function setFile(file: File | null) {
  error.value = ''
  uploadedTask.value = null
  if (!file) {
    selectedFile.value = null
    return
  }
  if (!file.name.toLowerCase().endsWith('.docx')) {
    selectedFile.value = null
    error.value = '仅支持上传 .docx 文件'
    return
  }
  selectedFile.value = file
}

async function submit() {
  if (!selectedFile.value) {
    error.value = '请先选择 .docx 文件'
    return
  }
  if (!canUpload.value) {
    error.value = '剩余审核次数不足，请联系管理员。'
    return
  }
  submitting.value = true
  error.value = ''
  try {
    uploadedTask.value = await uploadReviewTask(selectedFile.value)
    selectedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
    await tasks.refreshStudentProfile()
  } catch (submitError) {
    error.value = getErrorMessage(submitError, '上传失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}
</script>
