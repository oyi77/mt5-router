import { api } from './client'

export interface TelegramConfig {
  bot_token: string
  chat_id: string
}

export interface WebhookConfig {
  name: string
  url: string
  events: string[]
}

export interface AlertRule {
  id: string
  type: string
  symbol: string | null
  condition: string
  value: number
  channel: string
  is_active: boolean
  last_triggered: string | null
}

export interface AlertRuleCreate {
  alert_type: string
  symbol?: string
  condition: string
  value: number
  channel?: string
  cooldown_seconds?: number
}

export const notificationsApi = {
  // Telegram
  configureTelegram: (config: TelegramConfig) =>
    api.post('/notifications/telegram/configure', config),
  
  testTelegram: () =>
    api.post('/notifications/telegram/test'),
  
  // Webhooks
  addWebhook: (config: WebhookConfig) =>
    api.post('/notifications/webhooks', config),
  
  listWebhooks: () =>
    api.get<Record<string, any>>('/notifications/webhooks'),
  
  deleteWebhook: (name: string) =>
    api.delete(`/notifications/webhooks/${name}`),
  
  // Alerts
  createAlert: (alert: AlertRuleCreate) =>
    api.post<AlertRule>('/notifications/alerts', alert),
  
  listAlerts: () =>
    api.get<AlertRule[]>('/notifications/alerts'),
  
  updateAlert: (id: string, is_active: boolean) =>
    api.put(`/notifications/alerts/${id}`, { is_active }),
  
  deleteAlert: (id: string) =>
    api.delete(`/notifications/alerts/${id}`),
  
  // Test
  sendTestNotification: (channel: string = 'telegram') =>
    api.post(`/notifications/test?channel=${channel}`),
}
