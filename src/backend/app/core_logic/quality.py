# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 플래시카드 자기 평가 → SM-2 점수(0~5) 변환 (FR-SRS-03, 인터페이스 정의서 4.3)
# 파일 위치: src/backend/app/core_logic/quality.py

# 몰랐음=1(실패), 애매함=3(간신히 성공), 알았음=5(완벽). 변환 규칙을 바꾸려면 이 표만 고치면 된다.
FLASHCARD_QUALITY = {
    "dont_know": 1,
    "unsure": 3,
    "know": 5,
}


def flashcard_quality(rating: str) -> int:
    """플래시카드 평가(dont_know/unsure/know)를 SM-2 점수로 바꾼다. 모르는 값이면 ValueError."""
    try:
        return FLASHCARD_QUALITY[rating]
    except KeyError:
        raise ValueError(f"알 수 없는 평가값: {rating}") from None
