import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { formatCurrency, formatNumber } from '@/lib/utils'
import { AccountInfo } from '@/api/trading'
import { Wallet, TrendingUp, Shield, Server } from 'lucide-react'

interface AccountCardProps {
  account: AccountInfo | null
  className?: string
}

export function AccountCard({ account, className }: AccountCardProps) {
  if (!account) {
    return (
      <Card className={className}>
        <CardContent className="py-8">
          <p className="text-center text-muted-foreground">No account data available. Select an instance to view trading info.</p>
        </CardContent>
      </Card>
    )
  }

  const marginLevelVariant = account.margin_level > 200 ? 'success' : account.margin_level > 100 ? 'warning' : 'destructive'

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Wallet className="h-5 w-5" />
            Account #{account.login}
          </CardTitle>
          <Badge variant="outline">{account.server}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Balance</p>
            <p className="text-xl font-bold">{formatCurrency(account.balance, account.currency)}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Equity</p>
            <p className="text-xl font-bold">{formatCurrency(account.equity, account.currency)}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Free Margin</p>
            <p className="text-xl font-bold">{formatCurrency(account.free_margin, account.currency)}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Margin Level</p>
            <div className="flex items-center gap-2">
              <p className="text-xl font-bold">{formatNumber(account.margin_level, 1)}%</p>
              <Badge variant={marginLevelVariant}>
                {account.margin_level > 200 ? 'Safe' : account.margin_level > 100 ? 'Warning' : 'Danger'}
              </Badge>
            </div>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <TrendingUp className="h-4 w-4 shrink-0" />
            <span>Leverage: 1:{account.leverage}</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Shield className="h-4 w-4 shrink-0" />
            <span className="truncate">{account.name}</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Server className="h-4 w-4 shrink-0" />
            <span>{account.currency}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
