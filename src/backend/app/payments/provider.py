# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 결제 담당자(provider)의 공통 모양과 선택 함수 (FR-SUB-03·08)
# 파일 위치: src/backend/app/payments/provider.py
# 서비스 로직은 "결제사에 승인 확인"만 알고, 결제사가 토스인지 가짜인지는 모른다 → 결제 부분을 갈아 끼울 수 있다.
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.core.config import get_settings
from app.core.errors import AppError


@dataclass(frozen=True)
class ConfirmResult:
    """결제사가 승인했을 때 돌려준 정보."""

    payment_key: str
    approved_at: datetime


class PaymentRejected(Exception):
    """결제사가 승인을 거절했다(카드 한도 초과, 이미 처리된 결제 등). 결제는 실패로 기록한다."""

    def __init__(self, code: str, message: str = ""):
        super().__init__(message or code)
        self.code = code


class PaymentProviderUnavailable(Exception):
    """결제사와 통신이 안 됐거나 일시 오류. 결제 결과를 모르므로 pending 으로 두고 다시 확인할 수 있게 한다."""


class PaymentProvider(Protocol):
    """결제 담당자가 지켜야 할 모양. confirm 하나뿐이다."""

    name: str

    def confirm(self, payment_key: str, order_id: str, amount: int) -> ConfirmResult:
        """결제사에 승인 확인을 요청한다. 거절이면 PaymentRejected, 통신 실패면 PaymentProviderUnavailable."""
        ...


def get_payment_provider() -> PaymentProvider:
    """설정(PAYMENT_PROVIDER)에 따라 담당자를 고른다. FastAPI 의존성으로 쓰며, 테스트는 이 함수를 바꿔 끼운다."""
    settings = get_settings()
    if settings.payment_provider == "fake":
        from app.payments.fake_provider import FakePaymentProvider

        return FakePaymentProvider()
    from app.payments.toss_provider import TossPaymentProvider

    try:
        return TossPaymentProvider(secret_key=settings.toss_secret_key)
    except PaymentProviderUnavailable as error:
        # 키가 없는 설정 오류도 사용자에게는 같은 모양의 502 로 보여 준다
        raise AppError(502, "PAYMENT_PROVIDER_ERROR", "결제 서비스에 연결할 수 없어요. 잠시 후 다시 시도해 주세요.") from error
