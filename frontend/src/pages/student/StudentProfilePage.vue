<template>
  <PageHeader title="个人信息" description="个人资料和剩余审核次数由后端维护，当前页面仅展示。">
    <template #actions>
      <button class="btn btn-secondary" type="button" @click="load">刷新</button>
    </template>
  </PageHeader>

  <LoadingState v-if="loading" />
  <ErrorState v-else-if="error" :message="error" />

  <section v-else-if="profile" class="rounded-lg border border-slate-200 bg-white p-6">
    <dl class="grid grid-cols-3 gap-5">
      <div class="info-cell">
        <dt>姓名</dt>
        <dd>{{ profile.name || '-' }}</dd>
      </div>
      <div class="info-cell">
        <dt>学号</dt>
        <dd>{{ profile.student_no || '-' }}</dd>
      </div>
      <div class="info-cell">
        <dt>学院</dt>
        <dd>{{ profile.college || '-' }}</dd>
      </div>
      <div class="info-cell">
        <dt>专业</dt>
        <dd>{{ profile.major || '-' }}</dd>
      </div>
      <div class="info-cell">
        <dt>班级</dt>
        <dd>{{ profile.class_name || '-' }}</dd>
      </div>
      <div class="info-cell">
        <dt>指导教师</dt>
        <dd>{{ profile.teacher || '-' }}</dd>
      </div>
      <div class="info-cell">
        <dt>剩余审核次数</dt>
        <dd>{{ profile.remaining_reviews }}</dd>
      </div>
    </dl>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { getStudentProfile } from '@/api/student'
import { getErrorMessage } from '@/api/client'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import type { StudentProfile } from '@/types/review'

const profile = ref<StudentProfile | null>(null)
const loading = ref(false)
const error = ref('')

onMounted(load)

async function load() {
  loading.value = true
  error.value = ''
  try {
    profile.value = await getStudentProfile()
  } catch (loadError) {
    error.value = getErrorMessage(loadError)
  } finally {
    loading.value = false
  }
}
</script>
