# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 결제 순수 규칙: 주문번호, 회원 키, 금액 비교, 이용권 연장 계산 (FR-SUB-03·05·06, DD-7)
# 파일 위치: src/backend/app/core_logic/payment_rules.py
# DB·네트워크를 쓰지 않는 계산만 모아 둔다 → 빠르고 정확하게 단위 테스트할 수 있다.
import hashlib
import hmac
import secrets
import string
from datetime import datetime, timedelta

ORDER_ID_PREFIX = "svc-"
_ORDER_ID_CHARS = string.ascii_lowercase + string.digits
_ORDER_ID_RANDOM_LENGTH = 16


def generate_order_id() -> str:
    """주문번호 'svc-' + 무작위 16자(영문 소문자·숫자). secrets 는 추측하기 어려운 난수를 만든다.

    토스 주문번호 규칙(6~64자, 영문·숫자·-·_)에 맞는다.
    """
    random_part = "".join(secrets.choice(_ORDER_ID_CHARS) for _ in range(_ORDER_ID_RANDOM_LENGTH))
    return ORDER_ID_PREFIX + random_part


def make_customer_key(user_id: int, secret: str) -> str:
    """결제위젯에 넘길 회원 고유 키. 회원 id 에서 서버 비밀값으로 계산하므로 id 를 알아도 추측할 수 없다.

    같은 회원은 항상 같은 값, 다른 회원은 다른 값. DB 에 따로 저장하지 않는다.
    """
    digest = hmac.new(secret.encode("utf-8"), f"customer:{user_id}".encode("utf-8"), hashlib.sha256).hexdigest()
    return "u_" + digest[:32]


def is_amount_matching(requested_amount: int, expected_amount: int) -> bool:
    """확인 요청의 금액이 서버가 주문 때 정한 금액과 정확히 같은지."""
    return requested_amount == expected_amount


def extend_premium_until(current_until: datetime | None, now: datetime, pass_days: int) -> datetime:
    """이용권 만료 시각을 늘린다: max(지금, 현재 만료 시각) + pass_days 일.

    이미 이용권이 남아 있으면 남은 기간 뒤에 이어 붙고, 없거나 만료됐으면 지금부터 시작한다.
    """
    start = now if current_until is None or current_until < now else current_until
    return start + timedelta(days=pass_days)
