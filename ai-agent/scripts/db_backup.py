#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 2026-11-05 - smart-voca - PostgreSQL 백업(pg_dump)과 복원(pg_restore) 도구 (NFR-DATA-01)
# 파일 위치: ai-agent/scripts/db_backup.py
# 실행: cd src/backend 후
#   .\.venv\Scripts\python.exe ..\..\ai-agent\scripts\db_backup.py backup [--target dev|test]
#   .\.venv\Scripts\python.exe ..\..\ai-agent\scripts\db_backup.py restore --file ..\..\backups\파일.dump [--target dev|test] [--yes]
# 접속 정보는 .env 의 DATABASE_URL / TEST_DATABASE_URL 에서 읽고, 비밀번호는 명령줄이 아닌 환경변수(PGPASSWORD)로만 넘긴다.
import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "backend"))  # app 패키지를 불러오기 위해

from sqlalchemy.engine import make_url  # noqa: E402

from app.core.config import get_settings  # noqa: E402

BACKUP_DIR = PROJECT_ROOT / "backups"
PG_BIN_CANDIDATES = [Path(r"C:\Program Files\PostgreSQL\17\bin")]


def find_tool(name: str) -> str:
    """PATH 에 없으면 PostgreSQL 17 기본 설치 위치에서 찾는다."""
    for folder in PG_BIN_CANDIDATES:
        candidate = folder / f"{name}.exe"
        if candidate.exists():
            return str(candidate)
    return name


def connection(target: str):
    settings = get_settings()
    url = make_url(settings.database_url if target == "dev" else settings.test_database_url)
    args = ["-h", url.host or "localhost", "-p", str(url.port or 5432), "-U", url.username, "-d", url.database]
    env = {**os.environ, "PGPASSWORD": url.password or ""}
    return url.database, args, env


def backup(target: str) -> int:
    database, args, env = connection(target)
    BACKUP_DIR.mkdir(exist_ok=True)
    out_file = BACKUP_DIR / f"{database}_{datetime.now():%y%m%d_%H%M%S}.dump"
    # -Fc: 압축된 pg_restore 전용 형식. --no-owner: 다른 컴퓨터·사용자에게 복원해도 소유자 오류가 나지 않게
    result = subprocess.run([find_tool("pg_dump"), *args, "-Fc", "--no-owner", "-f", str(out_file)], env=env)
    if result.returncode != 0:
        print("백업 실패")
        return 1
    print(f"백업 완료: {out_file} ({out_file.stat().st_size:,} bytes)")
    return 0


def restore(target: str, file: Path, confirmed: bool) -> int:
    database, args, env = connection(target)
    if not file.exists():
        print(f"파일이 없습니다: {file}")
        return 1
    if target == "dev" and not confirmed:
        print(f"개발 DB({database})의 현재 내용을 지우고 백업으로 덮어씁니다. 계속하려면 --yes 를 붙이세요.")
        return 1
    # --clean --if-exists: 같은 이름의 표가 있으면 지우고 다시 만든다. --no-owner: 소유자 정보는 무시
    result = subprocess.run(
        [find_tool("pg_restore"), *args, "--clean", "--if-exists", "--no-owner", "--exit-on-error", str(file)], env=env
    )
    if result.returncode != 0:
        print("복원 실패")
        return 1
    print(f"복원 완료: {file.name} → {database}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="DB 백업·복원")
    parser.add_argument("command", choices=["backup", "restore"])
    parser.add_argument("--target", choices=["dev", "test"], default="dev")
    parser.add_argument("--file", type=Path, help="복원할 .dump 파일")
    parser.add_argument("--yes", action="store_true", help="개발 DB 덮어쓰기 확인")
    args = parser.parse_args()
    if args.command == "backup":
        return backup(args.target)
    if args.file is None:
        print("restore 에는 --file 이 필요합니다.")
        return 1
    return restore(args.target, args.file, args.yes)


if __name__ == "__main__":
    sys.exit(main())
