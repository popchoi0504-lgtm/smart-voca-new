# -*- coding: utf-8 -*-
# 2026-11-25 - smart-voca - 내 단어 API 통합 테스트 (등록·수정·삭제·검색·CSV·공부, 이슈 #24, VOCA-FR-001~004)
# 파일 위치: src/backend/tests/test_my_words.py
from datetime import timedelta
from pathlib import Path

import pytest
from sqlalchemy import func, select

from consent_helpers import SIGNUP_CONSENT
from app.core.timeutil import today_kst
from app.models.my_word import MyWord
from app.models.word import Word

CREDENTIALS = {"email": "student@gmail.com", "password": "abcd1234"}
OTHER_CREDENTIALS = {"email": "other@gmail.com", "password": "abcd1234"}
SAMPLE_CSV = Path(__file__).resolve().parents[3] / "ai-agent" / "uploads" / "단어사전_샘플.csv"


@pytest.fixture
def client(api_client):
    assert api_client.post("/api/auth/signup", json={**CREDENTIALS, **SIGNUP_CONSENT}).status_code == 201
    return api_client


def add(client, headword="apple", meaning="사과"):
    return client.post("/api/my-words", json={"headword": headword, "meaning_ko": meaning})


def count(db_session):
    return db_session.scalar(select(func.count()).select_from(MyWord))


# ---------- 등록 (VOCA-FR-001) ----------

def test_create_and_list(client):
    response = add(client)
    assert response.status_code == 201
    assert response.json()["headword"] == "apple"
    listing = client.get("/api/my-words").json()
    assert listing["total_count"] == 1 and listing["items"][0]["meaning_ko"] == "사과"


def test_create_trims_spaces_and_keeps_case(client):
    assert add(client, "  Apple  ", "  사과 ").json()["headword"] == "Apple"


def test_create_duplicate_ignoring_case_is_409(client, db_session):
    add(client, "apple")
    response = add(client, "APPLE", "다른 뜻")
    assert response.status_code == 409 and response.json()["error"]["code"] == "MY_WORD_DUPLICATE"
    assert count(db_session) == 1


@pytest.mark.parametrize("body", [
    {"headword": "", "meaning_ko": "뜻"}, {"headword": "   ", "meaning_ko": "뜻"}, {"headword": "a", "meaning_ko": ""},
    {"headword": "a\nb", "meaning_ko": "뜻"}, {"headword": "a" * 101, "meaning_ko": "뜻"}, {"headword": "a"},
])
def test_create_rejects_bad_input(client, body):
    assert client.post("/api/my-words", json=body).status_code == 422


# ---------- 수정·삭제 (VOCA-FR-002) ----------

def test_update(client):
    word_id = add(client).json()["id"]
    response = client.put(f"/api/my-words/{word_id}", json={"headword": "apples", "meaning_ko": "사과들"})
    assert response.status_code == 200 and response.json()["headword"] == "apples"
    assert client.get("/api/my-words").json()["items"][0]["meaning_ko"] == "사과들"


def test_update_to_existing_word_is_409(client):
    add(client, "apple")
    other_id = add(client, "pear", "배").json()["id"]
    assert client.put(f"/api/my-words/{other_id}", json={"headword": "Apple", "meaning_ko": "x"}).status_code == 409


def test_update_same_word_keeps_working(client):
    word_id = add(client).json()["id"]  # 자기 자신과는 중복이 아니다
    assert client.put(f"/api/my-words/{word_id}", json={"headword": "APPLE", "meaning_ko": "사과!"}).status_code == 200


def test_delete(client, db_session):
    word_id = add(client).json()["id"]
    assert client.delete(f"/api/my-words/{word_id}").status_code == 204
    assert count(db_session) == 0
    assert client.delete(f"/api/my-words/{word_id}").status_code == 404


