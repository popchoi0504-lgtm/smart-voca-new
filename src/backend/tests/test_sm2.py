# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - SM-2 계산과 점수 변환 단위 테스트 (FR-SRS-02·03·06, 구현 계획서 VS-3)
# 파일 위치: src/backend/tests/test_sm2.py
from decimal import Decimal

import pytest

from app.core_logic.quality import flashcard_quality
from app.core_logic.sm2 import MIN_EASE_FACTOR, Sm2State, calculate_next


def test_first_success_gives_one_day():
    new_state = calculate_next(Sm2State(), 5)
    assert (new_state.repetitions, new_state.interval_days) == (1, 1)


def test_second_success_gives_six_days():
    state = calculate_next(Sm2State(), 5)
    new_state = calculate_next(state, 5)
    assert (new_state.repetitions, new_state.interval_days) == (2, 6)


def test_third_success_multiplies_by_ease_factor():
    state = Sm2State()
    for _ in range(2):
        state = calculate_next(state, 5)  # EF: 2.50 → 2.60 → 2.70, 간격 1 → 6
    assert state.ease_factor == Decimal("2.70")
    third = calculate_next(state, 5)
    assert third.interval_days == 16  # 6 × 2.70 = 16.2 → 16
    assert third.repetitions == 3


def test_interval_keeps_growing_with_good_answers():
    state = Sm2State()
    intervals = []
    for _ in range(6):
        state = calculate_next(state, 5)
        intervals.append(state.interval_days)
    assert intervals == sorted(intervals) and len(set(intervals)) == 6


@pytest.mark.parametrize("low_quality", [0, 1, 2])
def test_low_quality_resets_to_start(low_quality):
    learned = Sm2State(repetitions=4, interval_days=40, ease_factor=Decimal("2.30"))
    new_state = calculate_next(learned, low_quality)
    assert new_state.repetitions == 0
    assert new_state.interval_days == 1
    assert new_state.ease_factor == Decimal("2.30")  # 실패해도 난이도 계수는 그대로 (SM-2 원 규칙)


def test_quality_three_is_success_but_lowers_ease_factor():
    new_state = calculate_next(Sm2State(), 3)
    assert new_state.repetitions == 1
    assert new_state.ease_factor == Decimal("2.36")  # 2.50 - 0.14


def test_quality_four_keeps_ease_factor():
    assert calculate_next(Sm2State(), 4).ease_factor == Decimal("2.50")


def test_quality_five_raises_ease_factor():
    assert calculate_next(Sm2State(), 5).ease_factor == Decimal("2.60")


def test_ease_factor_never_below_minimum():
    state = Sm2State()
    for _ in range(30):
        state = calculate_next(state, 3)  # 3점을 계속 받으면 계속 내려가려 한다
        assert state.ease_factor >= MIN_EASE_FACTOR
    assert state.ease_factor == Decimal("1.30")


def test_original_state_is_not_modified():
    state = Sm2State()
    calculate_next(state, 5)
    assert state == Sm2State()


@pytest.mark.parametrize("bad_quality", [-1, 6])
def test_out_of_range_quality_is_rejected(bad_quality):
    with pytest.raises(ValueError):
        calculate_next(Sm2State(), bad_quality)


def test_flashcard_rating_to_quality():
    assert flashcard_quality("dont_know") == 1
    assert flashcard_quality("unsure") == 3
    assert flashcard_quality("know") == 5


def test_unknown_rating_is_rejected():
    with pytest.raises(ValueError):
        flashcard_quality("maybe")
