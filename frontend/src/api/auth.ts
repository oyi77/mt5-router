import { api } from './client'

interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
}

interface User {
  id: string
  username: string
  role: string
}

export const authApi = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    
    if (!response.ok) {
      throw new Error('Login failed')
    }
    
    return response.json()
  },
  
  getMe: () => api.get<User>('/auth/me'),
  
  logout: () => {
    localStorage.removeItem('token')
  },
}
