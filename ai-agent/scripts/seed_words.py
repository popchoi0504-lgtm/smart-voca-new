#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-04 - smart-voca - 단어 CSV 를 검증하고 words 표에 적재하는 시드 스크립트 (여러 번 실행해도 안전)
# 파일 위치: ai-agent/scripts/seed_words.py
# 실행: cd src/backend 후  .\.venv\Scripts\python.exe ..\..\ai-agent\scripts\seed_words.py [--dry-run] [--target dev|test] [--csv 경로]
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "src" / "backend"
sys.path.insert(0, str(BACKEND_DIR))  # app 패키지를 불러오기 위해

from sqlalchemy import create_engine, func, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.models.word import Word  # noqa: E402
from app.services.word_import import WordImportError, import_words, read_word_csv, validate_rows  # noqa: E402

DEFAULT_CSV = PROJECT_ROOT / "data" / "words" / "toeic_500.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description="단어 CSV 검증·적재")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--target", choices=["dev", "test"], default="dev", help="dev: 개발 DB, test: 테스트 DB")
    parser.add_argument("--dry-run", action="store_true", help="검증만 하고 적재하지 않음")
    args = parser.parse_args()

    rows, errors = read_word_csv(args.csv)
    errors += validate_rows(rows) if rows else []
    if errors:
        print(f"검증 실패 {len(errors)}건 (적재하지 않음):")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"검증 통과: {len(rows)}행")
    if args.dry_run:
        return 0

    settings = get_settings()
    database_url = settings.database_url if args.target == "dev" else settings.test_database_url
    engine = create_engine(database_url)
    try:
        with Session(engine) as session:
            result = import_words(session, rows)
            session.commit()  # 한 트랜잭션: 중간에 실패하면 아무것도 반영되지 않는다
            total = session.scalar(select(func.count()).select_from(Word))
    except WordImportError as error:
        print(f"적재 실패: {error}")
        return 1
    print(f"적재 완료({args.target}): 추가 {result['inserted']}, 갱신 {result['updated']}, DB 총 {total}행")
    return 0


if __name__ == "__main__":
    sys.exit(main())
