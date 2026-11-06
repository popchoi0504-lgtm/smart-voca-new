# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 구독 안내·주문·결제 확인·결제 내역 API (인터페이스 정의서 4.6)
# 파일 위치: src/backend/app/routers/subscription.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.payments.provider import PaymentProvider, get_payment_provider
from app.schemas.subscription import (
    ConfirmRequest,
    ConfirmResponse,
    OrderRequest,
    OrderResponse,
    PaymentListResponse,
    RefundResponse,
    SubscriptionResponse,
)
from app.services import subscription_service

subscription_router = APIRouter(prefix="/subscription", tags=["구독"])
payments_router = APIRouter(prefix="/payments", tags=["결제"])


@subscription_router.get("", response_model=SubscriptionResponse)
def subscription(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return subscription_service.get_subscription(db, current_user)


@payments_router.post("/orders", response_model=OrderResponse)
def create_order(body: OrderRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return subscription_service.create_order(db, current_user)


@payments_router.post("/confirm", response_model=ConfirmResponse)
def confirm(
    body: ConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    provider: PaymentProvider = Depends(get_payment_provider),
):
    return subscription_service.confirm_payment(db, current_user, provider, body.payment_key, body.order_id, body.amount)


@payments_router.post("/{order_id}/refund", response_model=RefundResponse)
def refund(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    provider: PaymentProvider = Depends(get_payment_provider),
):
    return subscription_service.refund_payment(db, current_user, provider, order_id)


@payments_router.get("", response_model=PaymentListResponse)
def list_payments(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return subscription_service.list_payments(db, current_user, limit)
