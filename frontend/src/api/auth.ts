import { apiClient } from './client'

import type { CurrentUserDetail, LoginPayload, LoginResponse, RefreshResponse } from '@/types/auth'

export async function login(payload: LoginPayload) {
  const { data } = await apiClient.post<LoginResponse>('/api/auth/login/', payload)
  return data
}

export async function refreshAccessToken(refresh: string) {
  const { data } = await apiClient.post<RefreshResponse>('/api/auth/refresh/', { refresh })
  return data
}

export async function logout(refresh: string) {
  const { data } = await apiClient.post<{ detail: string }>('/api/auth/logout/', { refresh })
  return data
}

export async function getCurrentUser() {
  const { data } = await apiClient.get<CurrentUserDetail>('/api/me/')
  return data
}
