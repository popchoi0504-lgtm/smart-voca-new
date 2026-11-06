# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 연속 학습일·숙련도 규칙 단위 테스트 (DB 없음, 구현 계획서 VS-6)
# 파일 위치: src/backend/tests/test_progress_rules.py
from datetime import date, datetime, timedelta, timezone

import pytest

from app.core.timeutil import KST
from app.core_logic.progress_rules import (
    FAMILIAR_INTERVAL_DAYS, MASTERY_FAMILIAR, MASTERY_LEARNING, calculate_streak, classify_mastery,
)

TODAY = date(2026, 11, 5)


def days_ago(count: int) -> date:
    return TODAY - timedelta(days=count)


# ---------- 연속 학습일 ----------


def test_no_records_is_zero():
    assert calculate_streak([], TODAY) == 0


def test_only_today_is_one():
    assert calculate_streak([TODAY], TODAY) == 1


def test_before_studying_today_keeps_yesterdays_streak():
    """오늘 학습 전: 어제까지 3일 이어졌으면 3 (끊기지 않음)."""
    assert calculate_streak([days_ago(1), days_ago(2), days_ago(3)], TODAY) == 3


def test_studying_today_extends_streak():
    assert calculate_streak([TODAY, days_ago(1), days_ago(2)], TODAY) == 3


def test_skipped_a_day_breaks_streak():
    """하루 건너뜀: 그저께까지 했고 어제·오늘 안 했으면 0."""
    assert calculate_streak([days_ago(2), days_ago(3)], TODAY) == 0


def test_gap_in_the_middle_counts_only_recent_run():
    """오늘, 어제 했고 그저께 건너뜀, 그 전에 많이 했어도 2."""
    assert calculate_streak([TODAY, days_ago(1), days_ago(3), days_ago(4), days_ago(5)], TODAY) == 2


def test_gap_before_yesterday_with_today_missing():
    """오늘 안 했고 어제만 했음(그저께 비어 있음) → 1."""
    assert calculate_streak([days_ago(1), days_ago(3)], TODAY) == 1


def test_same_day_many_times_counts_once():
    assert calculate_streak([TODAY] * 5 + [days_ago(1)] * 3, TODAY) == 2


def test_input_order_does_not_matter():
    assert calculate_streak([days_ago(2), TODAY, days_ago(1)], TODAY) == 3


def test_future_dates_are_ignored():
    assert calculate_streak([TODAY + timedelta(days=1), TODAY + timedelta(days=2)], TODAY) == 0
    assert calculate_streak([TODAY + timedelta(days=1), TODAY], TODAY) == 1


def test_works_across_month_and_year_boundary():
    today = date(2027, 1, 2)
    assert calculate_streak([date(2027, 1, 2), date(2027, 1, 1), date(2026, 12, 31), date(2026, 12, 30)], today) == 4


def test_leap_day_boundary():
    today = date(2028, 3, 1)
    assert calculate_streak([date(2028, 3, 1), date(2028, 2, 29), date(2028, 2, 28)], today) == 3


def test_midnight_kst_boundary_decides_the_day():
    """한국 시간 기준 날짜가 바뀌는 순간: UTC 14:59:59 는 11-05, 15:00:00 은 11-06."""
    before_midnight = datetime(2026, 11, 5, 14, 59, 59, tzinfo=timezone.utc).astimezone(KST).date()
    after_midnight = datetime(2026, 11, 5, 15, 0, 0, tzinfo=timezone.utc).astimezone(KST).date()
    assert before_midnight == date(2026, 11, 5)
    assert after_midnight == date(2026, 11, 6)
    studied = [date(2026, 11, 5)]
    assert calculate_streak(studied, before_midnight) == 1  # 같은 날: 오늘 학습함
    assert calculate_streak(studied, after_midnight) == 1  # 자정이 지나도 어제 기록이 있어 아직 이어짐
    assert calculate_streak(studied, date(2026, 11, 7)) == 0  # 이틀 지나면 끊김


# ---------- 숙련도 ----------


@pytest.mark.parametrize("interval_days,expected", [
    (0, MASTERY_LEARNING),
    (1, MASTERY_LEARNING),
    (FAMILIAR_INTERVAL_DAYS - 1, MASTERY_LEARNING),
    (FAMILIAR_INTERVAL_DAYS, MASTERY_FAMILIAR),
    (FAMILIAR_INTERVAL_DAYS + 1, MASTERY_FAMILIAR),
    (365, MASTERY_FAMILIAR),
])
def test_mastery_boundary(interval_days, expected):
    assert classify_mastery(interval_days) == expected


def test_threshold_is_21_days():
    """설계서가 정한 값(21일)이 바뀌면 이 테스트가 알려 준다."""
    assert FAMILIAR_INTERVAL_DAYS == 21


def test_최장_연속은_과거의_가장_긴_묶음():
    from datetime import date

    from app.core_logic.progress_rules import calculate_longest_streak

    days = [date(2026, 10, d) for d in (1, 2, 3, 4, 10, 11, 20)]
    assert calculate_longest_streak(days) == 4
    assert calculate_longest_streak(days + days) == 4  # 같은 날 중복은 하루
    assert calculate_longest_streak([date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 4)]) == 2  # 하루 빠지면 끊김
    assert calculate_longest_streak([]) == 0
    assert calculate_longest_streak([date(2026, 10, 1)]) == 1
