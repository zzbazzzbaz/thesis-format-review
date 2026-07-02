<template>
  <div
    class="grid w-[1040px] grid-cols-[420px_1fr] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg"
  >
    <section
      class="border-r border-slate-200 bg-gradient-to-br from-slate-900 via-slate-950 to-indigo-950 px-8 py-10 text-white"
    >
      <p class="text-sm font-semibold text-indigo-300">毕业设计格式审核系统</p>
      <h1 class="mt-4 text-3xl font-bold leading-tight">欢迎使用毕业设计格式审核系统</h1>
      <p class="mt-5 text-sm leading-7 text-slate-300">
        学生可提交 Word 文档并下载审核结果，教师可查看所指导学生的提交情况与统计数据。
      </p>
    </section>

    <section class="px-10 py-10">
      <h2 class="text-2xl font-bold text-slate-950">账号登录</h2>
      <p class="mt-2 text-sm text-slate-500">请输入您的账号和密码登录。</p>

      <ErrorState v-if="error" class="mt-6" :message="error" title="登录失败" />

      <form class="mt-6 space-y-5" @submit.prevent="submit">
        <label class="form-field">
          <span>用户名</span>
          <input v-model.trim="username" class="input" type="text" autocomplete="username" />
        </label>
        <label class="form-field">
          <span>密码</span>
          <input v-model="password" class="input" type="password" autocomplete="current-password" />
        </label>
        <button class="btn btn-primary w-full gap-2" type="submit" :disabled="submitting">
          <LoaderCircle v-if="submitting" class="h-4 w-4 animate-spin" aria-hidden="true" />
          登录
        </button>
      </form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { LoaderCircle } from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'

import ErrorState from '@/components/common/ErrorState.vue'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/api/client'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const username = ref('')
const password = ref('')
const submitting = ref(false)
const error = ref('')

async function submit() {
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }

  submitting.value = true
  error.value = ''
  try {
    const user = await auth.login(username.value, password.value)
    if (user.role === 'admin') {
      auth.clearSession()
      error.value = '管理员请通过管理后台登录。'
      return
    }
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    if (redirect && redirect.startsWith(`/${user.role}`)) {
      await router.replace(redirect)
      return
    }
    await router.replace(user.role === 'teacher' ? '/teacher' : '/student')
  } catch (loginError) {
    error.value = getErrorMessage(loginError, '用户名或密码错误')
  } finally {
    submitting.value = false
  }
}
</script>
