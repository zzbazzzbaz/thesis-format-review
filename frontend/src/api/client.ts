import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'

import type { RefreshResponse } from '@/types/auth'

export const API_BASE_URL = normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL || '/')

export const SESSION_EXPIRED_MESSAGE = '登录已过期，请重新登录'

export interface ApiAuthHandlers {
  getAccessToken: () => string | null
  getRefreshToken: () => string | null
  setAccessToken: (access: string) => void
  clearAuth: () => void
}

export class ApiError extends Error {
  status?: number

  constructor(message: string, status?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

let authHandlers: ApiAuthHandlers = {
  getAccessToken: () => null,
  getRefreshToken: () => null,
  setAccessToken: () => undefined,
  clearAuth: () => undefined,
}

let refreshPromise: Promise<string> | null = null

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    Accept: 'application/json',
  },
})

export function configureApiAuth(handlers: ApiAuthHandlers) {
  authHandlers = handlers
}

export function normalizeApiBaseUrl(value: string) {
  return value.replace(/\/+$/, '')
}

export function getErrorMessage(error: unknown, fallback = '服务暂不可用，请稍后重试') {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data
    if (data instanceof Blob) {
      return fallback
    }
    if (typeof data === 'string' && data.trim()) {
      return data
    }
    if (typeof data?.detail === 'string' && data.detail.trim()) {
      return data.detail
    }
    if (typeof data?.message === 'string' && data.message.trim()) {
      return data.message
    }
    if (error.response?.status === 403) {
      return '无权访问'
    }
    if (error.response?.status === 404) {
      return '任务不存在或无权访问'
    }
    if (error.response?.status === 409) {
      return '审核结果尚未生成'
    }
  }
  if (error instanceof ApiError) {
    return error.message
  }
  return fallback
}

export function toApiError(error: unknown, fallback?: string) {
  if (axios.isAxiosError(error)) {
    return new ApiError(getErrorMessage(error, fallback), error.response?.status)
  }
  if (error instanceof ApiError) {
    return error
  }
  return new ApiError(fallback || '服务暂不可用，请稍后重试')
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const access = authHandlers.getAccessToken()
  if (access) {
    config.headers.Authorization = `Bearer ${access}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalConfig = error.config as
      (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined

    if (!originalConfig || error.response?.status !== 401 || originalConfig._retry) {
      return Promise.reject(error)
    }

    const url = originalConfig.url || ''
    if (url.includes('/api/auth/login/') || url.includes('/api/auth/refresh/')) {
      return Promise.reject(error)
    }

    const refresh = authHandlers.getRefreshToken()
    if (!refresh) {
      authHandlers.clearAuth()
      return Promise.reject(new ApiError(SESSION_EXPIRED_MESSAGE, 401))
    }

    originalConfig._retry = true

    try {
      if (!refreshPromise) {
        refreshPromise = axios
          .post<RefreshResponse>(`${API_BASE_URL}/api/auth/refresh/`, { refresh })
          .then((response) => response.data.access)
          .finally(() => {
            refreshPromise = null
          })
      }

      const access = await refreshPromise
      authHandlers.setAccessToken(access)
      originalConfig.headers.Authorization = `Bearer ${access}`
      return apiClient.request(originalConfig)
    } catch (refreshError) {
      authHandlers.clearAuth()
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.assign('/login')
      }
      return Promise.reject(refreshError)
    }
  },
)
