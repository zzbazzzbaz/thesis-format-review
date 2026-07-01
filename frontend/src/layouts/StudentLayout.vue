<template>
  <AppShell
    app-title="毕业设计格式审核系统"
    section-title="学生端"
    :nav-items="navItems"
    :user-name="auth.displayName"
    :role-label="auth.roleLabel"
    @logout="handleLogout"
  />
</template>

<script setup lang="ts">
import { BookOpenCheck, FileClock, History, Upload, UserRound } from '@lucide/vue'
import { useRouter } from 'vue-router'

import AppShell from '@/components/common/AppShell.vue'
import { useAuthStore } from '@/stores/auth'
import type { ShellNavItem } from '@/types/shell'

const router = useRouter()
const auth = useAuthStore()

const navItems: ShellNavItem[] = [
  { label: '工作台', to: '/student', icon: BookOpenCheck },
  { label: '上传论文', to: '/student/upload', icon: Upload },
  { label: '历史记录', to: '/student/history', icon: History },
  { label: '任务详情', to: '/student/tasks', icon: FileClock, hidden: true },
  { label: '个人信息', to: '/student/profile', icon: UserRound },
]

async function handleLogout() {
  await auth.logout()
  router.replace('/login')
}
</script>