def test_other_users_word_is_404(client, api_client):
    word_id = add(client).json()["id"]
    api_client.post("/api/auth/logout")
    assert api_client.post("/api/auth/signup", json={**OTHER_CREDENTIALS, **SIGNUP_CONSENT}).status_code == 201
    assert api_client.get("/api/my-words").json()["total_count"] == 0
    assert api_client.put(f"/api/my-words/{word_id}", json={"headword": "x", "meaning_ko": "y"}).status_code == 404
    assert api_client.delete(f"/api/my-words/{word_id}").status_code == 404
    assert api_client.post(f"/api/my-words/{word_id}/review", json={"rating": "know"}).status_code == 404
    assert add(api_client, "apple").status_code == 201  # 다른 회원은 같은 단어를 따로 가질 수 있다


# ---------- 검색 (VOCA-FR-004) ----------

def test_search_by_headword_and_meaning(client):
    for headword, meaning in [("apple", "사과"), ("pineapple", "파인애플"), ("banana", "바나나 (과일)")]:
        add(client, headword, meaning)
    by_english = client.get("/api/my-words", params={"q": "APPLE"}).json()
    assert [item["headword"] for item in by_english["items"]] == ["apple", "pineapple"]
    by_korean = client.get("/api/my-words", params={"q": "과일"}).json()
    assert [item["headword"] for item in by_korean["items"]] == ["banana"]
    assert client.get("/api/my-words", params={"q": "zzz"}).json()["total_count"] == 0


def test_search_treats_percent_as_plain_character(client):
    add(client, "apple")
    assert client.get("/api/my-words", params={"q": "%"}).json()["total_count"] == 0


def test_list_is_paged_alphabetically(client):
    for number in range(55):
        add(client, f"w{number:02d}")
    first = client.get("/api/my-words").json()
    second = client.get("/api/my-words", params={"page": 2}).json()
    assert first["total_count"] == 55 and len(first["items"]) == 50 and len(second["items"]) == 5
    assert first["items"][0]["headword"] == "w00" and second["items"][-1]["headword"] == "w54"


def test_my_words_do_not_touch_shared_words(client, db_session):
    add(client)
    assert db_session.scalar(select(func.count()).select_from(Word)) == 0


# ---------- CSV (VOCA-FR-003) ----------

def post_csv(client, text):
    return client.post("/api/my-words/import", json={"csv_text": text})


def test_csv_imports_with_bom(client):
    response = post_csv(client, "﻿영단어,뜻\r\napple,사과\r\nbanana,바나나\r\n")
    assert response.status_code == 200
    assert response.json() == {"inserted": 2, "updated": 0, "duplicate_in_file": 0, "total_count": 2}


def test_csv_overwrites_meaning_ignoring_case(client):
    add(client, "apple", "옛 뜻")
    result = post_csv(client, "영단어,뜻\nAPPLE,새 뜻\nbanana,바나나\n").json()
    assert result["inserted"] == 1 and result["updated"] == 1
    items = {item["headword"]: item["meaning_ko"] for item in client.get("/api/my-words").json()["items"]}
    assert items == {"apple": "새 뜻", "banana": "바나나"}  # 이미 있던 표기(apple)는 그대로


def test_csv_duplicate_in_file_last_line_wins(client):
    result = post_csv(client, "영단어,뜻\npeck,앞 뜻\nPeck,나중 뜻\n").json()
    assert result["inserted"] == 1 and result["duplicate_in_file"] == 1
    assert client.get("/api/my-words").json()["items"][0]["meaning_ko"] == "나중 뜻"


def test_csv_keeps_review_progress_when_overwriting(client, db_session):
    word_id = add(client, "apple", "옛 뜻").json()["id"]
    client.post(f"/api/my-words/{word_id}/review", json={"rating": "know"})
    post_csv(client, "영단어,뜻\napple,새 뜻\n")
    word = db_session.scalar(select(MyWord))
    assert word.meaning_ko == "새 뜻" and word.repetitions == 1


@pytest.mark.parametrize("text", ["word,meaning\na,b\n", "", "영단어,뜻\n", "영단어,뜻\na,b,c\n", "영단어,뜻\na,\n"])
def test_csv_bad_files_change_nothing(client, db_session, text):
    add(client, "keep")
    response = post_csv(client, text)
    assert response.status_code == 422 and response.json()["error"]["code"] == "CSV_INVALID"
    assert count(db_session) == 1


