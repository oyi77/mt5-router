import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { Instance, InstanceStats } from '@/api/instances'
import { Play, Square, RotateCcw, Trash2, Monitor, Terminal } from 'lucide-react'

interface InstanceCardProps {
  instance: Instance
  stats?: InstanceStats
  onStart?: () => void
  onStop?: () => void
  onRestart?: () => void
  onDelete?: () => void
  onVNC?: () => void
  onLogs?: () => void
  className?: string
}

export function InstanceCard({
  instance,
  stats,
  onStart,
  onStop,
  onRestart,
  onDelete,
  onVNC,
  onLogs,
  className,
}: InstanceCardProps) {
  const statusVariant = {
    running: 'success',
    stopped: 'destructive',
    restarting: 'warning',
    created: 'secondary',
  } as const

  const statusDotClass = {
    running: 'status-running',
    stopped: 'status-stopped',
    restarting: 'status-restarting',
    created: 'bg-gray-500',
  }

  return (
    <Card className={cn('', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={cn('status-dot', statusDotClass[instance.status])} />
            <CardTitle className="text-lg">{instance.name}</CardTitle>
          </div>
          <Badge variant={statusVariant[instance.status]}>
            {instance.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {stats && (
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-muted-foreground">CPU</span>
                <span>{stats.cpu_percent.toFixed(1)}%</span>
              </div>
              <Progress
                value={stats.cpu_percent}
                variant={stats.cpu_percent > 80 ? 'danger' : stats.cpu_percent > 50 ? 'warning' : 'default'}
                className="h-2"
              />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-muted-foreground">Memory</span>
                <span>{stats.memory_usage_mb.toFixed(0)} / {stats.memory_limit_mb.toFixed(0)} MB</span>
              </div>
              <Progress
                value={stats.memory_percent}
                variant={stats.memory_percent > 80 ? 'danger' : stats.memory_percent > 50 ? 'warning' : 'default'}
                className="h-2"
              />
            </div>
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          {instance.status === 'stopped' && onStart && (
            <Button size="sm" variant="outline" onClick={onStart}>
              <Play className="h-4 w-4 mr-1" />
              Start
            </Button>
          )}
          {instance.status === 'running' && onStop && (
            <Button size="sm" variant="outline" onClick={onStop}>
              <Square className="h-4 w-4 mr-1" />
              Stop
            </Button>
          )}
          {instance.status === 'running' && onRestart && (
            <Button size="sm" variant="outline" onClick={onRestart}>
              <RotateCcw className="h-4 w-4 mr-1" />
              Restart
            </Button>
          )}
          {instance.vnc_port && onVNC && (
            <Button size="sm" variant="outline" onClick={onVNC}>
              <Monitor className="h-4 w-4 mr-1" />
              VNC
            </Button>
          )}
          {onLogs && (
            <Button size="sm" variant="outline" onClick={onLogs}>
              <Terminal className="h-4 w-4 mr-1" />
              Logs
            </Button>
          )}
          {onDelete && (
            <Button size="sm" variant="destructive" onClick={onDelete}>
              <Trash2 className="h-4 w-4 mr-1" />
              Delete
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
