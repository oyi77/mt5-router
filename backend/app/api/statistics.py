from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.models.database import MT5Account
from app.auth.jwt import get_current_user
from app.services.mt5_service import MT5Service

router = APIRouter(prefix="/api/v1/stats", tags=["Trading Statistics"])
logger = logging.getLogger(__name__)


class TradeStatistics(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit: float
    total_loss: float
    net_profit: float
    profit_factor: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    average_trade_duration: float
    max_drawdown: float
    sharpe_ratio: Optional[float]


class DailySummary(BaseModel):
    date: str
    trades: int
    profit: float
    wins: int
    losses: int


class SymbolStats(BaseModel):
    symbol: str
    trades: int
    win_rate: float
    net_profit: float
    total_volume: float


class EquityPoint(BaseModel):
    timestamp: str
    equity: float
    balance: float


@router.get("/summary", response_model=TradeStatistics)
async def get_statistics(
    instance_id: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    user: dict = Depends(get_current_user),
):
    try:
        mt5 = MT5Service(instance_id)

        deals = mt5.get_deals_history(days=days)
        if not deals:
            return TradeStatistics(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0,
                total_profit=0,
                total_loss=0,
                net_profit=0,
                profit_factor=0,
                average_win=0,
                average_loss=0,
                largest_win=0,
                largest_loss=0,
                average_trade_duration=0,
                max_drawdown=0,
                sharpe_ratio=None,
            )

        winning = [d for d in deals if float(d.get("profit", 0)) > 0]
        losing = [d for d in deals if float(d.get("profit", 0)) < 0]

        total_profit = sum(float(d.get("profit", 0)) for d in winning)
        total_loss = abs(sum(float(d.get("profit", 0)) for d in losing))

        avg_win = total_profit / len(winning) if winning else 0
        avg_loss = total_loss / len(losing) if losing else 0

        largest_win = max((float(d.get("profit", 0)) for d in winning), default=0)
        largest_loss = min((float(d.get("profit", 0)) for d in losing), default=0)

        profit_factor = (
            (total_profit / total_loss)
            if total_loss > 0
            else float("inf")
            if total_profit > 0
            else 0
        )

        equity_curve = []
        running = 0
        max_equity = 0
        max_dd = 0
        for deal in sorted(deals, key=lambda x: x.get("time", "")):
            running += float(deal.get("profit", 0))
            equity_curve.append(running)
            if running > max_equity:
                max_equity = running
            dd = max_equity - running
            if dd > max_dd:
                max_dd = dd

        return TradeStatistics(
            total_trades=len(deals),
            winning_trades=len(winning),
            losing_trades=len(losing),
            win_rate=len(winning) / len(deals) * 100 if deals else 0,
            total_profit=total_profit,
            total_loss=total_loss,
            net_profit=total_profit - total_loss,
            profit_factor=profit_factor,
            average_win=avg_win,
            average_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            average_trade_duration=0,
            max_drawdown=max_dd,
            sharpe_ratio=None,
        )

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily", response_model=List[DailySummary])
async def get_daily_summary(
    instance_id: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    user: dict = Depends(get_current_user),
):
    try:
        mt5 = MT5Service(instance_id)
        deals = mt5.get_deals_history(days=days)

        daily = {}
        for deal in deals:
            date = deal.get("time", "")[:10]
            if date not in daily:
                daily[date] = {"trades": 0, "profit": 0, "wins": 0, "losses": 0}
            daily[date]["trades"] += 1
            profit = float(deal.get("profit", 0))
            daily[date]["profit"] += profit
            if profit > 0:
                daily[date]["wins"] += 1
            else:
                daily[date]["losses"] += 1

        result = [
            DailySummary(
                date=date,
                trades=data["trades"],
                profit=data["profit"],
                wins=data["wins"],
                losses=data["losses"],
            )
            for date, data in sorted(daily.items())
        ]

        return result

    except Exception as e:
        logger.error(f"Error getting daily summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symbols", response_model=List[SymbolStats])
async def get_symbol_stats(
    instance_id: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    user: dict = Depends(get_current_user),
):
    try:
        mt5 = MT5Service(instance_id)
        deals = mt5.get_deals_history(days=days)

        symbol_data = {}
        for deal in deals:
            symbol = deal.get("symbol", "UNKNOWN")
            if symbol not in symbol_data:
                symbol_data[symbol] = {"trades": 0, "wins": 0, "profit": 0, "volume": 0}

            profit = float(deal.get("profit", 0))
            volume = float(deal.get("volume", 0))

            symbol_data[symbol]["trades"] += 1
            symbol_data[symbol]["profit"] += profit
            symbol_data[symbol]["volume"] += volume
            if profit > 0:
                symbol_data[symbol]["wins"] += 1

        result = [
            SymbolStats(
                symbol=symbol,
                trades=data["trades"],
                win_rate=data["wins"] / data["trades"] * 100 if data["trades"] else 0,
                net_profit=data["profit"],
                total_volume=data["volume"],
            )
            for symbol, data in symbol_data.items()
        ]

        return sorted(result, key=lambda x: abs(x.net_profit), reverse=True)

    except Exception as e:
        logger.error(f"Error getting symbol stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/equity-curve", response_model=List[EquityPoint])
async def get_equity_curve(
    instance_id: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    user: dict = Depends(get_current_user),
):
    try:
        mt5 = MT5Service(instance_id)

        account_info = mt5.get_account_info()
        current_equity = float(account_info.get("equity", 0)) if account_info else 0

        deals = mt5.get_deals_history(days=days)

        sorted_deals = sorted(deals, key=lambda x: x.get("time", ""))

        equity_points = []
        running = current_equity

        for deal in reversed(sorted_deals):
            profit = float(deal.get("profit", 0))
            running -= profit
            equity_points.append(
                EquityPoint(
                    timestamp=deal.get("time", ""),
                    equity=round(running, 2),
                    balance=round(running + profit, 2),
                )
            )

        if equity_points:
            equity_points.append(
                EquityPoint(
                    timestamp=datetime.utcnow().isoformat(),
                    equity=round(current_equity, 2),
                    balance=round(current_equity, 2),
                )
            )

        return sorted(equity_points, key=lambda x: x.timestamp)

    except Exception as e:
        logger.error(f"Error getting equity curve: {e}")
        raise HTTPException(status_code=500, detail=str(e))
