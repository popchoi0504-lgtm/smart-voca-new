# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 구독·주문·결제 확인·결제 내역 API 통합 테스트 (FR-SUB-01~06, IF-6, 구현 계획서 VS-5)
# 파일 위치: src/backend/tests/test_subscription.py
# 결제사는 가짜 담당자(FakePaymentProvider)로 바꿔 끼워서, 인터넷 없이 성공·거절·통신 실패를 흉내 낸다.
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.core.timeutil import now_utc
from app.main import app
from app.models.payment import Payment
from app.models.user import User
from app.models.word import Word
from app.payments.fake_provider import FakePaymentProvider
from app.payments.provider import get_payment_provider

CREDENTIALS = {"email": "student@gmail.com", "password": "abcd1234"}
PRICE = 4900  # 설정 premium_price_krw 기본값
PASS_DAYS = 30
FREE_LIMIT = 250


@pytest.fixture
def client(api_client, db_session):
    db_session.add_all(
        Word(headword=f"word{rank:03d}", part_of_speech="n.", meaning_ko=f"뜻{rank}", example_en=f"I see word{rank:03d}.",
             example_ko=f"예문{rank}", frequency_rank=rank)
        for rank in range(1, 261)
    )
    db_session.commit()
    assert api_client.post("/api/auth/signup", json=CREDENTIALS).status_code == 201
    return api_client


@pytest.fixture
def provider():
    """가짜 결제사. 기본은 승인. 테스트가 provider.outcome 을 바꿔 거절·통신 실패를 만든다."""
    fake = FakePaymentProvider()
    app.dependency_overrides[get_payment_provider] = lambda: fake
    return fake


def order(client):
    response = client.post("/api/payments/orders", json={"product": "premium_30d"})
    assert response.status_code == 200
    return response.json()


def confirm(client, order_id, amount=PRICE, payment_key="pk_test_1"):
    return client.post("/api/payments/confirm", json={"payment_key": payment_key, "order_id": order_id, "amount": amount})


def me(db_session):
    db_session.expire_all()
    return db_session.scalar(select(User))


def payment_row(db_session, order_id):
    db_session.expire_all()
    return db_session.scalar(select(Payment).where(Payment.order_id == order_id))


# ---------- 로그인 필요 ----------


@pytest.mark.parametrize("method,path", [("get", "/api/subscription"), ("post", "/api/payments/orders"),
                                          ("post", "/api/payments/confirm"), ("get", "/api/payments")])
def test_requires_login(api_client, method, path):
    assert getattr(api_client, method)(path).status_code == 401


# ---------- 요금제 안내 ----------


def test_subscription_shows_plans_and_free_status(client):
    body = client.get("/api/subscription").json()
    free, premium = body["plans"]
    assert (free["code"], free["word_limit"], free["price_krw"], free["pass_days"]) == ("free", FREE_LIMIT, 0, None)
    assert (premium["code"], premium["word_limit"], premium["price_krw"], premium["pass_days"]) == ("premium", 260, PRICE, PASS_DAYS)
    assert body["current"] == {"plan": "free", "premium_until": None}


def test_expired_pass_is_free_again(client, db_session):
    me(db_session).premium_until = now_utc() - timedelta(days=1)
    db_session.commit()
    current = client.get("/api/subscription").json()["current"]
    assert current["plan"] == "free"


# ---------- 주문 ----------


def test_order_is_pending_and_amount_is_set_by_server(client, db_session):
    # 요청에 금액을 끼워 보내도 무시되고 서버 금액이 쓰인다
    response = client.post("/api/payments/orders", json={"product": "premium_30d", "amount": 1})
    body = response.json()
    assert body["amount"] == PRICE
    assert body["order_id"].startswith("svc-") and len(body["order_id"]) == 20
    row = payment_row(db_session, body["order_id"])
    assert (row.status, row.amount, row.pass_days, row.payment_key) == ("pending", PRICE, PASS_DAYS, None)


def test_order_ids_differ_and_customer_key_is_stable(client):
    first, second = order(client), order(client)
    assert first["order_id"] != second["order_id"]
    assert first["customer_key"] == second["customer_key"]
    assert 22 <= len(first["customer_key"]) <= 50  # 토스 customerKey 길이 규칙


def test_unknown_product_is_rejected(client):
    assert client.post("/api/payments/orders", json={"product": "premium_999d"}).status_code == 422


# ---------- 결제 확인: 성공 ----------


def test_confirm_grants_pass_once(client, db_session, provider):
    placed = order(client)
    before = now_utc()
    response = confirm(client, placed["order_id"])
    assert response.status_code == 200
    body = response.json()
    assert (body["status"], body["already_processed"]) == ("paid", False)
    assert body["payment"]["amount"] == PRICE
    user = me(db_session)
    assert before + timedelta(days=PASS_DAYS) - timedelta(minutes=1) < user.premium_until < now_utc() + timedelta(days=PASS_DAYS)
    row = payment_row(db_session, placed["order_id"])
    assert (row.status, row.payment_key) == ("paid", "pk_test_1")
    assert row.approved_at is not None
    assert provider.calls == [("pk_test_1", placed["order_id"], PRICE)]


def test_confirm_twice_does_not_extend_twice(client, db_session, provider):
    """IF-6: 같은 확인 요청을 또 보내면 같은 결과를 돌려주고 이용권은 한 번만 늘어난다."""
    placed = order(client)
    first = confirm(client, placed["order_id"]).json()
    until_after_first = me(db_session).premium_until
    second = confirm(client, placed["order_id"])
    assert second.status_code == 200
    assert second.json()["already_processed"] is True
    assert second.json()["premium_until"] == first["premium_until"]
    assert me(db_session).premium_until == until_after_first
    assert len(provider.calls) == 1  # 결제사도 한 번만 불렀다


