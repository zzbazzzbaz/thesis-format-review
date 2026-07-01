import { isUnfinishedStatus } from './format'

import type { ReviewTaskStatus } from '@/types/review'

export interface PollableTask {
  status: ReviewTaskStatus
}

export interface TaskPollerOptions<T extends PollableTask> {
  intervalMs?: number
  maxFailures?: number
  fetchTask: () => Promise<T>
  onUpdate: (task: T) => void
  onError?: (message: string) => void
}

export interface TaskPoller {
  start: () => void
  stop: () => void
  isRunning: () => boolean
}

export function createTaskPoller<T extends PollableTask>({
  intervalMs = 3000,
  maxFailures = 3,
  fetchTask,
  onUpdate,
  onError,
}: TaskPollerOptions<T>): TaskPoller {
  let timer: number | null = null
  let stopped = true
  let failures = 0

  async function tick() {
    if (stopped) {
      return
    }
    if (typeof document !== 'undefined' && document.visibilityState === 'hidden') {
      schedule(intervalMs * 2)
      return
    }

    try {
      const task = await fetchTask()
      failures = 0
      onUpdate(task)
      if (!isUnfinishedStatus(task.status)) {
        stop()
        return
      }
      schedule(intervalMs)
    } catch {
      failures += 1
      if (failures >= maxFailures) {
        stop()
        onError?.('网络异常，已停止自动刷新')
        return
      }
      schedule(intervalMs)
    }
  }

  function schedule(ms: number) {
    if (stopped) {
      return
    }
    timer = window.setTimeout(tick, ms)
  }

  function start() {
    if (!stopped) {
      return
    }
    stopped = false
    failures = 0
    schedule(intervalMs)
  }

  function stop() {
    stopped = true
    if (timer !== null) {
      window.clearTimeout(timer)
      timer = null
    }
  }

  return {
    start,
    stop,
    isRunning: () => !stopped,
  }
}
