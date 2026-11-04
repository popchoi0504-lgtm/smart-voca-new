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


# 퀴즈 점수 (인터페이스 정의서 4.4, FR-SRS-03). 정답은 힌트를 많이 쓸수록 점수가 낮다.
QUIZ_CORRECT_QUALITY = {0: 5, 1: 4, 2: 3}  # 사용한 최고 힌트 단계 → 점수
QUIZ_WRONG_QUALITY = 1
QUIZ_REVEALED_QUALITY = 2  # 정답 확인(3단계): 오답보다 덜 감점하되 복습은 앞당긴다 (D-5)


def quiz_quality(result: str, max_hint_level: int) -> int:
    """퀴즈 결과(correct/wrong/revealed)와 최고 힌트 단계(0~3)를 SM-2 점수로 바꾼다."""
    if result == "wrong":
        return QUIZ_WRONG_QUALITY
    if result == "revealed":
        return QUIZ_REVEALED_QUALITY
    if result == "correct":
        if max_hint_level not in QUIZ_CORRECT_QUALITY:  # 3단계까지 봤으면 정답이 아니라 revealed 여야 한다
            raise ValueError(f"correct 에 허용되지 않는 힌트 단계: {max_hint_level}")
        return QUIZ_CORRECT_QUALITY[max_hint_level]
    raise ValueError(f"알 수 없는 퀴즈 결과: {result}")
