# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - 프로필 순수 규칙: 닉네임 검사, 표시 이름, 아바타 색 자동 배정 (프로필 설정 설계서 3장, FR-PROFILE-01·02)
# 파일 위치: src/backend/app/core_logic/profile_rules.py
import unicodedata

NICKNAME_MIN_LENGTH = 2
NICKNAME_MAX_LENGTH = 12

# 화면에서 고를 수 있는 색 6종. 실제 색값은 화면(CSS)에서 정한다
AVATAR_COLORS = ("mint", "lavender", "yellow", "pink", "sky", "orange")

WITHDRAW_CONFIRM_TEXT = "탈퇴합니다"


def normalize_nickname(raw_nickname: str) -> str:
    """앞뒤 공백을 지우고 2~12자인지, 줄바꿈 같은 눈에 안 보이는 제어 문자가 없는지 검사한다."""
    nickname = raw_nickname.strip()
    if not NICKNAME_MIN_LENGTH <= len(nickname) <= NICKNAME_MAX_LENGTH:
        raise ValueError(f"닉네임은 {NICKNAME_MIN_LENGTH}자 이상 {NICKNAME_MAX_LENGTH}자 이하여야 합니다.")
    # 범주 C* = 제어·서식·미사용 문자(줄바꿈, 글자 너비 0 문자 등). 화면에서 이름이 비어 보이는 것을 막는다
    if any(unicodedata.category(char).startswith("C") for char in nickname):
        raise ValueError("닉네임에 사용할 수 없는 문자가 있습니다.")
    return nickname


def display_name_of(nickname: str | None, email: str) -> str:
    """화면에 보여 줄 이름: 닉네임이 있으면 닉네임, 없으면 이메일의 @ 앞부분."""
    return nickname if nickname else email.partition("@")[0]


def auto_avatar_color(email: str) -> str:
    """색을 고르지 않은 회원에게 이메일로 색을 정해 준다. 글자 코드의 합이라 같은 이메일은 항상 같은 색(저장 불필요)."""
    return AVATAR_COLORS[sum(ord(char) for char in email) % len(AVATAR_COLORS)]
