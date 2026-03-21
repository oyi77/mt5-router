import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Position } from "@/api/trading"
import { formatNumber, formatCurrency } from "@/lib/utils"
import { X, TrendingUp, TrendingDown } from "lucide-react"

interface PositionsTableProps {
  positions: Position[]
  onClosePosition: (ticket: number) => void
  isLoading?: boolean
}

export function PositionsTable({ positions, onClosePosition, isLoading }: PositionsTableProps) {
  const totalPnL = positions.reduce((sum, pos) => sum + pos.profit, 0)

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>
          Open Positions ({positions.length})
          <span className={`ml-2 text-lg ${totalPnL >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {totalPnL >= 0 ? '+' : ''}{formatCurrency(totalPnL)}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {positions.length === 0 ? (
          <p className="text-center text-muted-foreground py-4">No open positions</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-2">Symbol</th>
                  <th className="text-left py-2 px-2">Type</th>
                  <th className="text-right py-2 px-2">Volume</th>
                  <th className="text-right py-2 px-2">Open Price</th>
                  <th className="text-right py-2 px-2">Current</th>
                  <th className="text-right py-2 px-2">P&L</th>
                  <th className="text-right py-2 px-2">SL</th>
                  <th className="text-right py-2 px-2">TP</th>
                  <th className="text-center py-2 px-2">Action</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((pos) => (
                  <tr key={pos.ticket} className="border-b hover:bg-muted/50">
                    <td className="py-2 px-2 font-medium">{pos.symbol}</td>
                    <td className="py-2 px-2">
                      <Badge variant={pos.type === 'BUY' ? 'success' : 'destructive'}>
                        {pos.type === 'BUY' ? (
                          <TrendingUp className="h-3 w-3 mr-1" />
                        ) : (
                          <TrendingDown className="h-3 w-3 mr-1" />
                        )}
                        {pos.type}
                      </Badge>
                    </td>
                    <td className="py-2 px-2 text-right font-mono">{formatNumber(pos.volume)}</td>
                    <td className="py-2 px-2 text-right font-mono">{formatNumber(pos.open_price)}</td>
                    <td className="py-2 px-2 text-right font-mono">{formatNumber(pos.current_price)}</td>
                    <td className={`py-2 px-2 text-right font-mono ${pos.profit >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {pos.profit >= 0 ? '+' : ''}{formatCurrency(pos.profit)}
                    </td>
                    <td className="py-2 px-2 text-right font-mono text-muted-foreground">
                      {pos.sl ? formatNumber(pos.sl) : '-'}
                    </td>
                    <td className="py-2 px-2 text-right font-mono text-muted-foreground">
                      {pos.tp ? formatNumber(pos.tp) : '-'}
                    </td>
                    <td className="py-2 px-2 text-center">
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => onClosePosition(pos.ticket)}
                        disabled={isLoading}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
