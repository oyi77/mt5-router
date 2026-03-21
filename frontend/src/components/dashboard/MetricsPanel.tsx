import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { formatBytes } from '@/lib/utils'
import { SystemMetrics, InstanceMetric } from '@/api/monitoring'
import { Cpu, HardDrive, MemoryStick, Server } from 'lucide-react'

interface MetricsPanelProps {
  systemMetrics: SystemMetrics | null
  instanceMetrics: InstanceMetric[]
  isLoading?: boolean
}

export function MetricsPanel({ systemMetrics, instanceMetrics, isLoading }: MetricsPanelProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="pb-2">
              <div className="h-4 w-24 bg-muted rounded" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-16 bg-muted rounded mb-2" />
              <div className="h-2 w-full bg-muted rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (!systemMetrics) return null

  const cpuVariant = systemMetrics.cpu_percent > 80 ? 'danger' : systemMetrics.cpu_percent > 50 ? 'warning' : 'default'
  const memVariant = systemMetrics.memory.percent > 80 ? 'danger' : systemMetrics.memory.percent > 50 ? 'warning' : 'default'
  const diskVariant = systemMetrics.disk.percent > 80 ? 'danger' : systemMetrics.disk.percent > 50 ? 'warning' : 'default'

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.cpu_percent.toFixed(1)}%</div>
            <Progress value={systemMetrics.cpu_percent} variant={cpuVariant} className="mt-2 h-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Memory</CardTitle>
            <MemoryStick className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.memory.percent.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              {formatBytes(systemMetrics.memory.used)} / {formatBytes(systemMetrics.memory.total)}
            </p>
            <Progress value={systemMetrics.memory.percent} variant={memVariant} className="mt-2 h-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Disk</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.disk.percent.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              {formatBytes(systemMetrics.disk.used)} / {formatBytes(systemMetrics.disk.total)}
            </p>
            <Progress value={systemMetrics.disk.percent} variant={diskVariant} className="mt-2 h-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Instances</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{instanceMetrics.length}</div>
            <p className="text-xs text-muted-foreground">
              {instanceMetrics.filter(i => i.status === 'running').length} running
            </p>
          </CardContent>
        </Card>
      </div>

      {instanceMetrics.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Instance Resources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {instanceMetrics.map((instance) => (
                <div key={instance.id} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{instance.name}</span>
                    <span className="text-sm text-muted-foreground">{instance.status}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-muted-foreground">CPU</span>
                        <span>{instance.cpu_percent.toFixed(1)}%</span>
                      </div>
                      <Progress
                        value={instance.cpu_percent}
                        variant={instance.cpu_percent > 80 ? 'danger' : instance.cpu_percent > 50 ? 'warning' : 'default'}
                        className="h-1"
                      />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-muted-foreground">Memory</span>
                        <span>{instance.memory_percent.toFixed(1)}%</span>
                      </div>
                      <Progress
                        value={instance.memory_percent}
                        variant={instance.memory_percent > 80 ? 'danger' : instance.memory_percent > 50 ? 'warning' : 'default'}
                        className="h-1"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
