# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 연속 학습일 계산과 숙련도 구간 규칙 (FR-PROG-03·04, 데이터 설계서 4.3·DD-3, 인터페이스 정의서 4.5)
# 파일 위치: src/backend/app/core_logic/progress_rules.py
from collections.abc import Iterable
from datetime import date, timedelta

# interval_days 가 이 값 이상이면 "익숙함". 임시 기준(설계서 [설계 확정], 구현 후 조정 가능)
FAMILIAR_INTERVAL_DAYS = 21

MASTERY_LEARNING = "learning"
MASTERY_FAMILIAR = "familiar"


def classify_mastery(interval_days: int) -> str:
    """학습한 적 있는 단어의 숙련도. (새 단어는 user_words 행이 없어서 여기로 오지 않는다)"""
    return MASTERY_FAMILIAR if interval_days >= FAMILIAR_INTERVAL_DAYS else MASTERY_LEARNING


def calculate_streak(study_dates: Iterable[date], today: date) -> int:
    """연속 학습일 수.

    - 오늘 학습했으면 오늘부터, 오늘은 아직인데 어제 했으면 어제부터 거꾸로 센다(어제까지 이어졌으면 끊기지 않음).
    - 하루라도 비면 거기서 멈춘다. 오늘과 어제 모두 없으면 0.
    - 오늘에서 거꾸로만 세므로 today 보다 미래 날짜는 저절로 무시된다(별도 처리 불필요).
    같은 날이 여러 번 들어와도 하루로 센다.
    """
    days = set(study_dates)
    cursor = today if today in days else today - timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def calculate_longest_streak(study_dates: Iterable[date]) -> int:
    """지금까지의 가장 긴 연속 학습일 수(오늘과 무관). 날짜를 정렬해 이어지는 묶음의 최대 길이를 센다."""
    longest = current = 0
    previous: date | None = None
    for day in sorted(set(study_dates)):
        current = current + 1 if previous is not None and day - previous == timedelta(days=1) else 1
        longest = max(longest, current)
        previous = day
    return longest
