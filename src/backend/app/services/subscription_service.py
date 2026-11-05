# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 구독 안내, 주문 생성, 결제 확인(이용권 부여), 결제 내역 (인터페이스 정의서 4.6, FR-SUB-01~06)
# 파일 위치: src/backend/app/services/subscription_service.py
import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.timeutil import now_utc, to_kst
from app.core_logic.payment_rules import extend_premium_until, generate_order_id, is_amount_matching, make_customer_key
from app.models.payment import Payment
from app.models.user import User
from app.models.word import Word
from app.payments.provider import PaymentProvider, PaymentProviderUnavailable, PaymentRejected
from app.schemas.subscription import (
    ConfirmResponse,
    CurrentPlanOut,
    OrderResponse,
    PaymentItem,
    PaymentListResponse,
    PaymentOut,
    PlanOut,
    SubscriptionResponse,
)

logger = logging.getLogger("smart_voca.payments")

ORDER_NAME = "smart-voca 프리미엄 30일"


def get_subscription(db: Session, user: User) -> SubscriptionResponse:
    """요금제 목록과 내 현재 상태. 프리미엄 범위는 단어 순위의 최댓값(전체 단어)이다."""
    settings = get_settings()
    premium_word_limit = db.scalar(select(func.max(Word.frequency_rank))) or settings.free_word_limit
    is_premium = user.premium_until is not None and user.premium_until > now_utc()
    return SubscriptionResponse(
        plans=[
            PlanOut(code="free", name="무료", word_limit=settings.free_word_limit, price_krw=0, pass_days=None),
            PlanOut(
                code="premium",
                name="프리미엄",
                word_limit=premium_word_limit,
                price_krw=settings.premium_price_krw,
                pass_days=settings.premium_pass_days,
            ),
        ],
        current=CurrentPlanOut(
            plan="premium" if is_premium else "free",
            premium_until=to_kst(user.premium_until) if user.premium_until else None,
        ),
    )


def create_order(db: Session, user: User) -> OrderResponse:
    """주문 한 건을 pending 으로 만든다. 금액과 일수는 서버 설정에서 가져온다(요청에서 받지 않는다)."""
    settings = get_settings()
    payment = Payment(
        user_id=user.id,
        order_id=generate_order_id(),
        amount=settings.premium_price_krw,
        pass_days=settings.premium_pass_days,
        status="pending",
    )
    db.add(payment)
    db.commit()
    logger.info("주문 생성 user_id=%s order_id=%s amount=%s", user.id, payment.order_id, payment.amount)
    return OrderResponse(
        order_id=payment.order_id,
        order_name=ORDER_NAME,
        amount=payment.amount,
        # fake 일 때는 공개 키가 필요 없다. toss 일 때만 .env 의 공개 키를 내려 준다
        client_key="fake" if settings.payment_provider == "fake" else settings.toss_client_key,
        customer_key=make_customer_key(user.id, settings.jwt_secret),
        provider="fake" if settings.payment_provider == "fake" else "toss",
    )


def _to_confirm_response(payment: Payment, user: User, already_processed: bool) -> ConfirmResponse:
    return ConfirmResponse(
        status="paid",
        already_processed=already_processed,
        premium_until=to_kst(user.premium_until),
        payment=PaymentOut(
            order_id=payment.order_id,
            amount=payment.amount,
            approved_at=to_kst(payment.approved_at) if payment.approved_at else None,
        ),
    )


def confirm_payment(
    db: Session, user: User, provider: PaymentProvider, payment_key: str, order_id: str, amount: int
) -> ConfirmResponse:
    """결제 확인. 순서: 내 주문 → 이미 처리됨 → 금액 비교 → 결제사 승인 → (한 트랜잭션) paid + 이용권 연장."""
    # 주문 행을 잠가서(FOR UPDATE) 같은 주문의 확인 요청이 동시에 와도 한 번에 하나씩만 처리한다
    payment = db.scalar(
        select(Payment).where(Payment.order_id == order_id, Payment.user_id == user.id).with_for_update()
    )
    if payment is None:
        raise AppError(404, "ORDER_NOT_FOUND", "주문을 찾을 수 없어요.")

    if payment.status == "paid":
        # 멱등: 이미 부여했으므로 같은 결과를 다시 돌려주고 이용권은 늘리지 않는다 (IF-6)
        logger.info("결제 확인 재요청(이미 처리됨) user_id=%s order_id=%s", user.id, order_id)
        db.refresh(user)
        return _to_confirm_response(payment, user, already_processed=True)

    if payment.status in ("failed", "canceled"):
        raise AppError(402, "PAYMENT_FAILED", "결제가 완료되지 않았어요. 새로 주문해 주세요.")

    if not is_amount_matching(amount, payment.amount):
        logger.warning("결제 금액 불일치 user_id=%s order_id=%s requested=%s expected=%s", user.id, order_id, amount, payment.amount)
        raise AppError(400, "AMOUNT_MISMATCH", "결제 금액이 주문과 달라 처리하지 않았어요.")

    try:
        result = provider.confirm(payment_key, order_id, payment.amount)
    except PaymentRejected as rejected:
        payment.status = "failed"
        payment.failure_code = rejected.code
        db.commit()
        logger.info("결제 거절 user_id=%s order_id=%s code=%s", user.id, order_id, rejected.code)
        raise AppError(402, "PAYMENT_FAILED", "결제가 승인되지 않았어요. 다른 방법으로 다시 시도해 주세요.") from rejected
    except PaymentProviderUnavailable as unavailable:
        db.rollback()  # pending 유지: 결과를 모르므로 실패로 단정하지 않고 다시 확인할 수 있게 둔다
        logger.warning("결제사 통신 실패 user_id=%s order_id=%s: %s", user.id, order_id, unavailable)
        raise AppError(502, "PAYMENT_PROVIDER_ERROR", "결제 서비스에 연결할 수 없어요. 잠시 후 다시 시도해 주세요.") from unavailable

    # 같은 회원의 다른 주문과 겹쳐도 이용권 날짜가 덮어써지지 않도록 회원 행도 잠근다
    locked_user = db.scalar(select(User).where(User.id == user.id).with_for_update())
    payment.status = "paid"
    payment.payment_key = result.payment_key
    payment.approved_at = result.approved_at
    payment.failure_code = None
    locked_user.premium_until = extend_premium_until(locked_user.premium_until, now_utc(), payment.pass_days)
    db.commit()  # paid 변경과 이용권 연장이 한 번에 저장된다. 하나만 저장되는 일은 없다
    logger.info("결제 승인 user_id=%s order_id=%s premium_until=%s", user.id, order_id, locked_user.premium_until)
    return _to_confirm_response(payment, locked_user, already_processed=False)


def list_payments(db: Session, user: User, limit: int) -> PaymentListResponse:
    """내 결제 내역(최신순). pending 도 보여 준다."""
    rows = db.scalars(
        select(Payment).where(Payment.user_id == user.id).order_by(Payment.requested_at.desc(), Payment.id.desc()).limit(limit)
    ).all()
    return PaymentListResponse(
        items=[
            PaymentItem(
                order_id=row.order_id,
                amount=row.amount,
                status=row.status,
                pass_days=row.pass_days,
                requested_at=to_kst(row.requested_at),
                approved_at=to_kst(row.approved_at) if row.approved_at else None,
            )
            for row in rows
        ]
    )
