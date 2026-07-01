import type { AxiosResponse } from 'axios'

import { apiClient, getErrorMessage, toApiError } from '@/api/client'
import type { ReviewArtifact } from '@/types/review'

const artifactSuffix: Record<ReviewArtifact, string> = {
  source: '.docx',
  marked: '.marked.docx',
  issues: '.issues.json',
}

export function buildArtifactFilename(originalFilename: string, artifact: ReviewArtifact) {
  const normalized = originalFilename || 'review-task'
  const stem = normalized.replace(/\.docx$/i, '')
  if (artifact === 'source') {
    return normalized.endsWith('.docx') ? normalized : `${normalized}.docx`
  }
  return `${stem}${artifactSuffix[artifact]}`
}

export function filenameFromContentDisposition(header: string | null | undefined) {
  if (!header) {
    return null
  }
  const encoded = /filename\*=UTF-8''([^;]+)/i.exec(header)
  if (encoded?.[1]) {
    return decodeURIComponent(encoded[1].replace(/"/g, ''))
  }
  const plain = /filename="?([^";]+)"?/i.exec(header)
  return plain?.[1] ? plain[1] : null
}

export function getDownloadErrorMessage(error: unknown) {
  return getErrorMessage(error, '下载失败，请稍后重试')
}

export async function downloadAuthorizedFile(path: string, fallbackFilename: string) {
  try {
    const response = await apiClient.get<Blob>(path, { responseType: 'blob' })
    triggerBlobDownload(response, fallbackFilename)
  } catch (error) {
    throw toApiError(error, getDownloadErrorMessage(error))
  }
}

export function triggerBlobDownload(response: AxiosResponse<Blob>, fallbackFilename: string) {
  const filename =
    filenameFromContentDisposition(response.headers['content-disposition']) || fallbackFilename
  const blob = response.data
  const objectUrl = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = filename
  anchor.style.display = 'none'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(objectUrl)
}
