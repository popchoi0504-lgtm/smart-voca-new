# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - 프로필 순수 규칙 단위 테스트 (프로필 설정 설계서 8장)
# 파일 위치: src/backend/tests/test_profile_rules.py
import pytest

from app.core_logic.profile_rules import AVATAR_COLORS, auto_avatar_color, display_name_of, normalize_nickname


@pytest.mark.parametrize("raw, expected", [("민트", "민트"), ("  듀니  ", "듀니"), ("a" * 12, "a" * 12), ("가나 다", "가나 다")])
def test_nickname_accepts_valid(raw, expected):
    assert normalize_nickname(raw) == expected


@pytest.mark.parametrize("raw", ["", "a", " a ", "   ", "a" * 13, "ab\ncd", "ab​cd", "ab\tcd"])
def test_nickname_rejects_invalid(raw):
    with pytest.raises(ValueError):
        normalize_nickname(raw)


def test_nickname_length_counts_characters_not_bytes():
    # 한글 12자는 바이트로는 36이지만 글자 수로는 12 → 통과
    assert normalize_nickname("가" * 12) == "가" * 12


def test_display_name_prefers_nickname():
    assert display_name_of("듀니", "dooni@gmail.com") == "듀니"
    assert display_name_of(None, "dooni@gmail.com") == "dooni"


def test_auto_color_is_stable_and_in_palette():
    assert auto_avatar_color("a@b.com") == auto_avatar_color("a@b.com")
    assert all(auto_avatar_color(f"user{i}@x.com") in AVATAR_COLORS for i in range(50))
    # 이메일이 다르면 색이 여러 가지로 나뉜다(전부 같은 색이면 의미 없음)
    assert len({auto_avatar_color(f"user{i}@x.com") for i in range(50)}) > 1
