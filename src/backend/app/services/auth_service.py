# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 회원가입·로그인의 업무 규칙 (FR-AUTH-01·02·04, FR-SYS-02)
# 파일 위치: src/backend/app/services/auth_service.py
import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import hash_password, verify_password
from app.core.timeutil import now_utc, to_kst
from app.core_logic.profile_rules import auto_avatar_color, display_name_of
from app.models.user import User
from app.schemas.auth import UserOut

logger = logging.getLogger("smart_voca.auth")

# 없는 이메일로 로그인을 시도해도 비밀번호 확인과 같은 시간이 걸리게 하려는 가짜 해시.
# (응답 시간 차이로 "이 이메일은 가입되어 있구나"를 해커가 알아채지 못하게 한다.)
_DUMMY_HASH = hash_password("dummy-password-for-timing-only")

_INVALID_CREDENTIALS = AppError(401, "INVALID_CREDENTIALS", "이메일 또는 비밀번호가 올바르지 않습니다.")


def mask_email(email: str) -> str:
    """로그에 개인정보가 그대로 남지 않도록 이메일의 앞부분을 가린다. (예: a***@gmail.com)"""
    local_part, _, domain = email.partition("@")
    return f"{local_part[:1]}***@{domain}"


def signup(db: Session, email: str, password: str) -> User:
    """새 회원을 만든다. 같은 이메일이 이미 있으면 409. 비밀번호는 해시로만 저장한다."""
    if db.scalar(select(User.id).where(User.email == email)) is not None:
        raise AppError(409, "EMAIL_ALREADY_EXISTS", "이미 가입된 이메일입니다.")

    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # 위 확인과 저장 사이에 같은 이메일이 동시에 가입된 경우: DB 의 UNIQUE 제약이 최후의 방어선
        db.rollback()
        raise AppError(409, "EMAIL_ALREADY_EXISTS", "이미 가입된 이메일입니다.") from None
    db.refresh(user)
    logger.info("회원가입 성공 user_id=%s", user.id)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    """이메일과 비밀번호가 맞으면 회원을 돌려준다. 어느 쪽이 틀렸는지는 알려주지 않는다."""
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        verify_password(_DUMMY_HASH, password)  # 시간을 맞추기 위한 헛계산
        logger.warning("로그인 실패(가입되지 않은 이메일) email=%s", mask_email(email))
        raise _INVALID_CREDENTIALS
    if not verify_password(user.password_hash, password):
        logger.warning("로그인 실패(비밀번호 불일치) user_id=%s", user.id)
        raise _INVALID_CREDENTIALS
    logger.info("로그인 성공 user_id=%s", user.id)
    return user


def to_user_out(user: User) -> UserOut:
    """DB 의 회원 정보를 화면에 내려 줄 모양으로 바꾼다(해시 제외, 시각은 한국 시간)."""
    premium_until = user.premium_until
    is_premium = premium_until is not None and premium_until > now_utc()
    return UserOut(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        display_name=display_name_of(user.nickname, user.email),
        avatar_color=user.avatar_color or auto_avatar_color(user.email),
        daily_new_limit=user.daily_new_limit,
        is_premium=is_premium,
        premium_until=to_kst(premium_until) if premium_until is not None else None,
    )
