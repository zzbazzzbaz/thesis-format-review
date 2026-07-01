<template>
  <form class="rounded-lg border border-slate-200 bg-white p-4" @submit.prevent="submit">
    <div class="grid grid-cols-[1fr_1fr_180px_180px_180px_auto] items-end gap-3">
      <label class="form-field">
        <span>学号</span>
        <input v-model.trim="draft.student_no" class="input" type="text" placeholder="输入学号" />
      </label>
      <label class="form-field">
        <span>学生姓名</span>
        <input v-model.trim="draft.student_name" class="input" type="text" placeholder="输入姓名" />
      </label>
      <label class="form-field">
        <span>状态</span>
        <select v-model="draft.status" class="input">
          <option value="">全部状态</option>
          <option v-for="option in statusOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </label>
      <label class="form-field">
        <span>开始日期</span>
        <input v-model="draft.submitted_from" class="input" type="date" />
      </label>
      <label class="form-field">
        <span>结束日期</span>
        <input v-model="draft.submitted_to" class="input" type="date" />
      </label>
      <div class="flex gap-2">
        <button class="btn btn-primary gap-2" type="submit">
          <Search class="h-4 w-4" aria-hidden="true" />
          筛选
        </button>
        <button class="btn btn-secondary" type="button" @click="reset">重置</button>
      </div>
    </div>
  </form>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import { Search } from '@lucide/vue'

import type { TeacherTaskListParams } from '@/types/teacher'
import { statusOptions } from '@/utils/format'

const props = defineProps<{
  modelValue: TeacherTaskListParams
}>()

const emit = defineEmits<{
  'update:modelValue': [value: TeacherTaskListParams]
  submit: [value: TeacherTaskListParams]
}>()

const draft = reactive<TeacherTaskListParams>({ ...props.modelValue })

watch(
  () => props.modelValue,
  (value) => Object.assign(draft, value),
)

function submit() {
  const value = { ...draft, page: 1 }
  emit('update:modelValue', value)
  emit('submit', value)
}

function reset() {
  const value: TeacherTaskListParams = { page: 1, page_size: props.modelValue.page_size || 20 }
  Object.assign(draft, value)
  emit('update:modelValue', value)
  emit('submit', value)
}
</script>
