# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 회원가입·로그인의 요청/응답 양식과 입력 검사 규칙 (인터페이스 정의서 4.1·4.2, FR-AUTH-07)
# 파일 위치: src/backend/app/schemas/auth.py
import re
from datetime import datetime

from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, field_validator

EMAIL_MAX_LENGTH = 254
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 64
LOGIN_INPUT_MAX_LENGTH = 128  # 로그인 입력이 비정상적으로 길면 해시 계산 부담을 주므로 막는다


def normalize_email(raw_email: str) -> str:
    """이메일의 앞뒤 공백을 지우고 소문자로 맞춘 뒤, 형식이 올바른지 검사한다."""
    email = raw_email.strip().lower()
    if len(email) > EMAIL_MAX_LENGTH:
        raise ValueError(f"이메일은 {EMAIL_MAX_LENGTH}자 이하여야 합니다.")
    try:
        # check_deliverability=False: 실제로 메일을 받을 수 있는지 인터넷에서 확인하지 않는다(형식만 검사)
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        raise ValueError("이메일 형식이 올바르지 않습니다.") from None
    return email


def check_password_rules(password: str) -> str:
    """비밀번호 규칙: 8~64자, 영문과 숫자를 각각 1자 이상 포함 (원문은 공백 등을 포함해 그대로 사용)."""
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        raise ValueError(f"비밀번호는 {PASSWORD_MIN_LENGTH}자 이상 {PASSWORD_MAX_LENGTH}자 이하여야 합니다.")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ValueError("비밀번호에는 영문과 숫자가 각각 1자 이상 들어가야 합니다.")
    return password


class SignupRequest(BaseModel):
    """회원가입 요청: 이메일과 비밀번호."""

    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("password")
    @classmethod
    def validate_password_field(cls, value: str) -> str:
        return check_password_rules(value)


class LoginRequest(BaseModel):
    """로그인 요청. 형식 검사는 하지 않는다: 어떤 입력이 틀렸는지 알려주지 않는 것이 보안상 낫기 때문."""

    email: str
    password: str

    @field_validator("email", "password")
    @classmethod
    def limit_length(cls, value: str) -> str:
        if len(value) > LOGIN_INPUT_MAX_LENGTH:
            raise ValueError("입력값이 너무 깁니다.")
        return value

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: str) -> str:
        return value.strip().lower()


class UserOut(BaseModel):
    """화면에 내려 주는 회원 정보. 비밀번호 해시는 절대 포함하지 않는다."""

    id: int
    email: str
    nickname: str | None
    display_name: str  # 닉네임, 없으면 이메일의 @ 앞부분. 화면은 이 값만 쓴다
    avatar_color: str  # 고른 색, 없으면 이메일로 자동 배정한 색
    daily_new_limit: int
    is_premium: bool
    premium_until: datetime | None


class AuthResponse(BaseModel):
    user: UserOut
