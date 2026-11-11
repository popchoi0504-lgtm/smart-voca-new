# smart-voca

**파일 위치**: `README.md`
**작성일**: 2026-11-03
**설명**: 토익 영단어를 짧은 시간에 반복해서 잊지 않고 외우도록 돕는 웹 서비스 (개발 중). 실행 방법을 적은 안내 문서 (VS-7 기준). 자세한 운영·백업·시연 절차는 `docs/운영_261105_운영·배포 정의서(Operations Guide) v1.0.md`

---

## 준비물 (이 컴퓨터에서 확인된 버전)

| 도구 | 버전 | 용도 |
|---|---|---|
| Python | 3.14.3 | 서버 |
| Node.js / npm | v24 / 11 | 화면 |
| PostgreSQL | 17 | DB (서비스 `postgresql-x64-17` 실행 중이어야 함) |

## 처음 한 번만 (새 컴퓨터에서)

PowerShell 기준.

```powershell
# 1) 서버 패키지 설치
cd src\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2) 화면 패키지 설치
cd ..\frontend
npm install

# 3) 설정 파일 만들기: .env.example 을 .env 로 복사한 뒤 값을 채운다
cd ..\..
copy .env.example .env
```

DB(`smart_voca`, `smart_voca_test`)와 전용 사용자는 PostgreSQL 관리자 계정으로 한 번 만들어야 한다.

```powershell
# 4) DB 표 만들기: DB 와 .env 가 준비된 뒤 한 번 (그리고 새 변경 파일이 생길 때마다)
cd src\backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

```powershell
# 5) 단어 2,000개 넣기: 4) 다음에 한 번 (여러 번 실행해도 2,000개 유지). 검증만 하려면 --dry-run
cd src\backend
.\.venv\Scripts\python.exe ..\..\ai-agent\scripts\seed_words.py
```

단어의 출처와 선정 기준은 `data/words/README.md` 를 본다.

## 실행 (터미널 2개)

```powershell
# 터미널 1: 서버 (주소 http://127.0.0.1:8000)
cd src\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 터미널 2: 화면 (브라우저에서 http://localhost:5173 로 접속)
cd src\frontend
npm run dev
```

- 화면은 `http://localhost:5173` 으로 접속한다. (`127.0.0.1:5173` 은 안 열릴 수 있다. 화면 서버가 IPv6 주소로 대기하기 때문)
- 서버 자동 문서: `http://localhost:5173/api/docs`
- 끌 때는 각 터미널에서 `Ctrl + C`

## 테스트

```powershell
cd src\backend
.\.venv\Scripts\python.exe -m pytest -v
```

## 시연용 데모 계정

```powershell
cd src\backend
.\.venv\Scripts\python.exe ..\..\ai-agent\scripts\seed_demo.py demo
```

`demo@smartvoca.com` / 기본 비밀번호는 운영·배포 정의서 5.2. 6일 학습 이력이 들어 있고, 여러 번 실행해도 같은 상태로 초기화된다.

## 백업·복원

```powershell
cd src\backend
.\.venv\Scripts\python.exe ..\..\ai-agent\scripts\db_backup.py backup
```

`backups\` 에 `.dump` 파일이 생긴다(Git 제외). 복원 방법은 운영·배포 정의서 6장.

## 문서

기획·분석·설계 문서는 `ai-agent/claude/` 에 있다. 작업 순서는 `작업계획_261103_구현 계획서` 를 따른다.
