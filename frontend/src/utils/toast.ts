import { reactive } from 'vue'

export interface ToastItem {
  id: number
  type: 'success' | 'error' | 'info'
  message: string
}

const toasts = reactive<ToastItem[]>([])
let nextId = 0

export function showToast(message: string, type: ToastItem['type'] = 'info', duration = 3500) {
  const id = ++nextId
  toasts.push({ id, type, message })
  setTimeout(() => removeToast(id), duration)
}

export function removeToast(id: number) {
  const index = toasts.findIndex((t) => t.id === id)
  if (index !== -1) toasts.splice(index, 1)
}

export function useToasts() {
  return toasts
}
