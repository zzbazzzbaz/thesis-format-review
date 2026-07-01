export type UserRole = 'student' | 'teacher' | 'admin'

export interface CurrentUser {
  id: number
  username: string
  name: string
  role: UserRole
}

export interface CurrentUserDetail extends CurrentUser {
  is_active: boolean
  created_at: string
}

export interface LoginPayload {
  username: string
  password: string
}

export interface LoginResponse {
  access: string
  refresh: string
  user: CurrentUser
}

export interface RefreshResponse {
  access: string
}
