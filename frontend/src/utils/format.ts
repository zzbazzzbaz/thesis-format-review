import type { ReviewTaskStatus } from '@/types/review'

export interface StatusMeta {
  label: string
  tone: 'neutral' | 'info' | 'success' | 'danger'
  progress: number
}

export const statusOptions: Array<{ value: ReviewTaskStatus; label: string }> = [
  { value: 'pending', label: '等待审核' },
  { value: 'running', label: '正在审核' },
  { value: 'succeeded', label: '审核完成' },
  { value: 'failed', label: '审核失败' },
]

export function getStatusMeta(status: ReviewTaskStatus): StatusMeta {
  const metas: Record<ReviewTaskStatus, StatusMeta> = {
    pending: { label: '等待审核', tone: 'neutral', progress: 0 },
    running: { label: '正在审核', tone: 'info', progress: 20 },
    succeeded: { label: '审核完成', tone: 'success', progress: 100 },
    failed: { label: '审核失败', tone: 'danger', progress: 100 },
  }
  return metas[status]
}

export function isUnfinishedStatus(status: ReviewTaskStatus) {
  return status === 'pending' || status === 'running'
}

export function canDownloadResults(status: ReviewTaskStatus) {
  return status === 'succeeded'
}

export function formatDate(value: string | null | undefined) {
  if (!value) {
    return '-'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return '-'
  }
  const year = date.getFullYear()
  const month = pad(date.getMonth() + 1)
  const day = pad(date.getDate())
  const hours = pad(date.getHours())
  const minutes = pad(date.getMinutes())
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

export function formatDateOnly(value: string | null | undefined) {
  if (!value) {
    return ''
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export function formatFileSize(bytes: number) {
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return '0 B'
  }
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex += 1
  }
  return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`
}

export function formatIssueSummary(summary: {
  total: number
  error: number
  warning: number
  info: number
}) {
  return `共 ${summary.total}，错误 ${summary.error}，警告 ${summary.warning}，提示 ${summary.info}`
}

export function issueDensityLabel(total: number) {
  if (total <= 0) return '未发现问题'
  if (total < 10) return '问题较少'
  if (total < 30) return '需要关注'
  return '问题较多'
}

function pad(value: number) {
  return String(value).padStart(2, '0')
}
