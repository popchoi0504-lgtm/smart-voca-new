# 운영·배포 정의서 (Operations Guide)

**파일 위치**: `ai-agent/claude/운영_261105_운영·배포 정의서(Operations Guide) v1.0.md`
**작성일**: 2026-11-05
**버전**: v1.0
**설명**: 처음 보는 사람이 문서만 보고 smart-voca 를 실행·시연하고, 데이터를 백업·복원하고, 문제가 났을 때 확인할 곳을 아는 것이 목표. (FR-SYS-04, NFR-DATA-01, NFR-SEC-03, 구현 계획서 VS-7)

---

## 1. 범위와 전제

- 이 문서는 **개발 PC 한 대에서 직접 실행**(Docker 미사용, 기획서 D-3)하는 방법을 다룬다. 인터넷 공개 배포는 범위 밖이며 7장에 필요한 조건만 적는다.
- 명령은 PowerShell 기준. 프로젝트 루트(`smart-voca_new`)에서 시작한다.
- 비밀값(DB 비밀번호, JWT 비밀값, 토스 키)은 `.env` 에만 쓰고 대화·문서·Git 에 올리지 않는다.

## 2. 준비물

| 도구 | 버전(확인된 값) | 확인 명령 |
|---|---|---|
| Python | 3.14.3 | `python --version` |
| Node.js / npm | v24 / 11 | `node --version` |
| PostgreSQL | 17 (서비스 `postgresql-x64-17` 실행 중) | `Get-Service postgresql-x64-17` |
| 토스페이먼츠 테스트 키 | 개발자센터에서 발급 | 없으면 `PAYMENT_PROVIDER=fake` 로 가짜 결제 사용 |

## 3. 처음부터 실행하기 (새 컴퓨터)

1. **패키지 설치**
   ```powershell
   cd src\backend
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   cd ..\frontend
   npm install
   cd ..\..
   ```
2. **설정 파일**: `copy .env.example .env` 후 `.env` 를 열어 값을 채운다 (키 설명은 4장).
3. **DB 와 전용 사용자 만들기** (PostgreSQL 관리자 계정으로 한 번). 비밀번호는 `.env` 의 `DATABASE_URL` 과 같게 한다.
   ```sql
   CREATE USER smart_voca_app WITH PASSWORD '<.env 와 같은 비밀번호>';
   CREATE DATABASE smart_voca OWNER smart_voca_app;
   CREATE DATABASE smart_voca_test OWNER smart_voca_app;
   ```
4. **표 만들기**: `cd src\backend` 후 `.\.venv\Scripts\python.exe -m alembic upgrade head` (표 5개 + 버전 표)
5. **단어 2,000개 넣기**: `.\.venv\Scripts\python.exe ..\..\ai-agent\scripts\seed_words.py` → "추가 2000" 이 나오면 정상. 다시 실행해도 "추가 0".
6. **(시연용) 데모 계정**: `.\.venv\Scripts\python.exe ..\..\ai-agent\scripts\seed_demo.py demo` (5장)
7. **테스트로 확인**: `.\.venv\Scripts\python.exe -m pytest -q` → 275개 통과.

## 4. 설정 키 (`.env`)

| 키 | 의미 | 비고 |
|---|---|---|
| `POSTGRES_HOST/PORT/SUPERUSER/SUPERUSER_PASSWORD` | DB 관리자 접속 | DB 를 처음 만들 때만 사용 |
| `DATABASE_URL` | 서비스용 DB 주소 | 없으면 서버가 시작할 때 바로 오류 |
| `TEST_DATABASE_URL` | 테스트용 DB 주소 | DB 이름이 `smart_voca_test` 가 아니면 테스트가 스스로 중단됨 |
| `JWT_SECRET` | 로그인 증표 서명 비밀값 | 길고 무작위로. 바꾸면 모든 로그인이 풀림 |
| `JWT_EXPIRE_DAYS` | 로그인 유지 기간(일) | 기본 7 |
| `COOKIE_SECURE` | 로그인 쿠키를 https 에서만 보냄 | 로컬 http 는 false, https 배포는 반드시 true |
| `FREE_WORD_LIMIT` | 무료 회원 단어 범위 | 기본 250 (전체 2,000 의 12.5%) |
| `PREMIUM_PRICE_KRW`, `PREMIUM_PASS_DAYS` | 이용권 가격·기간 | 4,900원 / 30일 |
| `PAYMENT_PROVIDER` | `toss`(토스 연동) 또는 `fake`(가짜 결제) | 토스 호출은 외부 통신 |
| `TOSS_CLIENT_KEY`, `TOSS_SECRET_KEY` | 토스 테스트 키 | 시크릿 키는 서버만 사용, 화면에 안 보냄 |

