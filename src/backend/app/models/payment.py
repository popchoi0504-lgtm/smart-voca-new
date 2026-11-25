# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - payments 표(결제 내역) 모델 (데이터 설계서 4.5, DD-6·DD-7, FR-SUB-02~06)
# 파일 위치: src/backend/app/models/payment.py
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, Integer, SmallInteger, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.timeutil import now_utc
from app.models.base import Base, BigIntId, UtcDateTime


class Payment(Base):
    """주문 하나당 행 하나. 주문을 만들 때 pending 으로 시작해서 결제 확인 결과에 따라 paid/failed 가 된다."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(BigIntId, primary_key=True)
    # ondelete 를 지정하지 않음: 회원을 지워도 결제 기록은 남기는 방향(DD-6). 기록이 있으면 회원 삭제가 막힌다.
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))

    # 서버가 만든 주문번호. UNIQUE → 같은 주문번호가 두 번 만들어지지 못하게 DB 가 막는다 (FR-SUB-06)
    order_id: Mapped[str] = mapped_column(Text, unique=True)
    # 결제사가 준 결제 키. 결제 확인 뒤에 채워지므로 처음엔 비어 있다. 값이 있으면 UNIQUE (NULL 은 여러 개 가능)
    payment_key: Mapped[str | None] = mapped_column(Text, unique=True)

    # 서버가 정한 금액(원). 요청 본문의 금액은 믿지 않는다
    amount: Mapped[int] = mapped_column(Integer)
    # 이 결제로 늘어나는 이용권 일수
    pass_days: Mapped[int] = mapped_column(SmallInteger)

    status: Mapped[str] = mapped_column(Text, server_default="pending")
    requested_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=now_utc, server_default=func.now())
    approved_at: Mapped[datetime | None] = mapped_column(UtcDateTime())
    # 실패했을 때 결제사 오류 코드
    failure_code: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("ix_payments_user_id_requested_at", "user_id", "requested_at"),
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("pass_days > 0", name="pass_days_positive"),
        CheckConstraint("status IN ('pending', 'paid', 'failed', 'canceled')", name="status_allowed"),
    )
