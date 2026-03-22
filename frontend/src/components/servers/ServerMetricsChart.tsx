import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { monitoringApi, ServerMetricsHistory } from '@/api/monitoring'
import { MiniChart, ChartDataPoint } from '@/components/charts/MiniChart'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

interface ServerMetricsChartProps {
  serverId: number
}

const TIME_RANGES = [
  { label: '1h', hours: 1 },
  { label: '6h', hours: 6 },
  { label: '24h', hours: 24 },
  { label: '7d', hours: 168 },
] as const

function toChartData(
  metrics: ServerMetricsHistory[],
  accessor: (m: ServerMetricsHistory) => number
): ChartDataPoint[] {
  return metrics.map((m) => ({
    time: m.recorded_at,
    value: accessor(m),
  }))
}

export function ServerMetricsChart({ serverId }: ServerMetricsChartProps) {
  const [hours, setHours] = useState(24)

  const { data: metrics = [], isLoading } = useQuery({
    queryKey: ['serverMetricsHistory', serverId, hours],
    queryFn: () => monitoringApi.getServerMetricsHistory(serverId, hours),
    refetchInterval: 60000,
  })

  const latestMetric = metrics.length > 0 ? metrics[metrics.length - 1] : null

  if (isLoading) {
    return (
      <div className="space-y-4 pt-4">
        <div className="flex gap-2">
          {TIME_RANGES.map((r) => (
            <Skeleton key={r.label} className="h-8 w-12" />
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="h-44" />
          <Skeleton className="h-44" />
          <Skeleton className="h-44" />
        </div>
      </div>
    )
  }

  const cpuData = toChartData(metrics, (m) => m.cpu_percent)
  const memoryData = toChartData(metrics, (m) =>
    m.memory_total_mb > 0 ? (m.memory_used_mb / m.memory_total_mb) * 100 : 0
  )
  const diskData = toChartData(metrics, (m) =>
    m.disk_total_gb > 0 ? (m.disk_used_gb / m.disk_total_gb) * 100 : 0
  )

  return (
    <div className="space-y-4 pt-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-1">
          {TIME_RANGES.map((range) => (
            <Button
              key={range.label}
              size="sm"
              variant={hours === range.hours ? 'default' : 'outline'}
              onClick={() => setHours(range.hours)}
              className="h-7 px-2.5 text-xs"
            >
              {range.label}
            </Button>
          ))}
        </div>
        {latestMetric && (
          <Badge variant="outline" className="text-xs">
            {latestMetric.docker_containers_running} / {latestMetric.docker_containers_total} containers
          </Badge>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MiniChart data={cpuData} label="CPU Usage" color="green" unit="%" />
        <MiniChart data={memoryData} label="Memory Usage" color="blue" unit="%" />
        <MiniChart data={diskData} label="Disk Usage" color="orange" unit="%" />
      </div>
    </div>
  )
}
