from fastapi import APIRouter, HTTPException, WebSocket, Depends, Query
from typing import List, Optional
from pydantic import BaseModel
import asyncio
import logging

from app.auth.jwt import get_current_user
from app.services.mt5_service import MT5Service

router = APIRouter()
logger = logging.getLogger(__name__)


class OrderRequest(BaseModel):
    symbol: str
    order_type: str
    volume: float
    price: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    magic: int = 234000
    comment: str = "mt5-router"


class OrderResponse(BaseModel):
    ticket: int
    symbol: str
    order_type: str
    volume: float
    price: float
    sl: Optional[float]
    tp: Optional[float]
    status: str


@router.get("/account")
async def get_account_info(
    instance_id: str = Query(...), user: dict = Depends(get_current_user)
):
    try:
        mt5 = MT5Service(instance_id)
        account = mt5.get_account_info()
        if not account:
            raise HTTPException(status_code=503, detail="MT5 not connected")
        return account
    except Exception as e:
        logger.error(f"Error getting account info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_positions(
    instance_id: str = Query(...),
    symbol: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    try:
        mt5 = MT5Service(instance_id)
        positions = mt5.get_positions(symbol)
        return positions
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders")
async def place_order(
    order: OrderRequest,
    instance_id: str = Query(...),
    user: dict = Depends(get_current_user),
):
    try:
        mt5 = MT5Service(instance_id)
        result = mt5.place_order(
            symbol=order.symbol,
            order_type=order.order_type,
            volume=order.volume,
            price=order.price,
            sl=order.sl,
            tp=order.tp,
            magic=order.magic,
            comment=order.comment,
        )
        if not result:
            raise HTTPException(status_code=400, detail="Order failed")
        return result
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders")
async def get_orders(
    instance_id: str = Query(...),
    symbol: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    try:
        mt5 = MT5Service(instance_id)
        orders = mt5.get_pending_orders(symbol)
        return orders
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/orders/{ticket}")
async def cancel_order(
    ticket: int, instance_id: str = Query(...), user: dict = Depends(get_current_user)
):
    try:
        mt5 = MT5Service(instance_id)
        success = mt5.cancel_pending_order(ticket)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to cancel order")
        return {"status": "cancelled", "ticket": ticket}
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/positions/{ticket}/close")
async def close_position(
    ticket: int, instance_id: str = Query(...), user: dict = Depends(get_current_user)
):
    try:
        mt5 = MT5Service(instance_id)
        success = mt5.close_position(ticket)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to close position")
        return {"status": "closed", "ticket": ticket}
    except Exception as e:
        logger.error(f"Error closing position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symbols/{symbol}")
async def get_symbol_info(
    symbol: str, instance_id: str = Query(...), user: dict = Depends(get_current_user)
):
    try:
        mt5 = MT5Service(instance_id)
        info = mt5.get_symbol_info(symbol)
        if not info:
            raise HTTPException(status_code=404, detail="Symbol not found")
        return info
    except Exception as e:
        logger.error(f"Error getting symbol info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(
    instance_id: str = Query(...),
    symbol: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    user: dict = Depends(get_current_user),
):
    try:
        mt5 = MT5Service(instance_id)
        history = mt5.get_history_deals(symbol, days)
        return history
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
