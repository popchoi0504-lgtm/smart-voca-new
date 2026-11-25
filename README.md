# smart-voca

**파일 위치**: `README.md`
**작성일**: 2026-11-03 (2026-11-25 SQLite·Docker 기준으로 개정)
**설명**: 토익 영단어를 짧은 시간에 반복해서 잊지 않고 외우도록 돕는 영어단어 학습 웹 앱. 기말 과제로 제출하는 개인 프로젝트.

---

## 앱 소개

- 단어 카드로 새 단어를 배우고, 퀴즈(직접 입력·3단계 힌트)로 복습한다. 복습 시점은 SM-2 간격 반복 공식으로 계산한다.
- 학습 기록(연속 학습일, 숙련도, 달력)을 DB 이력으로 계산해 보여 준다.
- 회원가입·로그인, 프로필 설정, 즐겨찾기, AI 선생님(서버 제출본은 가짜 답변), 기간제 이용권 결제(서버 제출본은 가짜 결제)가 있다.
- 단어 2,000개(TSL + NGSL)가 처음 실행할 때 DB 에 자동으로 들어간다.

## 사용한 기술과 DB

| 구분 | 내용 |
|---|---|
| 백엔드 | Python 3.14, FastAPI, SQLAlchemy |
| 프론트엔드 | React 19, Vite |
| **DB** | **SQLite** (파일 경로는 환경변수 `DB_PATH`, 서버에서는 `/data/voca.db`) |
| 실행 | Docker 이미지 1개. 컨테이너가 `0.0.0.0:8080` 에서 화면과 API 를 함께 내보낸다 |

처음 실행하면 표(테이블)가 자동으로 만들어지고, 단어가 비어 있으면 `data/words/toeic_2000.csv` 를 자동으로 넣는다.

## 구현한 요구사항 ID

요구사항 원문은 교수님 제공 「소프트웨어 요건」을 따른다. 상태는 2026-11-25 기준이며, 진행 상황은 GitHub 이슈로 추적한다.

| 상태 | ID | 내용 |
|---|---|---|
| 구현 | VOCA-FR-012 | 단어를 한 장씩 보며 암기 (영단어 → 뜻 보기) |
| 구현 | VOCA-FR-041, 042, 043 | 회원가입·로그인·로그아웃, 비밀번호 해시(Argon2) 저장, 계정별 이력 |
| 구현 | VOCA-NFR-001~004 | 웹 브라우저 동작, SQLite 저장, 첫 실행 시 표 자동 생성, 비밀값은 환경변수 |
| 부분 구현 | VOCA-FR-011 | 하루 학습량(새 단어 수, 1~50)에 따른 진도. 「N일차」 표시는 아직 없음 |
| 부분 구현 | VOCA-FR-013 | 복습 시점이 된 단어가 섞여 나옴(SM-2). 「자주 틀린 단어」 가중은 난이도 계수로만 반영 |
| 부분 구현 | VOCA-FR-014 | 암기 이력(누가·언제·어느 단어·결과)을 DB 에 저장. 「몇 일차」 항목은 아직 없음 |
| 부분 구현 | VOCA-FR-031, 034 | 진도 현황(학습한 단어 수 / 전체). 통계는 DB 이력으로 계산 |
| 부분 구현 | VOCA-FR-061, 062 | 하루 학습량 설정을 계정별로 DB 에 저장. 복습 비율·시험 기본값은 아직 없음 |
| 진행 예정 | VOCA-FR-001~004 | 단어 직접 등록·수정·삭제, 검색, CSV 가져오기 (이슈 #24) |
| 진행 예정 | VOCA-FR-021~026 | 시험: 문제 수·출제 방향·형식 2가지 이상·채점·문항 이력 (이슈 #25) |
| 진행 예정 | VOCA-FR-032, 033 | 시험 성적 추이, 자주 틀리는 단어 (이슈 #26) |
| 진행 예정 | VOCA-FR-051~053 | 다른 계정 이력 보기 (도전) |
| 진행 중 | VOCA-NFR-005, VOCA-SUB-031~037 | 서버 배포 요건: `Dockerfile`, 8080 포트, UID 10001, `/data` 에만 쓰기 (이슈 #23) |

## 실행 방법

### 방법 1. Docker (서버와 같은 방식)

```bash
docker build -t smart-voca .
docker run --rm -p 8080:8080 -v smart-voca-data:/data smart-voca
```

브라우저에서 `http://localhost:8080` 으로 접속한다. 데이터는 `smart-voca-data` 볼륨의 `/data/voca.db` 에 남는다.

환경변수 (모두 선택)

| 이름 | 설명 | 기본값 |
|---|---|---|
| `DB_PATH` | SQLite 파일 경로 | 이미지: `/data/voca.db` |
| `SECRET_KEY` | 로그인 토큰 서명 비밀값. 없으면 서버가 켜질 때 무작위로 만든다(서버를 다시 켜면 로그인이 풀린다) | 무작위 |
| `LOG_DIR` | 로그 폴더 | 이미지: `/tmp/logs` |
| `AI_PROVIDER`, `PAYMENT_PROVIDER` | `fake`(가짜, 인터넷 불필요) 또는 실제 연동 | 이미지: `fake` |

### 방법 2. 내 컴퓨터에서 개발 (터미널 2개)

준비물: Python 3.14, Node.js 22 이상. PowerShell 기준.

```powershell
# 처음 한 번만
cd src\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
cd ..\frontend
npm install
cd ..\..
copy .env.example .env   # 값은 비워 둬도 된다(DB 는 data\voca.db 에 자동 생성)
```

```powershell
# 터미널 1: 서버 (http://127.0.0.1:8000). 처음 켜면 표 생성과 단어 2,000개 적재가 자동으로 된다
cd src\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 터미널 2: 화면 (브라우저에서 http://localhost:5173)
cd src\frontend
npm run dev
```

- 화면은 `http://localhost:5173` 으로 접속한다. (`127.0.0.1:5173` 은 안 열릴 수 있다)
- 서버 자동 문서: `http://localhost:5173/api/docs`

## 테스트

```powershell
cd src\backend
.\.venv\Scripts\python.exe -m pytest -v
```

테스트는 임시 폴더에 만든 SQLite 파일만 쓰므로 개발 DB 는 건드리지 않는다.

## 시연용 데모 계정

```powershell
cd src\backend
.\.venv\Scripts\python.exe ..\..\ai-agent\scripts\seed_demo.py demo
```

`demo@smartvoca.com` 계정에 6일치 학습 이력이 들어간다. 여러 번 실행해도 같은 상태로 초기화된다.

## 백업

DB 가 파일 하나(`data/voca.db`, 서버에서는 `/data/voca.db`)이므로, 서버를 끈 뒤 이 파일을 복사해 두면 백업이다.

## 문서

- `docs/` : 기획·분석·설계·운영 산출물 (개발 방법론 `docs/개발방법론.md` 기준)
- `CLAUDE.md` : AI 도구와 함께 작업하는 방식(분석 → 설계 → 구현 → 테스트), 산출물 위치, 요구사항 ID 추적 규칙
- GitHub 이슈 : 작업 단위별 진행 기록
