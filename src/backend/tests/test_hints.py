# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 힌트(섞기·빈칸)와 퀴즈 점수 변환 단위 테스트 (FR-HINT-01·02·05·06, IF-5, 구현 계획서 VS-4)
# 파일 위치: src/backend/tests/test_hints.py
from datetime import date

import pytest

from app.core_logic.hints import can_scramble, letter_count, make_seed, mask, scramble
from app.core_logic.quality import quiz_quality

WORDS = ["negotiate", "contract", "ice cream", "state-of-the-art", "abc d", "aab", "aaaa", "go", "supply chain"]
SEEDS = range(200)


@pytest.mark.parametrize("word", ["negotiate", "contract", "ice cream", "state-of-the-art", "supply chain", "abba"])
def test_scramble_differs_from_original_and_keeps_letters(word):
    for seed in SEEDS:
        result = scramble(word, seed)
        assert result != word
        assert sorted(result.replace(" ", "").replace("-", "")) == sorted(word.replace(" ", "").replace("-", ""))


def test_scramble_retries_when_shuffle_equals_original():
    # 'abba' 처럼 같은 글자가 있는 단어도 200개 seed 모두 원형과 다르다(위 테스트). 두 글자 종류뿐인 'aaab' 도 확인
    assert all(scramble("aaab", seed) != "aaab" for seed in SEEDS)


@pytest.mark.parametrize("word", ["go", "cat", "aab", "aaaa", "a b", "ab-c"])
def test_scramble_skipped_for_short_or_same_letter_words(word):
    assert scramble(word, 1) is None
    assert can_scramble(word) is False


def test_scramble_not_skipped_for_four_letters():
    assert can_scramble("abcd") is True
    assert scramble("abcd", 1) not in (None, "abcd")


def test_scramble_keeps_space_and_hyphen_in_place():
    for word in ["ice cream", "state-of-the-art", "supply chain"]:
        for seed in SEEDS:
            result = scramble(word, seed)
            for i, ch in enumerate(word):
                if ch in " -":
                    assert result[i] == ch
                else:
                    assert result[i] not in " -"


def test_scramble_is_deterministic():
    assert scramble("negotiate", 42) == scramble("negotiate", 42)


def test_scramble_varies_with_seed():
    assert len({scramble("negotiate", seed) for seed in SEEDS}) > 50


@pytest.mark.parametrize("word", WORDS)
def test_mask_reveals_only_same_position_letters(word):
    for seed in SEEDS:
        masked = mask(word, seed)
        assert len(masked) == len(word)
        for original, shown in zip(word, masked):
            assert shown in (original, "_")


@pytest.mark.parametrize("word", WORDS)
def test_mask_always_reveals_first_letter(word):
    first_letter_index = next(i for i, ch in enumerate(word) if ch not in " -")
    for seed in SEEDS:
        assert mask(word, seed)[first_letter_index] == word[first_letter_index]


def test_mask_keeps_space_and_hyphen():
    for seed in SEEDS:
        assert mask("ice cream", seed)[3] == " "
        assert mask("state-of-the-art", seed)[5] == "-"


def test_mask_reveal_count_is_about_40_percent():
    # negotiate 9글자 → round(3.6)=4칸 공개, contract 8글자 → round(3.2)=3칸
    assert sum(ch != "_" for ch in mask("negotiate", 7)) == 4
    assert sum(ch != "_" for ch in mask("contract", 7)) == 3


def test_mask_always_hides_at_least_one_letter():
    for word in ["go", "ab", "abc"]:
        for seed in SEEDS:
            assert "_" in mask(word, seed)


def test_mask_is_deterministic_and_varies_with_seed():
    assert mask("negotiate", 5) == mask("negotiate", 5)
    assert len({tuple(mask("negotiate", seed)) for seed in SEEDS}) > 5


def test_make_seed_same_input_same_value():
    assert make_seed(1, 7, date(2026, 11, 4), 2) == make_seed(1, 7, date(2026, 11, 4), 2)


def test_make_seed_changes_with_each_input():
    base = make_seed(1, 7, date(2026, 11, 4), 2)
    assert make_seed(2, 7, date(2026, 11, 4), 2) != base
    assert make_seed(1, 8, date(2026, 11, 4), 2) != base
    assert make_seed(1, 7, date(2026, 11, 5), 2) != base
    assert make_seed(1, 7, date(2026, 11, 4), 1) != base


def test_letter_count_ignores_space_and_hyphen():
    assert letter_count("ice cream") ==8
    assert letter_count("state-of-the-art") == 13


@pytest.mark.parametrize(
    "result, hint_level, expected",
    [("correct", 0, 5), ("correct", 1, 4), ("correct", 2, 3), ("wrong", 0, 1), ("wrong", 2, 1),
     ("revealed", 3, 2)],
)
def test_quiz_quality_table(result, hint_level, expected):
    assert quiz_quality(result, hint_level) == expected


def test_quiz_quality_rejects_invalid():
    with pytest.raises(ValueError):
        quiz_quality("correct", 3)
    with pytest.raises(ValueError):
        quiz_quality("skipped", 0)
