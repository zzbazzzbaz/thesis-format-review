import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import AuthLayout from '@/layouts/AuthLayout.vue'
import StudentLayout from '@/layouts/StudentLayout.vue'
import TeacherLayout from '@/layouts/TeacherLayout.vue'
import LoginPage from '@/pages/LoginPage.vue'
import StudentDashboardPage from '@/pages/student/StudentDashboardPage.vue'
import StudentHistoryPage from '@/pages/student/StudentHistoryPage.vue'
import StudentProfilePage from '@/pages/student/StudentProfilePage.vue'
import StudentTaskDetailPage from '@/pages/student/StudentTaskDetailPage.vue'
import StudentUploadPage from '@/pages/student/StudentUploadPage.vue'
import TeacherDashboardPage from '@/pages/teacher/TeacherDashboardPage.vue'
import TeacherTaskDetailPage from '@/pages/teacher/TeacherTaskDetailPage.vue'
import TeacherTasksPage from '@/pages/teacher/TeacherTasksPage.vue'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/types/auth'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    role?: Exclude<UserRole, 'admin'>
  }
}

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/login' },
  {
    path: '/',
    component: AuthLayout,
    children: [{ path: 'login', name: 'login', component: LoginPage }],
  },
  {
    path: '/student',
    component: StudentLayout,
    meta: { requiresAuth: true, role: 'student' },
    children: [
      { path: '', name: 'student-dashboard', component: StudentDashboardPage },
      { path: 'upload', name: 'student-upload', component: StudentUploadPage },
      { path: 'history', name: 'student-history', component: StudentHistoryPage },
      { path: 'tasks/:id', name: 'student-task-detail', component: StudentTaskDetailPage },
      { path: 'profile', name: 'student-profile', component: StudentProfilePage },
    ],
  },
  {
    path: '/teacher',
    component: TeacherLayout,
    meta: { requiresAuth: true, role: 'teacher' },
    children: [
      { path: '', name: 'teacher-dashboard', component: TeacherDashboardPage },
      { path: 'tasks', name: 'teacher-tasks', component: TeacherTasksPage },
      { path: 'tasks/:id', name: 'teacher-task-detail', component: TeacherTaskDetailPage },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/login' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.name === 'login' && auth.isAuthenticated) {
    return auth.defaultHome
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.role && auth.user?.role !== to.meta.role) {
    if (auth.user?.role === 'student') {
      return '/student'
    }
    if (auth.user?.role === 'teacher') {
      return '/teacher'
    }
    auth.clearSession()
    return { name: 'login' }
  }

  return true
})

export default router
