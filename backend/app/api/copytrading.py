from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.core.database import get_db
from app.models.database import (
    CopyStrategy,
    CopySubscriber,
    CopySignal,
    CopyPosition,
    User,
)
from app.auth.jwt import get_current_user

router = APIRouter(prefix="/api/v1/copy", tags=["Copy Trading"])
logger = logging.getLogger(__name__)


class StrategyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    source_account_id: int
    symbol_filter: Optional[str] = None
    max_lots: float = 1.0


class StrategyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    source_account_id: int
    is_active: bool
    symbol_filter: Optional[str]
    max_lots: float
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriberCreate(BaseModel):
    strategy_id: int
    target_account_id: int
    lot_multiplier: float = 1.0
    lot_type: str = "fixed"


class SubscriberResponse(BaseModel):
    id: int
    strategy_id: int
    target_account_id: int
    is_active: bool
    lot_multiplier: float
    lot_type: str
    created_at: datetime

    class Config:
        from_attributes = True


def strategy_to_response(s: CopyStrategy) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "description": s.description,
        "source_account_id": s.source_account_id,
        "is_active": s.is_active,
        "symbol_filter": s.symbol_filter,
        "max_lots": s.max_lots,
        "created_at": s.created_at,
    }


def subscriber_to_response(s: CopySubscriber) -> dict:
    return {
        "id": s.id,
        "strategy_id": s.strategy_id,
        "target_account_id": s.target_account_id,
        "is_active": s.is_active,
        "lot_multiplier": s.lot_multiplier,
        "lot_type": s.lot_type,
        "created_at": s.created_at,
    }


@router.post("/strategies", response_model=StrategyResponse)
async def create_strategy(
    request: StrategyCreate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = user.get("id")
    strategy = CopyStrategy(
        user_id=user_id,
        name=request.name,
        description=request.description,
        source_account_id=request.source_account_id,
        symbol_filter=request.symbol_filter,
        max_lots=request.max_lots,
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy_to_response(strategy)


@router.get("/strategies", response_model=List[StrategyResponse])
async def list_strategies(
    user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    user_id = user.get("id")
    strategies = db.query(CopyStrategy).filter(CopyStrategy.user_id == user_id).all()
    return [strategy_to_response(s) for s in strategies]


@router.get("/strategies/{id}", response_model=StrategyResponse)
async def get_strategy(
    id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    user_id = user.get("id")
    strategy = (
        db.query(CopyStrategy)
        .filter(CopyStrategy.id == id, CopyStrategy.user_id == user_id)
        .first()
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy_to_response(strategy)


@router.put("/strategies/{id}", response_model=StrategyResponse)
async def update_strategy(
    id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = user.get("id")
    strategy = (
        db.query(CopyStrategy)
        .filter(CopyStrategy.id == id, CopyStrategy.user_id == user_id)
        .first()
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    if name is not None:
        strategy.name = name
    if description is not None:
        strategy.description = description
    if is_active is not None:
        strategy.is_active = is_active

    db.commit()
    db.refresh(strategy)
    return strategy_to_response(strategy)


@router.delete("/strategies/{id}")
async def delete_strategy(
    id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    user_id = user.get("id")
    strategy = (
        db.query(CopyStrategy)
        .filter(CopyStrategy.id == id, CopyStrategy.user_id == user_id)
        .first()
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    db.delete(strategy)
    db.commit()
    return {"message": "Strategy deleted"}


@router.post("/subscribers", response_model=SubscriberResponse)
async def create_subscriber(
    request: SubscriberCreate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = user.get("id")

    strategy = (
        db.query(CopyStrategy).filter(CopyStrategy.id == request.strategy_id).first()
    )
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    subscriber = CopySubscriber(
        user_id=user_id,
        strategy_id=request.strategy_id,
        target_account_id=request.target_account_id,
        lot_multiplier=request.lot_multiplier,
        lot_type=request.lot_type,
    )
    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)
    return subscriber_to_response(subscriber)


@router.get("/subscribers", response_model=List[SubscriberResponse])
async def list_subscribers(
    user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    user_id = user.get("id")
    subscribers = (
        db.query(CopySubscriber).filter(CopySubscriber.user_id == user_id).all()
    )
    return [subscriber_to_response(s) for s in subscribers]


@router.delete("/subscribers/{id}")
async def delete_subscriber(
    id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    user_id = user.get("id")
    subscriber = (
        db.query(CopySubscriber)
        .filter(CopySubscriber.id == id, CopySubscriber.user_id == user_id)
        .first()
    )
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    db.delete(subscriber)
    db.commit()
    return {"message": "Subscriber deleted"}
