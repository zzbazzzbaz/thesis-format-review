<template>
  <div class="min-h-screen min-w-[1280px] bg-slate-100 text-slate-950">
    <div class="flex min-h-screen">
      <aside class="flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white">
        <div class="border-b border-slate-200 px-6 py-5">
          <p class="text-sm font-medium text-slate-500">{{ appTitle }}</p>
          <h1 class="mt-1 text-xl font-semibold text-slate-950">{{ sectionTitle }}</h1>
        </div>

        <nav class="flex-1 space-y-1 px-4 py-5">
          <RouterLink
            v-for="item in visibleNavItems"
            :key="item.to"
            :to="item.to"
            class="nav-item"
            :class="{ 'nav-item-active': isActive(item.to) }"
          >
            <component :is="item.icon" class="h-4 w-4 shrink-0" aria-hidden="true" />
            <span class="truncate">{{ item.label }}</span>
          </RouterLink>
        </nav>

        <div class="border-t border-slate-200 px-6 py-4 text-xs leading-5 text-slate-500">
          <p class="font-semibold text-slate-700">产品侧前端</p>
          <p class="truncate" :title="apiBaseUrl">API {{ apiBaseUrl }}</p>
        </div>
      </aside>

      <main class="min-w-0 flex-1">
        <header
          class="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-8"
        >
          <div class="min-w-0">
            <p class="text-sm text-slate-500">{{ roleLabel }}</p>
            <p class="truncate text-base font-semibold text-slate-950">{{ userName }}</p>
          </div>
          <button class="btn btn-secondary gap-2" type="button" @click="$emit('logout')">
            <LogOut class="h-4 w-4" aria-hidden="true" />
            退出登录
          </button>
        </header>

        <section class="px-8 py-8">
          <RouterView />
        </section>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { LogOut } from '@lucide/vue'

import { API_BASE_URL } from '@/api/client'
import type { ShellNavItem } from '@/types/shell'

defineEmits<{
  logout: []
}>()

const props = defineProps<{
  appTitle: string
  sectionTitle: string
  navItems: ShellNavItem[]
  userName: string
  roleLabel: string
}>()

const route = useRoute()
const apiBaseUrl = API_BASE_URL
const visibleNavItems = computed(() => props.navItems.filter((item) => !item.hidden))

function isActive(to: string) {
  if (to === '/student' || to === '/teacher') {
    return route.path === to
  }
  return route.path.startsWith(to)
}
</script>
