import { api } from './client'

export interface SystemMetrics {
  cpu_percent: number
  memory: {
    total: number
    available: number
    percent: number
    used: number
  }
  disk: {
    total: number
    used: number
    free: number
    percent: number
  }
  timestamp: string
}

export interface InstanceMetric {
  id: string
  name: string
  status: string
  cpu_percent: number
  memory_usage_mb: number
  memory_limit_mb: number
  memory_percent: number
}

export interface Alert {
  id: number
  type: string
  message: string
  severity: 'info' | 'warning' | 'critical'
  instance_id: string | null
  acknowledged: boolean
  created_at: string
}

export const monitoringApi = {
  getSystemMetrics: () => api.get<SystemMetrics>('/monitoring/system'),
  
  getInstanceMetrics: () => api.get<InstanceMetric[]>('/monitoring/instances'),
  
  getAlerts: () => api.get<{ alerts: Alert[]; count: number }>('/monitoring/alerts'),
  
  connectMetricsStream: (onMessage: (data: any) => void) => {
    const ws = new WebSocket(`ws://${window.location.host}/api/v1/monitoring/stream`)
    ws.onmessage = (event) => {
      onMessage(JSON.parse(event.data))
    }
    return ws
  },
}
