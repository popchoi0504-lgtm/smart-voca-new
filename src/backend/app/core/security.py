# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 비밀번호 해시(Argon2)와 로그인 토큰(JWT) 쿠키 처리 (FR-AUTH-04·05)
# 파일 위치: src/backend/app/core/security.py
from datetime import datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Response

from app.core.config import get_settings
from app.core.timeutil import now_utc

ACCESS_TOKEN_COOKIE = "access_token"
JWT_ALGORITHM = "HS256"

# Argon2id: 일부러 느리고 메모리를 쓰게 만든 비밀번호 해시 방식. 소금(salt)은 자동으로 붙는다.
_password_hasher = PasswordHasher()


def hash_password(plain_password: str) -> str:
    """비밀번호를 되돌릴 수 없는 해시 문자열로 바꾼다. 같은 비밀번호도 호출할 때마다 다른 값이 나온다(소금 때문)."""
    return _password_hasher.hash(plain_password)


def verify_password(stored_hash: str, plain_password: str) -> bool:
    """입력한 비밀번호가 저장된 해시와 맞는지 확인한다. 틀리거나 해시가 이상하면 False."""
    try:
        return _password_hasher.verify(stored_hash, plain_password)
    except (VerificationError, InvalidHashError):
        return False


def create_access_token(user_id: int, issued_at: datetime | None = None) -> str:
    """로그인 증표(JWT)를 만든다. 담는 내용은 회원 번호(sub), 발급 시각(iat), 만료 시각(exp)뿐이다."""
    settings = get_settings()
    issued = issued_at or now_utc()
    payload = {
        "sub": str(user_id),  # JWT 규칙상 sub 는 문자열
        "iat": issued,
        "exp": issued + timedelta(days=settings.jwt_expire_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """증표가 진짜이고 만료되지 않았으면 회원 번호를, 아니면 None 을 돌려준다."""
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def set_auth_cookie(response: Response, token: str) -> None:
    """로그인 증표를 쿠키에 담는다. HttpOnly: 화면의 자바스크립트가 읽지 못한다. SameSite=Lax: 다른 사이트가 보낸 요청에는 실리지 않는다."""
    settings = get_settings()
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=token,
        max_age=settings.jwt_expire_days * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,  # https 로 배포할 때는 반드시 true
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """로그아웃: 같은 이름·속성의 쿠키를 지운다."""
    settings = get_settings()
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )
