# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 단어 CSV 검증 규칙과 적재(upsert) 테스트
# 파일 위치: src/backend/tests/test_word_import.py
import pytest
from sqlalchemy import func, select

from app.models.word import Word
from app.services.word_import import (
    WordImportError, WordRow, example_contains_headword, import_words, read_word_csv, validate_rows,
)

HEADER = "frequency_rank,headword,part_of_speech,meaning_ko,example_en,example_ko\n"


def make_row(rank=1, headword="client", pos="n.", meaning="고객",
             example_en="Our client will arrive at the office before the meeting.", example_ko="우리 고객이 회의 전에 사무실에 도착할 것입니다."):
    return WordRow(rank + 1, rank, headword, pos, meaning, example_en, example_ko)


def test_올바른_행은_오류가_없다():
    assert validate_rows([make_row()]) == []


@pytest.mark.parametrize("change, expected_text", [
    ({"headword": "Client"}, "소문자"),
    ({"headword": "o'clock"}, "소문자"),
    ({"pos": "noun"}, "품사"),
    ({"meaning": "가" * 61}, "meaning_ko"),
    ({"example_ko": "가" * 101}, "example_ko"),
    ({"example_en": "Too short sentence."}, "단어"),
    ({"example_en": "Our clients will arrive at the office before the meeting."}, "그대로"),
])
def test_규칙을_어기면_오류_메시지가_나온다(change, expected_text):
    errors = validate_rows([make_row(**change)])
    assert any(expected_text in error for error in errors)


def test_headword_중복과_순위_누락을_잡는다():
    errors = validate_rows([make_row(rank=1), make_row(rank=3)])
    assert any("연속" in error for error in errors)
    errors = validate_rows([make_row(rank=1), make_row(rank=2)])
    assert any("중복" in error for error in errors)


def test_예문_포함_검사는_단어_경계를_본다():
    assert example_contains_headword("Please sign the form.", "sign")
    assert example_contains_headword("Sign here, please.", "sign")  # 대소문자 무시
    assert not example_contains_headword("We design the form.", "sign")  # 다른 단어의 일부는 불가
    assert example_contains_headword("An e-book is on sale for the next week.", "e-book")


def test_csv_읽기_열_수와_빈_값_오류에_줄_번호가_붙는다(tmp_path):
    csv_path = tmp_path / "words.csv"
    csv_path.write_text(HEADER + "1,client,n.,고객,A client is here today at our office.,고객이 왔다\n2,memo,n.\n3,fax,n.,,x,y\n", encoding="utf-8")
    rows, errors = read_word_csv(csv_path)
    assert len(rows) == 1
    assert any(error.startswith("3줄") for error in errors) and any(error.startswith("4줄") for error in errors)


def test_csv_머리글이_다르면_중단한다(tmp_path):
    csv_path = tmp_path / "words.csv"
    csv_path.write_text("rank,word\n1,a\n", encoding="utf-8")
    rows, errors = read_word_csv(csv_path)
    assert rows == [] and "머리글" in errors[0]


SAMPLE = [
    make_row(1, "client"),
    make_row(2, "memo", "n.", "메모", "Please send me a memo about the new schedule today.", "새 일정에 관한 메모를 보내 주세요."),
    make_row(3, "reservation", "n.", "예약", "I would like to confirm my reservation for the conference room.", "회의실 예약을 확인하고 싶습니다."),
]


def test_적재를_두_번_해도_행_수가_같다(db_session):
    first = import_words(db_session, SAMPLE)
    db_session.commit()
    second = import_words(db_session, SAMPLE)
    db_session.commit()
    assert first == {"inserted": 3, "updated": 0} and second == {"inserted": 0, "updated": 3}
    assert db_session.scalar(select(func.count()).select_from(Word)) == 3


def test_순위를_서로_바꿔도_충돌하지_않는다(db_session):
    import_words(db_session, SAMPLE)
    db_session.commit()
    swapped = [make_row(1, "memo", "n.", "메모", SAMPLE[1].example_en, SAMPLE[1].example_ko),
               make_row(2, "client"), SAMPLE[2]]
    import_words(db_session, swapped)
    db_session.commit()
    ranks = dict(db_session.execute(select(Word.headword, Word.frequency_rank)).all())
    assert ranks == {"memo": 1, "client": 2, "reservation": 3}


def test_내용_수정은_같은_행에_반영된다(db_session):
    import_words(db_session, SAMPLE)
    db_session.commit()
    original_id = db_session.scalar(select(Word.id).where(Word.headword == "client"))
    changed = [make_row(1, "client", meaning="고객, 의뢰인"), SAMPLE[1], SAMPLE[2]]
    import_words(db_session, changed)
    db_session.commit()
    word = db_session.scalar(select(Word).where(Word.headword == "client"))
    assert word.id == original_id and word.meaning_ko == "고객, 의뢰인"


def test_DB에만_있는_단어가_있으면_오류를_내고_아무것도_바꾸지_않는다(db_session):
    import_words(db_session, SAMPLE)
    db_session.commit()
    with pytest.raises(WordImportError, match="reservation"):
        import_words(db_session, SAMPLE[:2])
    db_session.rollback()
    assert db_session.scalar(select(func.count()).select_from(Word)) == 3