def test_csv_one_bad_line_imports_nothing(client, db_session):
    assert post_csv(client, "영단어,뜻\na,가\nb\nc,다\n").status_code == 422
    assert count(db_session) == 0


def test_csv_skips_blank_lines(client):
    assert post_csv(client, "영단어,뜻\n\na,가\n\n").json()["inserted"] == 1


def test_csv_too_large_is_rejected(client):
    assert post_csv(client, "영단어,뜻\n" + "a,b\n" * 300_000).status_code == 422


def test_provided_sample_csv_imports_all(client, db_session):
    """교수님 제공 CSV(UTF-8 BOM, 2,000행)를 파일 그대로 읽어 가져온다. 영단어는 대소문자 무시로 1,999개."""
    csv_text = SAMPLE_CSV.read_text(encoding="utf-8-sig")
    result = post_csv(client, csv_text).json()
    assert result["inserted"] == 1999 and result["duplicate_in_file"] == 1 and result["total_count"] == 1999
    again = post_csv(client, csv_text).json()  # 두 번 가져와도 늘지 않는다
    assert again["inserted"] == 0 and again["total_count"] == 1999


def test_provided_sample_csv_with_bom_text_also_imports(client):
    raw_text = SAMPLE_CSV.read_bytes().decode("utf-8")  # BOM 이 글자 맨 앞에 남은 채로
    assert post_csv(client, raw_text).json()["inserted"] == 1999


# ---------- 공부 ----------

def test_study_returns_new_words_due_today(client):
    add(client, "apple")
    add(client, "pear", "배")
    study = client.get("/api/my-words/study").json()
    assert study["due_total"] == 2 and {item["headword"] for item in study["items"]} == {"apple", "pear"}


def test_study_is_limited_to_20_per_round(client):
    post_csv(client, "영단어,뜻\n" + "".join(f"w{n},뜻{n}\n" for n in range(30)))
    study = client.get("/api/my-words/study").json()
    assert study["due_total"] == 30 and len(study["items"]) == 20


def test_review_know_schedules_next_day_and_leaves_study_list(client):
    word_id = add(client).json()["id"]
    response = client.post(f"/api/my-words/{word_id}/review", json={"rating": "know"})
    assert response.status_code == 200
    assert response.json()["interval_days"] == 1
    assert response.json()["next_review_date"] == str(today_kst() + timedelta(days=1))
    assert client.get("/api/my-words/study").json()["due_total"] == 0


def test_review_second_success_goes_to_six_days(client):
    word_id = add(client).json()["id"]
    client.post(f"/api/my-words/{word_id}/review", json={"rating": "know"})
    assert client.post(f"/api/my-words/{word_id}/review", json={"rating": "know"}).json()["interval_days"] == 6


def test_review_dont_know_resets_to_one_day(client):
    word_id = add(client).json()["id"]
    client.post(f"/api/my-words/{word_id}/review", json={"rating": "know"})
    client.post(f"/api/my-words/{word_id}/review", json={"rating": "know"})
    assert client.post(f"/api/my-words/{word_id}/review", json={"rating": "dont_know"}).json()["interval_days"] == 1


def test_review_rejects_unknown_rating(client):
    word_id = add(client).json()["id"]
    assert client.post(f"/api/my-words/{word_id}/review", json={"rating": "great"}).status_code == 422


def test_withdraw_deletes_my_words(client, db_session):
    add(client)
    response = client.post("/api/me/withdraw", json={"password": CREDENTIALS["password"], "confirm_text": "탈퇴합니다"})
    assert response.status_code == 204, response.text
    assert count(db_session) == 0


def test_requires_login(api_client):
    assert api_client.get("/api/my-words").status_code == 401
    assert api_client.post("/api/my-words", json={"headword": "a", "meaning_ko": "b"}).status_code == 401
    assert api_client.post("/api/my-words/import", json={"csv_text": "x"}).status_code == 401
    assert api_client.get("/api/my-words/study").status_code == 401
    assert api_client.delete("/api/my-words/1").status_code == 401
