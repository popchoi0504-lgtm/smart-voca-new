# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 가짜 결제 담당자: 테스트와 토스 연동이 막혔을 때의 대체 경로 (FR-SUB-08)
# 파일 위치: src/backend/app/payments/fake_provider.py
from datetime import datetime

from app.core.timeutil import now_utc
from app.payments.provider import ConfirmResult, PaymentProviderUnavailable, PaymentRejected


class FakePaymentProvider:
    """네트워크 없이 결과를 정해 둔 대로 돌려준다.

    outcome: "approve"(승인) / "reject"(거절) / "unavailable"(통신 실패).
    calls 에 호출 기록이 남아서, 테스트가 "결제사를 몇 번 불렀는지"를 확인할 수 있다.
    서비스에서 직접 쓰는 가짜 결제(PAYMENT_PROVIDER=fake)는 항상 승인하며, 실제 돈은 오가지 않는다.
    """

    name = "fake"

    def __init__(self, outcome: str = "approve", reject_code: str = "REJECT_CARD_COMPANY", approved_at: datetime | None = None):
        self.outcome = outcome
        self.reject_code = reject_code
        self.approved_at = approved_at
        self.calls: list[tuple[str, str, int]] = []

    def confirm(self, payment_key: str, order_id: str, amount: int) -> ConfirmResult:
        self.calls.append((payment_key, order_id, amount))
        if self.outcome == "reject":
            raise PaymentRejected(self.reject_code)
        if self.outcome == "unavailable":
            raise PaymentProviderUnavailable("가짜 결제사 통신 실패")
        return ConfirmResult(payment_key=payment_key, approved_at=self.approved_at or now_utc())
