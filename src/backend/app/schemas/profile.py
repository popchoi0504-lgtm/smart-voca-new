# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - 프로필·비밀번호 변경·이용권 요약·탈퇴의 요청/응답 양식 (프로필 설정 설계서 3장)
# 파일 위치: src/backend/app/schemas/profile.py
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ValidationInfo, field_validator, model_validator

from app.core_logic.profile_rules import AVATAR_COLORS, WITHDRAW_CONFIRM_TEXT, normalize_nickname
from app.schemas.auth import LOGIN_INPUT_MAX_LENGTH, check_password_rules


class ProfileRequest(BaseModel):
    """프로필 수정. 보낸 칸만 바꾼다(보내지 않은 칸은 그대로). 닉네임을 비우는 기능은 없다."""

    nickname: str | None = None
    avatar_color: str | None = None

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, value: str | None) -> str | None:
        return None if value is None else normalize_nickname(value)

    @field_validator("avatar_color")
    @classmethod
    def validate_avatar_color(cls, value: str | None) -> str | None:
        if value is not None and value not in AVATAR_COLORS:
            raise ValueError("고를 수 없는 색입니다.")
        return value

    @model_validator(mode="after")
    def at_least_one_field(self):
        # 보냈는데 null 인 칸과 아무 칸도 안 보낸 경우를 막는다
        sent = {name: getattr(self, name) for name in self.model_fields_set}
        if not sent or any(value is None for value in sent.values()):
            raise ValueError("바꿀 닉네임이나 색을 보내 주세요.")
        return self


class ConsentRequest(BaseModel):
    """동의 변경: 선택 동의(마케팅)만 바꿀 수 있다. StrictBool 이 아니어도 bool 이면 충분."""

    marketing_agreed: bool


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("current_password")
    @classmethod
    def limit_length(cls, value: str) -> str:
        if len(value) > LOGIN_INPUT_MAX_LENGTH:
            raise ValueError("입력값이 너무 깁니다.")
        return value

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str, info: ValidationInfo) -> str:
        check_password_rules(value)  # 가입과 같은 규칙
        if value == info.data.get("current_password"):
            raise ValueError("새 비밀번호는 현재 비밀번호와 달라야 합니다.")
        return value


class WithdrawRequest(BaseModel):
    password: str
    confirm_text: str

    @field_validator("password")
    @classmethod
    def limit_length(cls, value: str) -> str:
        if len(value) > LOGIN_INPUT_MAX_LENGTH:
            raise ValueError("입력값이 너무 깁니다.")
        return value

    @field_validator("confirm_text")
    @classmethod
    def validate_confirm_text(cls, value: str) -> str:
        if value.strip() != WITHDRAW_CONFIRM_TEXT:
            raise ValueError(f"확인 문구 '{WITHDRAW_CONFIRM_TEXT}' 를 그대로 입력해 주세요.")
        return value


class PlanSummaryResponse(BaseModel):
    plan: Literal["free", "premium"]
    premium_until: datetime | None
    ai_daily_limit: int
    ai_used_today: int
    ai_remaining_today: int
