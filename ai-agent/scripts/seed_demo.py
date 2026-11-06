#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - 시연용 데모 계정·학습 이력과 화면 확인용 임시 계정을 개발 DB 에 만드는 스크립트
# 파일 위치: ai-agent/scripts/seed_demo.py
# 실행: cd src/backend 후  .\.venv\Scripts\python.exe ..\..\ai-agent\scripts\seed_demo.py <명령> [--premium-days N]
#   demo           데모 계정을 (다시) 만든다. 여러 번 실행해도 같은 결과(기존 데모 이력은 지우고 새로 채움)
#   check-free     임시 확인 계정을 무료 상태로: 1~249번을 배운 것으로 채움 → 다음 새 단어가 250번(무료 마지막)
#   check-premium  같은 임시 계정을 이용권 상태로: 1~500번을 배운 것으로 채움 → 다음 새 단어가 501번
#   check-cleanup  임시 확인 계정과 그 기록을 지운다
# 데모·임시 계정은 시연·확인 전용이다. 비밀번호는 환경변수로 바꿀 수 있다(DEMO_PASSWORD).
import argparse
import os
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "backend"))  # app 패키지를 불러오기 위해

from sqlalchemy import create_engine, delete, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.core.timeutil import now_utc, today_kst  # noqa: E402
from app.core_logic.consent_rules import TERMS_VERSION  # noqa: E402
from app.models import payment, review_log, user_word  # noqa: E402,F401
from app.models.review_log import ReviewLog  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.user_word import UserWord  # noqa: E402
from app.models.word import Word  # noqa: E402

DEMO_EMAIL = "demo@smartvoca.com"
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "Demo-1234-voca")
CHECK_EMAIL = "check.temp@smartvoca.com"
CHECK_PASSWORD = "Check-1234-temp"


def get_or_create_user(session: Session, email: str, password: str) -> User:
    user = session.scalar(select(User).where(User.email == email))
    if user is None:
        # 가입 동의 기록(이슈 #18)도 함께 남겨 실제 가입한 회원과 같은 모양으로 만든다
        user = User(email=email, password_hash=hash_password(password), terms_agreed_at=now_utc(), terms_version=TERMS_VERSION)
        session.add(user)
        session.flush()
    return user


def word_ids_by_rank(session: Session, last_rank: int) -> dict[int, int]:
    rows = session.execute(select(Word.frequency_rank, Word.id).where(Word.frequency_rank <= last_rank)).all()
    ids = {rank: word_id for rank, word_id in rows}
    missing = [rank for rank in range(1, last_rank + 1) if rank not in ids]
    if missing:
        raise SystemExit(f"words 표에 순위 {missing[:3]}... 가 없습니다. 먼저 seed_words.py 를 실행하세요.")
    return ids


def clear_history(session: Session, user: User) -> None:
    session.execute(delete(ReviewLog).where(ReviewLog.user_id == user.id))
    session.execute(delete(UserWord).where(UserWord.user_id == user.id))


def fill_learned(session: Session, user: User, last_rank: int) -> None:
    """1~last_rank 번을 '배운 것'으로 채운다(화면 확인용). 복습일은 멀리 두어 퀴즈에 섞이지 않게 한다."""
    ids = word_ids_by_rank(session, last_rank)
    moment = now_utc() - timedelta(days=30)
    session.add_all(
        UserWord(user_id=user.id, word_id=ids[rank], repetitions=3, interval_days=10, ease_factor=Decimal("2.50"),
                 next_review_date=today_kst() + timedelta(days=10), first_learned_at=moment, last_reviewed_at=moment)
        for rank in range(1, last_rank + 1)
    )


def seed_demo(session: Session, premium_days: int) -> None:
    """데모 이력: 최근 6일(어제까지) 매일 새 단어 5개씩(1~30번) + 퀴즈 기록. 오늘은 비워 두어 시연 중 연속 학습일이 7일이 되게 한다.
    복습 퀴즈가 바로 나오도록 8개 단어는 오늘 복습 대상, 5개는 21일 이상 간격(익숙함)으로 둔다."""
    user = get_or_create_user(session, DEMO_EMAIL, DEMO_PASSWORD)
    user.password_hash = hash_password(DEMO_PASSWORD)  # 다시 실행하면 비밀번호도 기본값으로 되돌린다
    user.premium_until = now_utc() + timedelta(days=premium_days) if premium_days > 0 else None
    clear_history(session, user)
    session.flush()

    ids = word_ids_by_rank(session, 30)
    today = today_kst()
    for day_index in range(6):  # 0 = 6일 전 ... 5 = 어제
        study_date = today - timedelta(days=6 - day_index)
        moment = now_utc() - timedelta(days=6 - day_index)
        for offset in range(5):
            rank = day_index * 5 + offset + 1
            rating, quality = ("know", 5) if rank % 3 else ("unsure", 3)
            session.add(ReviewLog(user_id=user.id, word_id=ids[rank], activity_type="flashcard", result=rating,
                                  max_hint_level=0, sm2_quality=quality, reviewed_at=moment, study_date=study_date))
            if day_index >= 1 and offset < 2:  # 이튿날부터 하루 2번은 복습 퀴즈도 한 것으로
                session.add(ReviewLog(user_id=user.id, word_id=ids[rank - 5], activity_type="quiz", result="correct",
                                      max_hint_level=0, sm2_quality=5, reviewed_at=moment, study_date=study_date))
            if rank <= 5:  # 익숙함: 간격 25일
                state = (4, 25, "2.60", today + timedelta(days=15))
            elif rank <= 13:  # 오늘 복습 대상
                state = (1, 1, "2.36", today)
            else:  # 학습 중
                state = (2, 6, "2.50", today + timedelta(days=2 + rank % 5))
            session.add(UserWord(user_id=user.id, word_id=ids[rank], repetitions=state[0], interval_days=state[1],
                                 ease_factor=Decimal(state[2]), next_review_date=state[3],
                                 first_learned_at=moment, last_reviewed_at=moment))
    print(f"데모 계정 준비: {DEMO_EMAIL} (이용권 {'있음 ' + str(premium_days) + '일' if premium_days > 0 else '없음=무료'}), 단어 30개·6일 이력")


def main() -> int:
    parser = argparse.ArgumentParser(description="데모·확인용 계정 준비")
    parser.add_argument("command", choices=["demo", "check-free", "check-premium", "check-cleanup"])
    parser.add_argument("--premium-days", type=int, default=0, help="demo 에 이용권을 줄 일수(기본 0=무료)")
    args = parser.parse_args()

    engine = create_engine(get_settings().database_url)  # 개발 DB 만 대상으로 한다
    with Session(engine) as session:
        if args.command == "demo":
            seed_demo(session, args.premium_days)
        elif args.command == "check-cleanup":
            user = session.scalar(select(User).where(User.email == CHECK_EMAIL))
            if user is None:
                print("임시 확인 계정이 없습니다.")
            else:
                clear_history(session, user)
                session.delete(user)
                print("임시 확인 계정과 기록을 지웠습니다.")
        else:
            user = get_or_create_user(session, CHECK_EMAIL, CHECK_PASSWORD)
            clear_history(session, user)
            session.flush()
            if args.command == "check-free":
                user.premium_until = None
                fill_learned(session, user, 249)
            else:
                user.premium_until = now_utc() + timedelta(days=1)
                fill_learned(session, user, 500)
            user.daily_new_limit = 10
            print(f"임시 확인 계정 {args.command} 준비 완료: {CHECK_EMAIL}")
        session.commit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
