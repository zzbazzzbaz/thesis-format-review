import { apiClient } from './client'

import type {
  PaginatedResponse,
  ReviewArtifact,
  ReviewTaskDetail,
  ReviewTaskListParams,
  ReviewTaskSummary,
  ReviewUploadResponse,
  StudentProfile,
} from '@/types/review'

export async function getStudentProfile() {
  const { data } = await apiClient.get<StudentProfile>('/api/student/profile/')
  return data
}

export async function uploadReviewTask(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await apiClient.post<ReviewUploadResponse>(
    '/api/student/review-tasks/',
    formData,
  )
  return data
}

export async function listStudentReviewTasks(params: ReviewTaskListParams = {}) {
  const { data } = await apiClient.get<PaginatedResponse<ReviewTaskSummary>>(
    '/api/student/review-tasks/',
    { params: sanitizeParams(params) },
  )
  return data
}

export async function getStudentReviewTask(taskId: string) {
  const { data } = await apiClient.get<ReviewTaskDetail>(`/api/student/review-tasks/${taskId}/`)
  return data
}

export function studentArtifactPath(taskId: string, artifact: ReviewArtifact) {
  return `/api/student/review-tasks/${taskId}/download/${artifact}/`
}

function sanitizeParams(params: object) {
  return Object.fromEntries(
    Object.entries(params).filter(
      ([, value]) => value !== undefined && value !== null && value !== '',
    ),
  )
}
