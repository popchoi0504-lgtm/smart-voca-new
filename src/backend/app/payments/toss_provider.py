# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 토스페이먼츠 결제 승인 API 호출 담당자 (FR-SUB-02·03)
# 파일 위치: src/backend/app/payments/toss_provider.py
# 근거: 토스 공식 문서(2026-11-05 확인) POST https://api.tosspayments.com/v1/payments/confirm
import base64
from datetime import datetime

import httpx

from app.payments.provider import ConfirmResult, PaymentProviderUnavailable, PaymentRejected

CONFIRM_URL = "https://api.tosspayments.com/v1/payments/confirm"
TIMEOUT_SECONDS = 10.0


class TossPaymentProvider:
    name = "toss"

    def __init__(self, secret_key: str):
        if not secret_key:
            raise PaymentProviderUnavailable("TOSS_SECRET_KEY 가 설정되지 않았습니다.")
        # 인증: base64("시크릿키:") — 끝의 콜론을 빠뜨리면 토스가 거부한다
        self._auth_header = "Basic " + base64.b64encode(f"{secret_key}:".encode("utf-8")).decode("ascii")

    def confirm(self, payment_key: str, order_id: str, amount: int) -> ConfirmResult:
        try:
            response = httpx.post(
                CONFIRM_URL,
                json={"paymentKey": payment_key, "orderId": order_id, "amount": amount},
                headers={
                    "Authorization": self._auth_header,
                    # 같은 주문의 확인 요청이 겹쳐도 토스가 첫 응답을 그대로 돌려주게 한다
                    "Idempotency-Key": order_id,
                },
                timeout=TIMEOUT_SECONDS,
            )
        except httpx.HTTPError as error:
            raise PaymentProviderUnavailable("토스 통신 실패") from error

        try:
            body = response.json()
        except ValueError as error:
            raise PaymentProviderUnavailable("토스 응답을 읽을 수 없음") from error

        if response.status_code == 200:
            # 승인 완료는 status == DONE. 그 밖의 상태는 부여 근거로 삼지 않는다
            if body.get("status") != "DONE" or body.get("totalAmount") != amount or body.get("orderId") != order_id:
                raise PaymentRejected("UNEXPECTED_PAYMENT_STATE", "승인 응답이 예상과 다름")
            return ConfirmResult(payment_key=body["paymentKey"], approved_at=datetime.fromisoformat(body["approvedAt"]))

        code = str(body.get("code", "UNKNOWN"))
        # 5xx 와 일시 오류는 결과를 모르는 상태 → 다시 확인할 수 있게 pending 유지
        if response.status_code >= 500 or code in ("PROVIDER_ERROR", "IDEMPOTENT_REQUEST_PROCESSING"):
            raise PaymentProviderUnavailable(f"토스 일시 오류 {code}")
        raise PaymentRejected(code, str(body.get("message", "")))