def test_second_pass_stacks_on_remaining_days(client, db_session, provider):
    first = order(client)
    confirm(client, first["order_id"], payment_key="pk_a")
    until_after_first = me(db_session).premium_until
    second = order(client)
    confirm(client, second["order_id"], payment_key="pk_b")
    assert me(db_session).premium_until == until_after_first + timedelta(days=PASS_DAYS)


# ---------- 결제 확인: 막아야 하는 경우 ----------


@pytest.mark.parametrize("wrong_amount", [100, 4899, 5000, 0, -4900])
def test_amount_mismatch_is_rejected_without_calling_provider(client, db_session, provider, wrong_amount):
    placed = order(client)
    response = confirm(client, placed["order_id"], amount=wrong_amount)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "AMOUNT_MISMATCH"
    assert me(db_session).premium_until is None
    assert payment_row(db_session, placed["order_id"]).status == "pending"
    assert provider.calls == []


def test_amount_must_be_integer(client, provider):
    placed = order(client)
    assert confirm(client, placed["order_id"], amount="4900").status_code == 422


def test_unknown_order_is_404(client, provider):
    response = confirm(client, "svc-doesnotexist0000")
    assert (response.status_code, response.json()["error"]["code"]) == (404, "ORDER_NOT_FOUND")
    assert provider.calls == []


def test_cannot_confirm_someone_elses_order(client, db_session, provider):
    other = User(email="other@gmail.com", password_hash="x")
    db_session.add(other)
    db_session.commit()
    db_session.add(Payment(user_id=other.id, order_id="svc-otherusersorder1", amount=PRICE, pass_days=PASS_DAYS))
    db_session.commit()
    response = confirm(client, "svc-otherusersorder1")
    assert response.status_code == 404
    assert provider.calls == []
    assert db_session.get(User, other.id).premium_until is None


def test_provider_rejection_marks_failed_and_grants_nothing(client, db_session, provider):
    provider.outcome = "reject"
    placed = order(client)
    response = confirm(client, placed["order_id"])
    assert (response.status_code, response.json()["error"]["code"]) == (402, "PAYMENT_FAILED")
    row = payment_row(db_session, placed["order_id"])
    assert (row.status, row.failure_code) == ("failed", "REJECT_CARD_COMPANY")
    assert me(db_session).premium_until is None
    # 실패한 주문은 다시 확인해도 결제사를 부르지 않고, 승인으로 바뀌지 않는다
    provider.outcome = "approve"
    again = confirm(client, placed["order_id"])
    assert again.status_code == 402
    assert len(provider.calls) == 1
    assert me(db_session).premium_until is None


def test_provider_outage_keeps_pending_and_can_retry(client, db_session, provider):
    provider.outcome = "unavailable"
    placed = order(client)
    response = confirm(client, placed["order_id"])
    assert (response.status_code, response.json()["error"]["code"]) == (502, "PAYMENT_PROVIDER_ERROR")
    assert payment_row(db_session, placed["order_id"]).status == "pending"
    assert me(db_session).premium_until is None
    provider.outcome = "approve"  # 결제사가 복구된 뒤 다시 확인
    assert confirm(client, placed["order_id"]).status_code == 200
    assert me(db_session).premium_until is not None


# ---------- 결제 내역 ----------


def test_payment_list_is_mine_and_newest_first(client, db_session, provider):
    first, second = order(client), order(client)
    confirm(client, first["order_id"], payment_key="pk_a")
    items = client.get("/api/payments").json()["items"]
    assert [item["order_id"] for item in items] == [second["order_id"], first["order_id"]]
    assert [item["status"] for item in items] == ["pending", "paid"]
    other = User(email="other@gmail.com", password_hash="x")
    db_session.add(other)
    db_session.commit()
    db_session.add(Payment(user_id=other.id, order_id="svc-otherusersorder1", amount=PRICE, pass_days=PASS_DAYS))
    db_session.commit()
    assert len(client.get("/api/payments").json()["items"]) == 2  # 남의 결제는 안 보인다


def test_payment_list_limit(client):
    for _ in range(3):
        order(client)
    assert len(client.get("/api/payments?limit=2").json()["items"]) == 2
    assert client.get("/api/payments?limit=0").status_code == 422
    assert client.get("/api/payments?limit=51").status_code == 422


# ---------- 이용권이 학습 범위를 연다 (구현 계획서 VS-5 통합 확인) ----------


def test_pass_unlocks_premium_words_and_expiry_closes_them(client, db_session, provider):
    assert client.get("/api/study/today").json()["plan_word_limit"] == FREE_LIMIT
    confirm(client, order(client)["order_id"])
    assert client.get("/api/study/today").json()["plan_word_limit"] == 260
    # 이용권 만료 → 새 단어 범위가 무료 범위로 돌아간다 (FR-SUB-05)
    me(db_session).premium_until = now_utc() - timedelta(seconds=1)
    db_session.commit()
    assert client.get("/api/study/today").json()["plan_word_limit"] == FREE_LIMIT


def test_default_provider_without_fake_override_is_toss(monkeypatch):
    """PAYMENT_PROVIDER=fake 로 바꾸면 가짜 담당자가, 아니면 토스 담당자가 선택된다 (FR-SUB-08)."""
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "payment_provider", "fake")
    assert get_payment_provider().name == "fake"
    monkeypatch.setattr(settings, "payment_provider", "toss")
    monkeypatch.setattr(settings, "toss_secret_key", "test_gsk_dummy")
    assert get_payment_provider().name == "toss"
