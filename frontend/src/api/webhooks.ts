import { api } from './client'

export interface Webhook {
  id: number
  name: string
  url: string
  events: string[]
  is_active: boolean
}

export interface CreateWebhookRequest {
  name: string
  url: string
  secret?: string
  events: string[]
}

export function useWebhooks() {
  const fetchWebhooks = async (): Promise<Webhook[]> => {
    return api.get<Webhook[]>('/webhooks')
  }

  const createWebhook = async (data: CreateWebhookRequest): Promise<{ id: number }> => {
    return api.post<{ id: number }>('/webhooks/configure', data)
  }

  const deleteWebhook = async (id: number): Promise<void> => {
    return api.delete<void>(`/webhooks/${id}`)
  }

  const testWebhook = async (id: number): Promise<{ status: string; response_code?: number; message?: string }> => {
    return api.post<{ status: string; response_code?: number; message?: string }>(`/webhooks/test/${id}`)
  }

  return {
    fetchWebhooks,
    createWebhook,
    deleteWebhook,
    testWebhook,
  }
}