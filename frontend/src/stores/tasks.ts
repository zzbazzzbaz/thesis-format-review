import { defineStore } from 'pinia'

import { getStudentProfile, listStudentReviewTasks } from '@/api/student'
import type { ReviewTaskSummary, StudentProfile } from '@/types/review'

export const useTasksStore = defineStore('tasks', {
  state: () => ({
    profile: null as StudentProfile | null,
    recentTasks: [] as ReviewTaskSummary[],
    loading: false,
  }),
  actions: {
    async loadStudentOverview() {
      this.loading = true
      try {
        const [profile, tasks] = await Promise.all([
          getStudentProfile(),
          listStudentReviewTasks({ page: 1, page_size: 5 }),
        ])
        this.profile = profile
        this.recentTasks = tasks.items
      } finally {
        this.loading = false
      }
    },
    async refreshStudentProfile() {
      this.profile = await getStudentProfile()
    },
  },
})
