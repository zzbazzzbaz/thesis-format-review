<template>
  <AppShell
    app-title="毕业设计格式审核系统"
    section-title="教师端"
    :nav-items="navItems"
    :user-name="auth.displayName"
    :role-label="auth.roleLabel"
    @logout="handleLogout"
  />
</template>

<script setup lang="ts">
import { BarChart3, ClipboardList, FileClock } from '@lucide/vue'
import { useRouter } from 'vue-router'

import AppShell from '@/components/common/AppShell.vue'
import { useAuthStore } from '@/stores/auth'
import type { ShellNavItem } from '@/types/shell'

const router = useRouter()
const auth = useAuthStore()

const navItems: ShellNavItem[] = [
  { label: '统计概览', to: '/teacher', icon: BarChart3 },
  { label: '学生提交', to: '/teacher/tasks', icon: ClipboardList },
  { label: '任务详情', to: '/teacher/tasks', icon: FileClock, hidden: true },
]

async function handleLogout() {
  await auth.logout()
  router.replace('/login')
}
</script>
