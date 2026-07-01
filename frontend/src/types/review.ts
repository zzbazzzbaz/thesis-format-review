export type ReviewTaskStatus = 'pending' | 'running' | 'succeeded' | 'failed'
export type ReviewArtifact = 'source' | 'marked' | 'issues'

export interface StudentProfile {
  name: string
  student_no: string
  college: string
  major: string
  class_name: string
  teacher: string | null
  remaining_reviews: number
}

export interface IssueSummary {
  total: number
  error: number
  warning: number
  info: number
}

export interface DownloadLinks {
  source: string
  marked: string | null
  issues: string | null
}

export interface ReviewTaskSummary {
  id: string
  status: ReviewTaskStatus
  progress: number
  original_filename: string
  summary: IssueSummary
  submitted_at: string
  started_at: string | null
  finished_at: string | null
  error_message: string
}

export interface ReviewTaskDetail extends ReviewTaskSummary {
  downloads: DownloadLinks
}

export interface ReviewUploadResponse {
  id: string
  status: ReviewTaskStatus
  original_filename: string
  submitted_at: string
}

export interface PaginatedResponse<T> {
  count: number
  page: number
  page_size: number
  items: T[]
}

export interface ReviewTaskListParams {
  page?: number
  page_size?: number
  status?: ReviewTaskStatus | ''
}
