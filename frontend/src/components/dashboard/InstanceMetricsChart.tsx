import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { monitoringApi, InstanceMetricsHistory } from '@/api/monitoring'
import { MiniChart, ChartDataPoint } from '@/components/charts/MiniChart'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'

interface InstanceMetricsChartProps {
  instanceId: string
}

const TIME_RANGES = [
  { label: '1h', hours: 1 },
  { label: '6h', hours: 6 },
  { label: '24h', hours: 24 },
] as const

function toChartData(
  metrics: InstanceMetricsHistory[],
  accessor: (m: InstanceMetricsHistory) => number
): ChartDataPoint[] {
  return metrics.map((m) => ({
    time: m.recorded_at,
    value: accessor(m),
  }))
}

export function InstanceMetricsChart({ instanceId }: InstanceMetricsChartProps) {
  const [hours, setHours] = useState(24)

  const { data: metrics = [], isLoading } = useQuery({
    queryKey: ['instanceMetricsHistory', instanceId, hours],
    queryFn: () => monitoringApi.getInstanceMetricsHistory(instanceId, hours),
    refetchInterval: 60000,
  })

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
  const memoryData = toChartData(metrics, (m) => m.memory_usage_mb)
  const networkData = toChartData(metrics, (m) => m.network_rx_mb)

  return (
    <div className="space-y-4 pt-4">
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

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MiniChart data={cpuData} label="CPU Usage" color="green" unit="%" />
        <MiniChart data={memoryData} label="Memory Usage" color="blue" unit=" MB" />
        <MiniChart data={networkData} label="Network RX" color="purple" unit=" MB" />
      </div>
    </div>
  )
}