`.env.example` 에는 키 이름만 있고 `.env` 는 Git 에서 제외되어 있다 (`.gitignore`).

## 5. 실행·종료·시연 준비

### 5.1 실행 (터미널 2개)

```powershell
# 터미널 1: 서버 (http://127.0.0.1:8000)
cd src\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 터미널 2: 화면
cd src\frontend
npm run dev
```

- 브라우저는 **`http://localhost:5173`** 으로 접속한다 (`127.0.0.1:5173` 은 연결 안 됨: 화면 서버가 IPv6 로 대기).
- 서버 상태: `http://localhost:5173/api/health` → `{"status":"ok","db":"ok"}`. 자동 문서: `/api/docs`.
- 종료: 각 터미널에서 `Ctrl + C`. 서버 코드를 고치면 서버를 껐다 다시 켠다(`--reload` 미사용).

### 5.2 데모 계정 (시연용)

| 항목 | 값 |
|---|---|
| 이메일 | `demo@smartvoca.com` |
| 비밀번호 | 기본 `Demo-1234-voca` (환경변수 `DEMO_PASSWORD` 로 바꿀 수 있음) |
| 상태 | 무료 회원, 단어 30개를 6일에 걸쳐 학습한 이력(연속 6일, 익숙함 5·학습 중 25), 오늘 복습 8개 |

- 만들기·초기화: `.\.venv\Scripts\python.exe ..\..\ai-agent\scripts\seed_demo.py demo` (여러 번 실행해도 같은 결과. 데모 계정의 이력만 지우고 다시 채움)
- 이용권이 있는 상태로: `seed_demo.py demo --premium-days 30`
- 시연 중 오늘 새 단어를 배우면 연속 학습일이 6 → 7일이 된다. 시연 후 초기화하려면 위 명령을 다시 실행.
- 다른 사람 계정 데이터는 건드리지 않는다. 이 계정은 **개발 DB 안의 시연용 데이터**이며 실제 개인정보가 아니다.

### 5.3 시연 시나리오 (약 5분, BDD)

| # | Given / When / Then | 확인 포인트 |
|---|---|---|
| 1 | Given 서버·화면이 켜져 있다 When `localhost:5173` 접속 Then 로그인 화면 | 로그인 안 하고 `/progress` 접속 시 로그인으로 이동 |
| 2 | When 데모 계정으로 로그인 Then "오늘 할 것": 복습 8개, 새 단어 10개 | 클릭 3번 이내에 학습 시작(NFR-USE-01) |
| 3 | When 새 단어 배우기 → 뜻 보기 → 알았음/애매함 Then 다음 카드, 끝나면 완료 문구 | 순서는 단어 순위(토익 단어 먼저) |
| 4 | When 복습 퀴즈에서 힌트 1→2→3단계 사용 Then 단계별 도움, 3단계는 정답 공개 | 힌트를 쓸수록 다음 복습이 앞당겨짐 |
| 5 | When 학습 기록 Then 연속 학습일, 배운 단어 N/2000, 숙련도 | 오늘 학습하면 연속일 증가 |
| 6 | When 프리미엄 → 이용권 구매(토스 테스트 카드) Then 이용권 만료일 표시, 결제 내역 | 토스 외부 호출이 있다. 실패 대비로 `PAYMENT_PROVIDER=fake` 준비 |
| 7 | When 무료 250개를 모두 배운 계정 Then "프리미엄이 필요해요" 안내 | 무료 12.5% / 프리미엄 100% |

## 6. 백업·복원 (NFR-DATA-01)

대상은 DB 전체(회원, 학습 기록, 결제 내역, 단어)이다. 도구: `ai-agent/scripts/db_backup.py` (PostgreSQL 의 `pg_dump`/`pg_restore` 사용).

```powershell
cd src\backend
# 백업: 프로젝트 루트의 backups\smart_voca_yymmdd_hhmmss.dump 생성
.\.venv\Scripts\python.exe ..\..\ai-agent\scripts\db_backup.py backup

# 복원(테스트 DB 로 연습): 개발 DB 를 건드리지 않음
.\.venv\Scripts\python.exe ..\..\ai-agent\scripts\db_backup.py restore --file ..\..\backups\파일.dump --target test

# 복원(개발 DB 덮어쓰기): 현재 내용이 지워지므로 --yes 필요. 복원 전에 서버를 끄고, 복원 직전 백업을 한 번 더 뜬다
.\.venv\Scripts\python.exe ..\..\ai-agent\scripts\db_backup.py restore --file ..\..\backups\파일.dump --yes
```

