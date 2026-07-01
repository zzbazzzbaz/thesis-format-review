import { defineStore } from 'pinia'

import * as authApi from '@/api/auth'
import { toApiError } from '@/api/client'
import type { CurrentUser } from '@/types/auth'

export const AUTH_STORAGE_KEY = 'thesis-review-auth'

interface AuthSnapshot {
  access: string | null
  refresh: string | null
  user: CurrentUser | null
}

function readSnapshot(): AuthSnapshot {
  if (typeof localStorage === 'undefined') {
    return { access: null, refresh: null, user: null }
  }

  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) {
      return { access: null, refresh: null, user: null }
    }
    const parsed = JSON.parse(raw) as AuthSnapshot
    return {
      access: parsed.access || null,
      refresh: parsed.refresh || null,
      user: parsed.user || null,
    }
  } catch {
    localStorage.removeItem(AUTH_STORAGE_KEY)
    return { access: null, refresh: null, user: null }
  }
}

function writeSnapshot(snapshot: AuthSnapshot) {
  if (typeof localStorage === 'undefined') {
    return
  }
  if (!snapshot.access || !snapshot.refresh || !snapshot.user) {
    localStorage.removeItem(AUTH_STORAGE_KEY)
    return
  }
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(snapshot))
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthSnapshot => readSnapshot(),
  getters: {
    isAuthenticated: (state) => Boolean(state.access && state.refresh && state.user),
    displayName: (state) => state.user?.name || state.user?.username || '未登录',
    roleLabel: (state) => {
      if (state.user?.role === 'student') return '学生'
      if (state.user?.role === 'teacher') return '教师'
      if (state.user?.role === 'admin') return '管理员'
      return '未知角色'
    },
    defaultHome: (state) => {
      if (state.user?.role === 'teacher') return '/teacher'
      if (state.user?.role === 'student') return '/student'
      return '/login'
    },
  },
  actions: {
    persist() {
      writeSnapshot({ access: this.access, refresh: this.refresh, user: this.user })
    },
    setSession(access: string, refresh: string, user: CurrentUser) {
      this.access = access
      this.refresh = refresh
      this.user = user
      this.persist()
    },
    setAccessToken(access: string) {
      this.access = access
      this.persist()
    },
    clearSession() {
      this.access = null
      this.refresh = null
      this.user = null
      writeSnapshot({ access: null, refresh: null, user: null })
    },
    async login(username: string, password: string) {
      try {
        const response = await authApi.login({ username, password })
        this.setSession(response.access, response.refresh, response.user)
        return response.user
      } catch (error) {
        throw toApiError(error, '用户名或密码错误')
      }
    },
    async logout() {
      const refresh = this.refresh
      this.clearSession()
      if (!refresh) {
        return
      }
      try {
        await authApi.logout(refresh)
      } catch {
        // 本地退出必须确定完成，后端注销失败不阻止用户离开前端会话。
      }
    },
  },
})
