import type { ReviewTaskStatus, ReviewTaskSummary } from './review'

export interface StudentBrief {
  id: number
  name: string
  student_no: string
  class_name: string
}

export interface TeacherTaskSummary extends ReviewTaskSummary {
  student: StudentBrief
}

export interface TeacherTaskDetail extends TeacherTaskSummary {
  downloads: {
    source: string
    marked: string | null
    issues: string | null
  }
}

export interface TeacherStats {
  student_total: number
  submitted_student_total: number
  task_total: number
  succeeded_task_total: number
  failed_task_total: number
  average_issue_total: number
  recent_tasks: TeacherTaskSummary[]
}

export interface TeacherTaskListParams {
  page?: number
  page_size?: number
  student_no?: string
  student_name?: string
  status?: ReviewTaskStatus | ''
  submitted_from?: string
  submitted_to?: string
}