- 백업 파일에는 회원 이메일과 비밀번호 해시가 들어 있어 `backups/` 는 Git 에서 제외했다. 외부에 공유하지 않는다.
- **복원 연습 결과(2026-11-05)**: 개발 DB 백업(138,939 bytes) → 테스트 DB 복원 후 행 수 일치 (users 2, words 2000, user_words 53, review_logs 76, payments 22). `--yes` 없이 개발 DB 복원을 시도하면 거부됨을 확인.
- 단어만 다시 만들 때는 백업이 아니라 `seed_words.py` 를 쓴다(CSV 가 원본, 재실행 안전).
- 한계: 자동 예약 백업은 없다(수동). 운영 단계가 되면 Windows 작업 스케줄러로 `backup` 을 매일 실행하는 것을 권한다.

## 7. 로그와 문제 확인

| 확인할 것 | 위치·방법 |
|---|---|
| 서버 로그 | 콘솔 + `logs/app.log` (1MB 마다 새 파일, 이전 3개 보관). 요청 줄: `메서드 경로 -> 상태 (ms)` |
| 로그에 남는 것 | 회원 번호(user_id), 주문 번호, 결과 코드. **남기지 않는 것**: 비밀번호, 로그인 토큰, 결제키, 비밀 키, 이메일 원문(마스킹 `a***@gmail.com`) |
| 자동 검증 | `tests/test_log_safety.py`: 가입·로그인·결제·서버 오류를 일으킨 뒤 로그에 비밀값이 있는지 검사. 일부러 비밀번호/결제키/이메일 원문을 로그에 넣어 보면 테스트가 실패함을 확인함 |
| 사용자에게 보이는 오류 | 모든 오류가 `{"error": {"code", "message"}}` 한 모양. 예상 못 한 오류(500)는 일반 문장만, 원인은 로그에만 |

| 증상 | 원인·조치 |
|---|---|
| `127.0.0.1:5173` 연결 안 됨 | `localhost:5173` 로 접속 |
| 화면에 "서버에 연결할 수 없어요" | 서버(8000) 꺼짐 → 터미널 1 확인. `/api/health` 로 DB 상태 확인 |
| 서버 시작 직후 오류 | `.env` 의 `DATABASE_URL`/`JWT_SECRET` 누락 여부 |
| `health` 가 503 | PostgreSQL 서비스 꺼짐 → 서비스 시작 |
| 코드를 고쳤는데 그대로 | 서버를 껐다 다시 켠다 |
| 결제창이 안 뜸 | 토스 키 확인. 시연 중 급하면 `PAYMENT_PROVIDER=fake` 로 바꾸고 서버 재시작 |
| 테스트가 "중단" | `TEST_DATABASE_URL` 의 DB 이름이 `smart_voca_test` 인지 확인 |

## 8. 시스템명 반영 방법

시스템명은 아직 미정(`smart-voca` 는 작업 이름)이다. 확정되면 아래 **4곳**만 바꾼다: `src/frontend/index.html` 의 `<title>`, `src/frontend/src/pages/LoginPage.jsx` 의 환영 문구, `src/frontend/src/pages/StatusPage.jsx` 의 제목, `src/backend/app/main.py` 의 API 문서 제목. 데모 이메일 도메인(`smartvoca.com`)은 이름과 무관한 시연용 값이다.

## 9. 공개 배포 시 필요한 조건 (범위 밖, 참고)

| 항목 | 이유 |
|---|---|
| `COOKIE_SECURE=true` + https | 로그인 쿠키가 평문으로 가지 않게 |
| 토스 라이브 키 + 가맹 계약 | 테스트 키로는 실결제 불가 |
| `JWT_SECRET` 새로 생성, `.env` 별도 보관 | 개발용 값 재사용 금지 |
| DB 자동 백업, 로그 보관 정책 | 6, 7장은 수동 기준 |
| 화면은 `npm run build` 결과(`dist`)를 웹 서버로 제공, `/api` 는 서버로 전달 | 현재의 Vite 개발 서버는 개발용 |
| 모바일 화면, 비밀번호 재설정, 이메일 인증 | 현 범위 밖(NFR-USE-02) |

## 10. 요구사항 추적

| 요구사항 | 충족 근거 |
|---|---|
| FR-SYS-04 실행 문서 | 3~5장 |
| FR-SYS-05 핵심 로직 자동 테스트 | SM-2, 힌트, 결제 검증, 인증 등 275개 (`pytest`) |
| NFR-SEC-01~03 | Argon2·JWT·검증·ORM, `.env` 분리, 로그 검사 테스트 |
| NFR-DATA-01 | 6장 (복원 연습 결과 포함) |
| NFR-MNT-01 | 모든 소스 파일 헤더 |
| NFR-LIC-01 | `data/words/README.md`, 화면 하단 출처 표기 |
