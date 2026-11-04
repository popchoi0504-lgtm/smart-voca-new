# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 한국 시간(KST) 처리 모음 (데이터 설계서 DD-8: 사용자의 "하루"는 한국 시간 기준)
# 파일 위치: src/backend/app/core/timeutil.py
from datetime import date, datetime, timedelta, timezone

# 한국은 서머타임이 없어 항상 UTC+9 이다. 고정 시차를 쓰면 윈도우에서 별도 시간대 데이터를 설치하지 않아도 된다.
KST = timezone(timedelta(hours=9), "KST")


def now_utc() -> datetime:
    """지금 시각(UTC, 시간대 정보 포함)."""
    return datetime.now(timezone.utc)


def to_kst(moment: datetime) -> datetime:
    """시각을 한국 시간으로 바꿔 보여 준다. 시간대 정보가 없으면 UTC 로 본다."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(KST)


def today_kst() -> date:
    """한국 시간 기준 오늘 날짜."""
    return now_utc().astimezone(KST).date()
