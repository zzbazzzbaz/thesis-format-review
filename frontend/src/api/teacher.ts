import { apiClient } from './client'

import type { PaginatedResponse, ReviewArtifact } from '@/types/review'
import type {
  TeacherStats,
  TeacherTaskDetail,
  TeacherTaskListParams,
  TeacherTaskSummary,
} from '@/types/teacher'

export async function getTeacherStats() {
  const { data } = await apiClient.get<TeacherStats>('/api/teacher/stats/')
  return data
}

export async function listTeacherReviewTasks(params: TeacherTaskListParams = {}) {
  const { data } = await apiClient.get<PaginatedResponse<TeacherTaskSummary>>(
    '/api/teacher/review-tasks/',
    { params: sanitizeParams(params) },
  )
  return data
}

export async function getTeacherReviewTask(taskId: string) {
  const { data } = await apiClient.get<TeacherTaskDetail>(`/api/teacher/review-tasks/${taskId}/`)
  return data
}

export function teacherArtifactPath(taskId: string, artifact: ReviewArtifact) {
  return `/api/teacher/review-tasks/${taskId}/download/${artifact}/`
}

function sanitizeParams(params: object) {
  return Object.fromEntries(
    Object.entries(params).filter(
      ([, value]) => value !== undefined && value !== null && value !== '',
    ),
  )
}
