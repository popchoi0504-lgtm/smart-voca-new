# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 비밀번호 해시와 로그인 토큰의 단위 테스트 (DB 없이 계산만 확인, FR-AUTH-04·05)
# 파일 위치: src/backend/tests/test_security.py
from datetime import timedelta

import jwt

from app.core.config import get_settings
from app.core.security import (
    JWT_ALGORITHM,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.core.timeutil import now_utc


def test_hash_is_argon2id_and_hides_the_plain_password():
    hashed = hash_password("abcd1234")
    assert hashed.startswith("$argon2id$")
    assert "abcd1234" not in hashed


def test_same_password_gives_different_hashes_because_of_salt():
    assert hash_password("abcd1234") != hash_password("abcd1234")


def test_verify_accepts_right_password_and_rejects_wrong_one():
    hashed = hash_password("abcd1234")
    assert verify_password(hashed, "abcd1234") is True
    assert verify_password(hashed, "abcd12345") is False


def test_verify_returns_false_for_garbage_hash():
    assert verify_password("not-a-real-hash", "abcd1234") is False


def test_token_roundtrip_returns_the_user_id():
    assert decode_access_token(create_access_token(42)) == 42


def test_token_contains_only_sub_iat_exp():
    token = create_access_token(7)
    payload = jwt.decode(token, options={"verify_signature": False})
    assert set(payload) == {"sub", "iat", "exp"}  # 이메일 같은 개인정보는 담지 않는다


def test_tampered_token_is_rejected():
    token = create_access_token(42)
    flipped = token[:-1] + ("A" if token[-1] != "A" else "B")
    assert decode_access_token(flipped) is None


def test_expired_token_is_rejected():
    eight_days_ago = now_utc() - timedelta(days=8)  # 유효기간은 7일
    assert decode_access_token(create_access_token(42, issued_at=eight_days_ago)) is None


def test_token_signed_with_another_secret_is_rejected():
    forged = jwt.encode({"sub": "42", "exp": now_utc() + timedelta(days=1)}, "another-secret-key-" * 4, algorithm=JWT_ALGORITHM)
    assert decode_access_token(forged) is None


def test_token_with_non_numeric_subject_is_rejected():
    secret = get_settings().jwt_secret
    token = jwt.encode({"sub": "abc", "exp": now_utc() + timedelta(days=1)}, secret, algorithm=JWT_ALGORITHM)
    assert decode_access_token(token) is None


def test_garbage_token_is_rejected():
    assert decode_access_token("abc") is None
    assert decode_access_token("") is None
