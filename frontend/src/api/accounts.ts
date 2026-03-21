import { useState, useEffect } from 'react'
import { api } from '../lib/api'

export interface MT5Account {
  id: number
  login: string
  server: string
  broker?: string
  account_name?: string
  is_demo: boolean
  connection_status: string
  connection_error?: string
  last_connected?: string
  created_at: string
  instance_id?: string
}

export interface CreateAccountRequest {
  login: string
  password: string
  server: string
  broker?: string
  account_name?: string
  is_demo: boolean
  instance_id?: string
}

export function useMT5Accounts() {
  const [accounts, setAccounts] = useState<MT5Account[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAccounts = async () => {
    try {
      setIsLoading(true)
      const response = await api.get<MT5Account[]>('/accounts')
      setAccounts(response)
      setError(null)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const createAccount = async (data: CreateAccountRequest) => {
    const response = await api.post<MT5Account>('/accounts', data)
    setAccounts(prev => [...prev, response])
    return response
  }

  const updateAccount = async (id: number, data: Partial<MT5Account>) => {
    const response = await api.put<MT5Account>(`/accounts/${id}`, data)
    setAccounts(prev => prev.map(acc => acc.id === id ? response : acc))
    return response
  }

  const deleteAccount = async (id: number) => {
    await api.delete(`/accounts/${id}`)
    setAccounts(prev => prev.filter(acc => acc.id !== id))
  }

  const connectAccount = async (id: number) => {
    const response = await api.post<MT5Account>(`/accounts/${id}/connect`)
    setAccounts(prev => prev.map(acc => acc.id === id ? response : acc))
    return response
  }

  const disconnectAccount = async (id: number) => {
    const response = await api.post<MT5Account>(`/accounts/${id}/disconnect`)
    setAccounts(prev => prev.map(acc => acc.id === id ? response : acc))
    return response
  }

  useEffect(() => {
    fetchAccounts()
  }, [])

  return {
    accounts,
    isLoading,
    error,
    fetchAccounts,
    createAccount,
    updateAccount,
    deleteAccount,
    connectAccount,
    disconnectAccount,
  }
}