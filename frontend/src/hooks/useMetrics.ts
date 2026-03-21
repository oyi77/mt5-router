import { useState, useEffect } from 'react'
import { monitoringApi, SystemMetrics, InstanceMetric } from '@/api/monitoring'

export function useMetrics(refetchInterval = 10000) {
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null)
  const [instanceMetrics, setInstanceMetrics] = useState<InstanceMetric[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchMetrics = async () => {
    try {
      const [system, instances] = await Promise.all([
        monitoringApi.getSystemMetrics(),
        monitoringApi.getInstanceMetrics(),
      ])
      setSystemMetrics(system)
      setInstanceMetrics(instances)
      setError(null)
    } catch (err) {
      setError(err as Error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchMetrics()
    const interval = setInterval(fetchMetrics, refetchInterval)
    return () => clearInterval(interval)
  }, [refetchInterval])

  return { systemMetrics, instanceMetrics, isLoading, error, refetch: fetchMetrics }
}
