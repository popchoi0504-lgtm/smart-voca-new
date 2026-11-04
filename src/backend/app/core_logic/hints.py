# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 퀴즈 힌트 생성 (철자 섞기, 빈칸). 순수 함수: DB·화면을 모른다 (FR-HINT-01·02·05·06, IF-5)
# 파일 위치: src/backend/app/core_logic/hints.py
import hashlib
import random
from datetime import date

SCRAMBLE_MIN_LETTERS = 4  # 글자 수가 이보다 적으면(3 이하) 섞기 힌트를 건너뛴다
REVEAL_RATIO = 0.4  # 빈칸 힌트에서 공개할 글자 비율(첫 글자 포함). 설계서 FR-HINT-02
FIXED_CHARS = (" ", "-")  # 섞거나 가리지 않고 제자리에 두는 구분 문자
BLANK = "_"


def make_seed(user_id: int, word_id: int, day: date, level: int) -> int:
    """회원·단어·날짜·힌트 단계로 정해지는 고정 숫자. 같은 입력이면 항상 같은 값(IF-5).

    왜 hash() 를 안 쓰나: 파이썬 기본 hash() 는 실행할 때마다 값이 달라진다. sha256 은 항상 같다.
    """
    text = f"{user_id}:{word_id}:{day.isoformat()}:{level}"
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")


def _letter_positions(word: str) -> list[int]:
    """공백·하이픈이 아닌 글자의 위치 목록."""
    return [i for i, ch in enumerate(word) if ch not in FIXED_CHARS]


def letter_count(word: str) -> int:
    """공백·하이픈을 뺀 글자 수 (문제 목록의 letter_count 와 같은 규칙)."""
    return len(_letter_positions(word))


def can_scramble(word: str) -> bool:
    """섞기 힌트를 낼 수 있는가: 글자 4개 이상이고, 서로 다른 글자가 2종류 이상(FR-HINT-05)."""
    letters = [word[i] for i in _letter_positions(word)]
    return len(letters) >= SCRAMBLE_MIN_LETTERS and len(set(letters)) > 1


def scramble(word: str, seed: int) -> str | None:
    """글자를 섞은 문자열. 건너뛰는 단어면 None. 공백·하이픈은 제자리에 둔다.

    섞은 결과가 원래 단어와 같으면 다시 섞는다(FR-HINT-01). 같은 seed 는 항상 같은 결과.
    서로 다른 글자가 2종류 이상이면 원형과 다른 배열이 반드시 있으므로 반복은 끝난다.
    """
    if not can_scramble(word):
        return None
    rng = random.Random(seed)
    positions = _letter_positions(word)
    letters = [word[i] for i in positions]
    while True:
        shuffled = letters[:]
        rng.shuffle(shuffled)
        if shuffled != letters:
            break
    result = list(word)
    for position, letter in zip(positions, shuffled):
        result[position] = letter
    return "".join(result)


def mask(word: str, seed: int) -> list[str]:
    """빈칸 힌트: 글자 배열. 첫 글자는 항상 공개, 나머지 공개 칸은 seed 로 고정된 위치를 고른다.

    공개된 글자는 정답의 같은 위치 글자 그대로다(FR-HINT-02). 가려진 칸은 "_".
    공개 개수는 글자 수의 약 40%(반올림, 최소 1). 단, 한 칸 이상은 반드시 가린다.
    """
    positions = _letter_positions(word)
    total = len(positions)
    reveal_count = max(1, round(total * REVEAL_RATIO))
    reveal_count = min(reveal_count, max(1, total - 1))  # 한 글자짜리 단어가 아니면 최소 1칸은 가림
    rng = random.Random(seed)
    others = positions[1:]
    revealed = {positions[0]} | set(rng.sample(others, min(reveal_count - 1, len(others))))
    return [ch if (ch in FIXED_CHARS or i in revealed) else BLANK for i, ch in enumerate(word)]
