import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { LucideIcon } from 'lucide-react'

interface MetricsCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: LucideIcon
  progress?: number
  variant?: 'default' | 'success' | 'warning' | 'danger'
  className?: string
}

export function MetricsCard({
  title,
  value,
  subtitle,
  icon: Icon,
  progress,
  variant = 'default',
  className,
}: MetricsCardProps) {
  const variantColors = {
    default: 'text-primary',
    success: 'text-green-500',
    warning: 'text-yellow-500',
    danger: 'text-red-500',
  }

  return (
    <Card className={cn('', className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={cn('h-4 w-4', variantColors[variant])} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {subtitle && (
          <p className="text-xs text-muted-foreground">{subtitle}</p>
        )}
        {progress !== undefined && (
          <Progress
            value={progress}
            variant={variant === 'default' ? 'default' : variant}
            className="mt-2 h-2"
          />
        )}
      </CardContent>
    </Card>
  )
}
