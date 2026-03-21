import { api } from './client'

export interface TradeStatistics {
  total_trades: number
  winning_trades: number
  losing_trades: number
  win_rate: number
  total_profit: number
  total_loss: number
  net_profit: number
  profit_factor: number
  average_win: number
  average_loss: number
  largest_win: number
  largest_loss: number
  average_trade_duration: number
  max_drawdown: number
  sharpe_ratio?: number
}

export interface DailySummary {
  date: string
  trades: number
  profit: number
  wins: number
  losses: number
}

export interface SymbolStats {
  symbol: string
  trades: number
  win_rate: number
  net_profit: number
  total_volume: number
}

export interface EquityPoint {
  timestamp: string
  equity: number
  balance: number
}

export const statisticsApi = {
  getSummary: (instanceId: string, days: number = 30) =>
    api.get<TradeStatistics>(`/stats/summary?instance_id=${instanceId}&days=${days}`),

  getDaily: (instanceId: string, days: number = 30) =>
    api.get<DailySummary[]>(`/stats/daily?instance_id=${instanceId}&days=${days}`),

  getSymbols: (instanceId: string, days: number = 30) =>
    api.get<SymbolStats[]>(`/stats/symbols?instance_id=${instanceId}&days=${days}`),

  getEquityCurve: (instanceId: string, days: number = 30) =>
    api.get<EquityPoint[]>(`/stats/equity-curve?instance_id=${instanceId}&days=${days}`),
}