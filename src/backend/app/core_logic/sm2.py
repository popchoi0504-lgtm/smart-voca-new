# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - SM-2 복습 간격 계산 (순수 함수: DB·화면을 모른다) (FR-SRS-01·02·06)
# 파일 위치: src/backend/app/core_logic/sm2.py
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

MIN_EASE_FACTOR = Decimal("1.30")  # SM-2 규칙: 난이도 계수 하한
INITIAL_EASE_FACTOR = Decimal("2.50")
PASS_QUALITY = 3  # 이 점수 이상이면 "기억했다"로 본다 (SM-2 원 규칙)
FIRST_INTERVAL_DAYS = 1
SECOND_INTERVAL_DAYS = 6


@dataclass(frozen=True)
class Sm2State:
    """한 사용자-단어의 SM-2 상태값 3개. (DB 의 user_words 컬럼과 같은 의미)"""

    repetitions: int = 0  # 연속 성공 횟수
    interval_days: int = 0  # 현재 복습 간격(일)
    ease_factor: Decimal = INITIAL_EASE_FACTOR  # 난이도 계수 (클수록 쉬운 단어)


def calculate_next(state: Sm2State, quality: int) -> Sm2State:
    """답한 점수(0~5)를 반영해 다음 상태를 계산한다. 원래 상태는 바꾸지 않고 새 상태를 돌려준다.

    - 3점 미만(실패): 연속 성공 횟수를 0 으로 되돌리고 내일 다시 본다. 난이도 계수는 그대로 둔다(SM-2 원 규칙).
    - 3점 이상(성공): 1번째 성공 1일 → 2번째 6일 → 이후 (이전 간격 × 난이도 계수). 난이도 계수도 점수에 따라 조정.
    """
    if not 0 <= quality <= 5:
        raise ValueError(f"quality 는 0~5 여야 합니다: {quality}")

    if quality < PASS_QUALITY:
        return Sm2State(repetitions=0, interval_days=FIRST_INTERVAL_DAYS, ease_factor=state.ease_factor)

    if state.repetitions == 0:
        interval_days = FIRST_INTERVAL_DAYS
    elif state.repetitions == 1:
        interval_days = SECOND_INTERVAL_DAYS
    else:
        interval_days = int((state.interval_days * state.ease_factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    return Sm2State(
        repetitions=state.repetitions + 1,
        interval_days=interval_days,
        ease_factor=_adjust_ease_factor(state.ease_factor, quality),
    )


def _adjust_ease_factor(ease_factor: Decimal, quality: int) -> Decimal:
    """SM-2 공식: EF' = EF + (0.1 - (5-q) × (0.08 + (5-q) × 0.02)). 1.30 아래로는 내려가지 않는다.

    5점이면 +0.10, 4점이면 0, 3점이면 -0.14. 소수 오차가 쌓이지 않도록 Decimal 로 계산한다.
    """
    gap = Decimal(5 - quality)
    adjusted = ease_factor + Decimal("0.1") - gap * (Decimal("0.08") + gap * Decimal("0.02"))
    adjusted = adjusted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return max(adjusted, MIN_EASE_FACTOR)
