# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 구독·결제의 요청/응답 양식 (인터페이스 정의서 4.6)
# 파일 위치: src/backend/app/schemas/subscription.py
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, StrictInt


class PlanOut(BaseModel):
    code: Literal["free", "premium"]
    name: str
    word_limit: int
    price_krw: int
    pass_days: int | None


class CurrentPlanOut(BaseModel):
    plan: Literal["free", "premium"]
    premium_until: datetime | None


class SubscriptionResponse(BaseModel):
    plans: list[PlanOut]
    current: CurrentPlanOut


class OrderRequest(BaseModel):
    """주문 요청. 금액 칸이 없다: 보내도 무시되고, 금액은 서버가 정한다."""

    product: Literal["premium_30d"]


class OrderResponse(BaseModel):
    order_id: str
    order_name: str
    amount: int
    client_key: str
    customer_key: str
    # 화면이 결제위젯(toss)을 띄울지 가짜 결제 버튼(fake)을 보여줄지 정하는 데 쓴다 (인터페이스 정의서에 없던 추가 항목)
    provider: Literal["toss", "fake"]


class ConfirmRequest(BaseModel):
    """결제위젯 성공 뒤 주소에 붙어 오는 값. StrictInt: 금액은 정수만 받는다."""

    payment_key: str
    order_id: str
    amount: StrictInt


class PaymentOut(BaseModel):
    order_id: str
    amount: int
    approved_at: datetime | None


class ConfirmResponse(BaseModel):
    status: Literal["paid"]
    already_processed: bool
    premium_until: datetime
    payment: PaymentOut


class PaymentItem(BaseModel):
    order_id: str
    amount: int
    status: str
    pass_days: int
    requested_at: datetime
    approved_at: datetime | None


class PaymentListResponse(BaseModel):
    items: list[PaymentItem]
