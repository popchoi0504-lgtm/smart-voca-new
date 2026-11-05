# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 결제 순수 규칙 단위 테스트 (주문번호, 회원 키, 금액 비교, 이용권 연장)
# 파일 위치: src/backend/tests/test_payment_rules.py
import re
from datetime import datetime, timedelta, timezone

from app.core_logic.payment_rules import (
    extend_premium_until,
    generate_order_id,
    is_amount_matching,
    make_customer_key,
)

NOW = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)


def test_주문번호는_svc_접두어와_소문자_숫자_16자():
    assert re.fullmatch(r"svc-[a-z0-9]{16}", generate_order_id())


def test_주문번호는_매번_다르다():
    assert len({generate_order_id() for _ in range(200)}) == 200


def test_회원_키는_같은_회원이면_같고_다른_회원이면_다르다():
    assert make_customer_key(1, "비밀") == make_customer_key(1, "비밀")
    assert make_customer_key(1, "비밀") != make_customer_key(2, "비밀")


def test_회원_키는_비밀값이_다르면_달라지고_토스_규칙에_맞는다():
    assert make_customer_key(1, "비밀A") != make_customer_key(1, "비밀B")
    assert re.fullmatch(r"u_[0-9a-f]{32}", make_customer_key(1, "비밀A"))


def test_회원_키에_회원_번호가_그대로_드러나지_않는다():
    assert "u_1" != make_customer_key(1, "비밀")


def test_금액이_같을_때만_일치():
    assert is_amount_matching(4900, 4900)
    assert not is_amount_matching(4899, 4900)
    assert not is_amount_matching(100, 4900)
    assert not is_amount_matching(0, 4900)
    assert not is_amount_matching(5000, 4900)  # 더 많아도 불일치(위조·실수 모두 막는다)


def test_이용권이_없으면_지금부터_30일():
    assert extend_premium_until(None, NOW, 30) == NOW + timedelta(days=30)


def test_이용권이_만료됐으면_지금부터_30일():
    expired = NOW - timedelta(days=3)
    assert extend_premium_until(expired, NOW, 30) == NOW + timedelta(days=30)


def test_이용권이_남아_있으면_남은_기간_뒤에_이어_붙는다():
    remaining = NOW + timedelta(days=10)
    assert extend_premium_until(remaining, NOW, 30) == NOW + timedelta(days=40)


def test_만료_시각이_정확히_지금이면_지금부터_시작():
    assert extend_premium_until(NOW, NOW, 30) == NOW + timedelta(days=30)
