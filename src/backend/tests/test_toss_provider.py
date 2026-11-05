# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 토스 담당자 단위 테스트: httpx.post 를 가짜로 바꿔 인터넷 없이 요청 모양과 응답 해석을 검증
# 파일 위치: src/backend/tests/test_toss_provider.py
import base64
from datetime import timedelta

import httpx
import pytest

from app.payments.provider import PaymentProviderUnavailable, PaymentRejected
from app.payments.toss_provider import CONFIRM_URL, TossPaymentProvider

SECRET = "test_gsk_dummy_value"


def fake_post(monkeypatch, status_code=200, body=None, error=None):
    """httpx.post 를 바꿔 끼우고, 실제로 보낸 요청 내용을 sent 에 담아 돌려준다."""
    sent = {}

    def post(url, json, headers, timeout):
        sent.update(url=url, json=json, headers=headers)
        if error:
            raise error
        return httpx.Response(status_code, json=body, request=httpx.Request("POST", url))

    monkeypatch.setattr("app.payments.toss_provider.httpx.post", post)
    return sent


def done_body(order_id="svc-aaaaaaaaaaaaaaaa", amount=4900):
    return {"status": "DONE", "paymentKey": "pk_real", "orderId": order_id, "totalAmount": amount,
            "approvedAt": "2026-11-05T14:07:11+09:00"}


def test_request_shape_and_auth_header(monkeypatch):
    sent = fake_post(monkeypatch, body=done_body())
    result = TossPaymentProvider(SECRET).confirm("pk_real", "svc-aaaaaaaaaaaaaaaa", 4900)
    assert sent["url"] == CONFIRM_URL
    assert sent["json"] == {"paymentKey": "pk_real", "orderId": "svc-aaaaaaaaaaaaaaaa", "amount": 4900}
    # 인증은 base64("시크릿키:") — 끝의 콜론이 있어야 한다
    assert base64.b64decode(sent["headers"]["Authorization"].removeprefix("Basic ")).decode() == SECRET + ":"
    assert sent["headers"]["Idempotency-Key"] == "svc-aaaaaaaaaaaaaaaa"
    assert result.payment_key == "pk_real"
    assert result.approved_at.utcoffset() == timedelta(hours=9)


@pytest.mark.parametrize("bad_body", [
    {**done_body(), "status": "IN_PROGRESS"},  # 승인 완료(DONE)가 아님
    {**done_body(), "totalAmount": 100},  # 금액이 다름
    {**done_body(), "orderId": "svc-bbbbbbbbbbbbbbbb"},  # 주문번호가 다름
])
def test_200_but_not_a_completed_matching_payment_is_not_trusted(monkeypatch, bad_body):
    fake_post(monkeypatch, body=bad_body)
    with pytest.raises(PaymentRejected):
        TossPaymentProvider(SECRET).confirm("pk_real", "svc-aaaaaaaaaaaaaaaa", 4900)


def test_card_rejection_becomes_rejected_with_code(monkeypatch):
    fake_post(monkeypatch, 403, {"code": "REJECT_CARD_COMPANY", "message": "결제 승인이 거절되었습니다."})
    with pytest.raises(PaymentRejected) as info:
        TossPaymentProvider(SECRET).confirm("pk_real", "svc-aaaaaaaaaaaaaaaa", 4900)
    assert info.value.code == "REJECT_CARD_COMPANY"


@pytest.mark.parametrize("status_code,body", [
    (500, {"code": "UNKNOWN_PAYMENT_ERROR", "message": "x"}),
    (400, {"code": "PROVIDER_ERROR", "message": "일시 오류"}),
    (409, {"code": "IDEMPOTENT_REQUEST_PROCESSING", "message": "처리 중"}),
])
def test_temporary_errors_become_unavailable(monkeypatch, status_code, body):
    fake_post(monkeypatch, status_code, body)
    with pytest.raises(PaymentProviderUnavailable):
        TossPaymentProvider(SECRET).confirm("pk_real", "svc-aaaaaaaaaaaaaaaa", 4900)


def test_network_failure_becomes_unavailable(monkeypatch):
    fake_post(monkeypatch, error=httpx.ConnectTimeout("시간 초과"))
    with pytest.raises(PaymentProviderUnavailable):
        TossPaymentProvider(SECRET).confirm("pk_real", "svc-aaaaaaaaaaaaaaaa", 4900)


def test_missing_secret_key_is_unavailable():
    with pytest.raises(PaymentProviderUnavailable):
        TossPaymentProvider("")
