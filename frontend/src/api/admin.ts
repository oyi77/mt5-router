import { api } from './client'

export interface AdminUser {
  id: number
  email: string
  username: string
  full_name: string | null
  role: string
  is_active: boolean
  is_verified: boolean
  created_at: string
  last_login: string | null
  two_factor_enabled: boolean
}

export interface AdminAnalytics {
  total_users: number
  active_users: number
  total_instances: number
  running_instances: number
  total_servers: number
  total_revenue: number
  signups_last_30_days: number
}

export interface TierConfig {
  name: string
  price_monthly: number
  price_yearly: number
  limits: {
    max_servers: number
    max_instances: number
    max_api_calls_per_day: number
    max_users: number
    support_level: string
  }
  features: string[]
}

interface PaginatedUsers {
  items: AdminUser[]
  total: number
}

interface TiersResponse {
  tiers: Record<string, TierConfig>
}

export const adminApi = {
  // Users
  listUsers: async (skip = 0, limit = 50): Promise<AdminUser[]> => {
    const res = await api.get<PaginatedUsers>(`/admin/users?skip=${skip}&limit=${limit}`)
    return res.items
  },
  getUser: (id: number) => api.get<AdminUser>(`/admin/users/${id}`),
  updateUser: (id: number, data: { role?: string; is_active?: boolean; full_name?: string }) =>
    api.put<AdminUser>(`/admin/users/${id}`, data),
  deleteUser: (id: number) => api.delete(`/admin/users/${id}`),
  banUser: (id: number) => api.post(`/admin/users/${id}/ban`),
  unbanUser: (id: number) => api.post(`/admin/users/${id}/unban`),

  // Tiers
  getTiers: async (): Promise<Record<string, TierConfig>> => {
    const res = await api.get<TiersResponse>('/admin/tiers')
    return res.tiers
  },
  updateTier: (name: string, data: Partial<TierConfig>) =>
    api.put<TierConfig>(`/admin/tiers/${name}`, data),

  // Analytics
  getAnalytics: () => api.get<AdminAnalytics>('/admin/analytics'),
}
