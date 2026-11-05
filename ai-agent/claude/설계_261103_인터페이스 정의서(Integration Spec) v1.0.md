# 인터페이스 정의서 (Integration Spec)

**파일 위치**: `ai-agent/claude/설계_261103_인터페이스 정의서(Integration Spec) v1.0.md`
**작성일**: 2026-11-03
**버전**: v1.0 (초안)
**설명**: React 화면과 FastAPI 서버가 주고받는 API 17개의 요청·응답 모양, 공통 규칙, 오류 코드를 정의한 문서

> 입력 문서: 아키텍처 설계서 v1.0(4장 API 개요), 데이터 설계서 v1.0, 요구사항 명세서 v1.0.
> 구현은 이 문서의 모양을 따른다. 모양을 바꿔야 하면 코드보다 **먼저 이 문서를 수정**한다. (방법론 §3)
> `[설계 확정]` 은 구현하며 값을 조정할 항목, `[구현 시 확인]` 은 아직 확인하지 못한 외부 사실이다.

---

## 1. 이 문서를 읽는 법 (대표 학습용)

| 용어 | 쉬운 설명 |
|---|---|
| API | 화면이 서버에게 "이거 해줘"라고 요청하는 약속된 창구 |
| 요청(Request) | 화면 → 서버. "무엇을 줄게 / 무엇을 원해" |
| 응답(Response) | 서버 → 화면. 결과와 데이터 |
| JSON | 데이터를 `{"이름": 값}` 모양으로 적는 글자 형식 |
| HTTP 상태 코드 | 결과를 숫자로 알리는 표준. 200 성공, 401 로그인 필요, 404 없음, 422 입력 오류 등 |
| 쿠키 | 브라우저가 서버 요청마다 자동으로 같이 보내는 작은 데이터. 우리는 로그인 증표를 여기에 담는다 |

## 2. 공통 규칙

| 항목 | 규칙 |
|---|---|
| 주소 | 모든 API 는 `/api` 로 시작 (예: `/api/auth/login`) |
| 형식 | 요청·응답 본문은 JSON(UTF-8). 필드 이름은 `snake_case`. 요청의 `Content-Type` 은 `application/json` 이어야 함 |
| 날짜 | 날짜는 `"2026-11-03"`, 시각은 `"2026-11-03T14:05:00+09:00"` (한국 시간대 포함) |
| "오늘" | 서버가 Asia/Seoul 기준으로 계산 (데이터 설계서 DD-8). 화면은 날짜를 만들어 보내지 않는다 |
| 로그인 | 로그인하면 서버가 쿠키 `access_token` 을 내려주고, 이후 요청에 브라우저가 자동으로 붙인다. **인증 필요** 표시된 API 는 쿠키가 없거나 만료되면 401 |
| 쿠키 속성 | `HttpOnly`(화면 스크립트가 못 읽음), `SameSite=Lax`, `Path=/`, 유효기간 7일 `[설계 확정]`. 로컬 시연은 http 라서 `Secure` 를 쓰지 않는다. **https 로 배포할 때는 반드시 `Secure` 를 켜야 한다** |
| 토큰 내용 | JWT 의 `sub`(회원 id), `iat`, `exp` 만 담는다. 이메일 등 개인정보는 담지 않는다 |
| 오류 모양 | 아래 3장 참고. 모든 오류가 같은 모양 |
| 목록 | 이번 범위에서는 페이지 번호 방식은 쓰지 않고 `limit` 만 사용 |

## 3. 오류 응답

```json
{ "error": { "code": "EMAIL_ALREADY_EXISTS", "message": "이미 가입된 이메일입니다." } }
```

입력 검증 오류(422)만 어느 칸이 문제인지 `fields` 를 추가로 담는다.

```json
{ "error": { "code": "VALIDATION_ERROR", "message": "입력값을 확인해 주세요.",
             "fields": [ { "field": "password", "message": "8자 이상이어야 합니다." } ] } }
```

### 3.1 오류 코드 목록

| 코드 | HTTP | 언제 | 화면이 할 일 |
|---|---|---|---|
| `VALIDATION_ERROR` | 422 | 입력 형식·길이 위반 | 칸별 메시지 표시 |
| `NOT_AUTHENTICATED` | 401 | 로그인 안 함, 쿠키 만료 | 로그인 화면으로 이동 |
| `INVALID_CREDENTIALS` | 401 | 이메일 또는 비밀번호 불일치 (어느 쪽인지 알려주지 않음) | 안내 문구 표시 |
| `EMAIL_ALREADY_EXISTS` | 409 | 이미 가입된 이메일 | 안내 문구 표시 |
| `WORD_NOT_FOUND` | 404 | 존재하지 않는 단어 id | 오류 안내 |
| `WORD_ALREADY_LEARNED` | 409 | 이미 학습한 단어를 새 단어로 평가 시도 (중복 제출 포함) | 성공처럼 다음 카드로 |
| `WORD_NOT_LEARNED` | 409 | 아직 학습하지 않은 단어로 퀴즈 시도 | 오류 안내 |
| `PLAN_LIMIT_EXCEEDED` | 403 | 무료 요금제 범위(빈도 순위 250 초과) 밖의 새 단어 | 프리미엄 안내 화면 |
| `ORDER_NOT_FOUND` | 404 | 없는 주문 또는 남의 주문 (남의 주문임을 알려주지 않음) | 오류 안내 |
| `AMOUNT_MISMATCH` | 400 | 확인 요청 금액이 서버가 정한 금액과 다름 | 오류 안내, 결제 처리 안 함 |
| `PAYMENT_FAILED` | 402 | 결제사가 승인을 거절 | 실패 사유 표시, 다시 시도 |
| `PAYMENT_PROVIDER_ERROR` | 502 | 결제사와 통신 실패 | 잠시 후 다시 시도 안내 |
| `NOT_FOUND` | 404 | 없는 주소 | - |
| `METHOD_NOT_ALLOWED` | 405 | 허용되지 않는 요청 방식 (예: 조회 전용 주소에 POST). VS-0 구현 중 추가 | - |
| `INTERNAL_ERROR` | 500 | 서버 내부 오류 (상세는 로그에만) | "문제가 생겼어요" 안내 |

## 4. API 상세

각 API 는 `인증 필요` 여부, 요청, 응답, 오류, 관련 FR 순으로 적는다.

### 4.1 공통 객체: `user`

| 필드 | 타입 | 설명 |
|---|---|---|
| id | 정수 | 회원 id |
| email | 문자열 | 소문자로 정리된 이메일 |
| daily_new_limit | 정수 | 하루 새 단어 수 설정 |
| is_premium | 불리언 | 지금 이용권이 유효한가 (`premium_until` 이 지금보다 미래) |
| premium_until | 시각 또는 null | 이용권 만료 시각 |

### 4.2 인증 (AUTH)

**POST `/api/auth/signup`** — 인증 불필요 · FR-AUTH-01, 07
| 요청 필드 | 규칙 |
|---|---|
| email | 이메일 형식, 최대 254자. 서버가 소문자·공백 정리 |
| password | 8~64자, 영문·숫자 각 1자 이상 `[설계 확정]` |

- 성공: **201** `{ "user": { ... } }` + 로그인 쿠키 발급 (가입 후 바로 로그인 상태. IF-3)
- 오류: 409 `EMAIL_ALREADY_EXISTS`, 422 `VALIDATION_ERROR`

**POST `/api/auth/login`** — 인증 불필요 · FR-AUTH-02, 05
- 요청: `{ "email": "...", "password": "..." }`
- 성공: **200** `{ "user": { ... } }` + 쿠키 발급
- 오류: 401 `INVALID_CREDENTIALS` (이메일 없음과 비밀번호 틀림을 같은 메시지로), 422

**POST `/api/auth/logout`** — 인증 불필요 · FR-AUTH-03
- 요청: 본문 없음. 성공: **204** + 쿠키 삭제. 쿠키가 이미 없어도 204

**GET `/api/auth/me`** — 인증 필요 · FR-AUTH-06, FR-SUB-05
- 성공: **200** `{ "user": { ... } }`. 오류: 401

**PATCH `/api/me/settings`** — 인증 필요 · FR-STUDY-04
- 요청: `{ "daily_new_limit": 15 }` (정수 1~50 `[설계 확정]`)
- 성공: **200** `{ "user": { ... } }`. 오류: 422

### 4.3 학습 (STUDY)

**GET `/api/study/today`** — 인증 필요 · FR-STUDY-01
```json
{ "today": "2026-11-03",
  "review_due_count": 12,
  "new_target_count": 6,
  "new_learned_today": 4,
  "daily_new_limit": 10,
  "plan_word_limit": 250,
  "new_locked_by_plan": false }
```
| 필드 | 뜻 |
|---|---|
| review_due_count | `next_review_date <= 오늘` 인 복습 대상 수 |
| new_target_count | 오늘 더 배울 새 단어 수 = `min(daily_new_limit - new_learned_today, 요금제 범위 안의 남은 새 단어)` (0 이상) |
| plan_word_limit | 요금제가 허용하는 단어 수(무료 250, 프리미엄 500) |
| new_locked_by_plan | 새 단어가 남아 있지만 요금제 때문에 막힌 상태인가 (화면이 프리미엄 안내를 띄우는 근거) |

**GET `/api/study/new?limit=10`** — 인증 필요 · FR-STUDY-02, 06, FR-WORD-06
- `limit`: 1~10, 기본 10. 반환 개수는 `min(limit, new_target_count)`
- 새 단어는 `frequency_rank` 가 낮은(자주 나오는) 순서이며, 요금제 범위 안에서만 반환
```json
{ "items": [ { "word_id": 7, "headword": "negotiate", "part_of_speech": "v.",
               "meaning_ko": "협상하다", "example_en": "They negotiate the contract.",
               "example_ko": "그들은 계약을 협상한다.", "frequency_rank": 7 } ] }
```
- 학습 카드는 공부용이므로 영단어(headword)를 보낸다. (퀴즈와 다름, 4.4)

**POST `/api/study/flashcard`** — 인증 필요 · FR-STUDY-03, FR-SRS-02
- 요청: `{ "word_id": 7, "rating": "know" }` — `rating` ∈ `dont_know` | `unsure` | `know`
- 점수 변환(제안) `[설계 확정]`: `dont_know`→1, `unsure`→3, `know`→5
- 동작: `user_words` 행 생성(SM-2 첫 계산) + `review_logs` 추가 — 한 트랜잭션
```json
{ "word_id": 7, "sm2_quality": 5, "interval_days": 1, "next_review_date": "2026-11-04" }
```
- 오류: 404 `WORD_NOT_FOUND`, 409 `WORD_ALREADY_LEARNED`, 403 `PLAN_LIMIT_EXCEEDED`, 422
- 새 단어 하루 한도(`daily_new_limit`)는 **목표치**라서 이 API 는 막지 않는다. 한도는 `/study/new` 가 돌려주는 개수로만 조절한다. 요금제 범위는 막는다.

### 4.4 퀴즈와 힌트 (QUIZ, HINT)

**GET `/api/quiz/queue?limit=10`** — 인증 필요 · FR-QUIZ-01, FR-SRS-04~05
- 복습 대상 중 **오래 밀린 순**으로 최대 `limit`(1~10, 기본 10)개. 이미 배운 단어는 이용권이 만료돼도 복습할 수 있다(IF-7)
```json
{ "items": [ { "word_id": 7, "part_of_speech": "v.", "meaning_ko": "협상하다",
               "example_masked": "They ______ the contract.", "letter_count": 9 } ],
  "remaining_due_count": 12 }
```
- **정답 영단어는 포함하지 않는다.** (아키텍처 AD-7) `example_masked` 는 예문에서 영단어를 `____` 로 바꾼 것이며, 예문에 영단어가 그대로 들어 있지 않은 단어는 `example_masked` 를 null 로 보낸다. 이를 막기 위해 시드 스크립트는 "예문에 영단어가 그대로 들어 있는지" 검사한다 (요구사항 FR-WORD-05 보강 필요).
- `letter_count` 는 공백·하이픈을 뺀 글자 수.

**POST `/api/quiz/{word_id}/hint`** — 인증 필요 · FR-HINT-01~05
- 요청: `{ "level": 1 }` — 1, 2, 3 중 하나
```json
{ "level": 1, "skipped": false, "scrambled": "tgeoianet" }
{ "level": 2, "masked": ["n","_","_","_","t","_","_","_","e"] }
{ "level": 3, "answer": "negotiate" }
```
| 단계 | 응답 | 규칙 |
|---|---|---|
| 1 철자 섞기 | `scrambled` | 글자를 섞은 문자열. 원래 단어와 같으면 다시 섞음. **3글자 이하이거나 모든 글자가 같은 단어는** `skipped: true`, `scrambled: null` (화면이 바로 2단계로 안내). 공백·하이픈은 제자리 고정 |
| 2 빈칸 | `masked` | 글자 배열. 가려진 칸은 `"_"`. 첫 글자는 항상 공개, 공개 개수는 길이의 약 40% `[설계 확정]`. 공백·하이픈은 그대로 표시 |
| 3 정답 | `answer` | 정답 영단어 |

- **같은 날 같은 단어에 대한 힌트는 항상 같은 결과**를 돌려준다(회원 id + 단어 id + 날짜로 정해지는 고정된 섞기). 이렇게 하지 않으면 2단계를 반복 요청해서 공개 위치를 계속 바꿔 정답 전체를 알아낼 수 있다. (IF-5)
- 이 API 는 아무것도 저장하지 않는다. 사용한 최고 단계는 아래 `answer` 제출 때 화면이 알려준다.
- 오류: 404 `WORD_NOT_FOUND`, 409 `WORD_NOT_LEARNED`, 422 (level 범위 밖)

**POST `/api/quiz/{word_id}/answer`** — 인증 필요 · FR-QUIZ-02~03, FR-HINT-03~04, FR-SRS-02~03
- 요청: `{ "answer": "negotiate", "max_hint_level": 2 }`
| 필드 | 규칙 |
|---|---|
| answer | 문자열. 대소문자·앞뒤 공백 무시하고 비교. `max_hint_level` 이 3이면 null 가능 |
| max_hint_level | 0~3. 이 문제에서 연 가장 높은 힌트 단계 |

```json
{ "result": "correct", "recorded": true, "practice": false,
  "sm2_quality": 3, "interval_days": 6, "next_review_date": "2026-11-09",
  "correct_answer": "negotiate", "remaining_due_count": 11 }
```
| 응답 필드 | 뜻 |
|---|---|
| result | `correct` / `wrong` / `revealed` (`max_hint_level` 이 3이면 입력과 상관없이 `revealed`) |
| recorded | 이 제출이 기록(`review_logs`)과 SM-2 계산에 반영됐는가 |
| practice | 연습 제출인가 (아래 규칙). 연습이면 `sm2_quality` 등은 null |
| correct_answer | 정답일 때와 `revealed` 일 때만 값이 있다. **오답이면 null** (계속 시도하거나 힌트를 쓸 수 있게) |

**점수 변환(제안) `[설계 확정]`** (요구사항 FR-SRS-03)
| 결과 | `sm2_quality` |
|---|---|
| 정답, 힌트 없음 | 5 |
| 정답, 1단계까지 사용 | 4 |
| 정답, 2단계까지 사용 | 3 |
| 오답 | 1 |
| 정답 확인(3단계, `revealed`) | 2 — 오답보다 덜 감점하되 복습은 앞당김. D-5 후속 |

**연습 규칙 (IF-4)**: 한 단어는 **하루에 한 번만** SM-2 에 반영한다. 다음 중 하나면 제출은 `practice: true`, `recorded: false` 로 처리하고 결과 판정만 돌려준다.
- 오늘 이미 이 단어의 퀴즈 결과가 기록되어 있다 (오답 후 다시 시도하는 경우 포함)
- 이 단어의 `next_review_date` 가 오늘보다 미래다 (복습 대상이 아닌데 직접 요청한 경우)

이 규칙으로 (1) 오답 후 재시도가 가능하고(FR-QUIZ-03), (2) 같은 요청을 두 번 보내도 두 번 계산되지 않으며, (3) 복습 시점이 아닌 단어를 반복해서 풀어 간격을 부풀리는 일을 막는다. 한계: 첫 오답이 그날 기록으로 남는다. 한 글자 오타 허용은 이번 범위에서 제외 `[설계 확정]`.

- 오류: 404 `WORD_NOT_FOUND`, 409 `WORD_NOT_LEARNED`, 422 (`answer` 가 null 인데 `max_hint_level` 이 3 미만 등)
- 한계(알려진 위험): 힌트 3단계를 요청해 정답을 본 뒤 `max_hint_level` 을 0으로 속여 제출할 수 있다. 이는 **본인의 복습 기록만 부정확해지는** 일이라 이번 범위에서는 허용한다.

### 4.5 학습 기록 (PROG)

**GET `/api/progress/summary`** — 인증 필요 · FR-PROG-02~05
```json
{ "today": { "date": "2026-11-03", "reviewed_count": 18, "new_learned_count": 4 },
  "total_learned_count": 37, "total_word_count": 500,
  "current_streak_days": 5,
  "mastery": { "new_count": 463, "learning_count": 30, "familiar_count": 7 } }
```
| 필드 | 계산 |
|---|---|
| reviewed_count | 오늘 `review_logs` 중 서로 다른 단어 수 (새 단어 평가 포함) |
| new_learned_count | 오늘 `review_logs` 중 `flashcard`(=처음 배움) 기록의 서로 다른 단어 수. 구현 중 정의 `[구현 확정]` |
| current_streak_days | 오늘(또는 오늘 아직 학습 전이면 어제)부터 거슬러 올라가며 **하루도 빠짐없이** 학습한 날 수. 오늘 아직 안 했어도 어제까지 이어졌으면 끊기지 않은 것으로 본다 |
| mastery | 새 단어 = 전체 단어 수(현재 2,000) - 학습한 수 / 학습 중 = `interval_days` 21 미만 / 익숙함 = 21 이상 (데이터 설계서 4.3, `[설계 확정]`) |

### 4.6 구독과 결제 (SUB)

**GET `/api/subscription`** — 인증 필요 · FR-SUB-01, 05
```json
{ "plans": [
    { "code": "free", "name": "무료", "word_limit": 250, "price_krw": 0, "pass_days": null },
    { "code": "premium", "name": "프리미엄", "word_limit": 500, "price_krw": 4900, "pass_days": 30 } ],
  "current": { "plan": "free", "premium_until": null } }
```
- `price_krw` 4,900원은 Claude 가 제안한 값을 대표가 그대로 채택했다(2026-11-03). **시장 조사에 근거한 가격은 아니다.** 참고로 조사한 말해보카 표기는 1개월 19,500원(최신 여부 미확인)이다. 가격은 서버 설정에서 바꿀 수 있다. (요구사항 9장 #3)

**POST `/api/payments/orders`** — 인증 필요 · FR-SUB-02, 06
- 요청: `{ "product": "premium_30d" }` (지금은 이 상품 하나)
```json
{ "order_id": "svc-3f9a1c0e5b2d4e78", "order_name": "smart-voca 프리미엄 30일",
  "amount": 4900, "client_key": "test_gck_...", "customer_key": "u_9c1e...", "provider": "toss" }
```
- `provider`(구현 때 추가, 2026-11-05): `toss` 또는 `fake`. 화면이 결제위젯을 띄울지 가짜 결제 버튼을 보여 줄지 정한다. `fake` 일 때 `client_key` 는 `"fake"`.
- 동작: `payments` 에 `pending` 행 생성. **금액은 서버가 정한다** (요청에 금액이 있어도 무시)
- `client_key` 는 결제위젯을 띄우는 **공개 키**(서버 시크릿 키와 다름). `customer_key` 는 회원마다 고유한 값으로, 회원 id 에서 서버 비밀 값으로 계산해 만든다(추측 불가). 추가 저장은 하지 않는다.
- 주문번호 규칙: 서버가 `svc-` + 무작위 16자리(영문 소문자·숫자)로 생성. 결제사의 주문번호 규칙(길이·허용 문자)은 구현 때 확인 `[구현 시 확인]`

**POST `/api/payments/confirm`** — 인증 필요 · FR-SUB-03, 06
- 요청: `{ "payment_key": "...", "order_id": "svc-...", "amount": 4900 }` (결제위젯 성공 후 주소에 붙어 오는 값)
- 서버 동작 순서: ① 내 주문인지 확인 → ② 이미 `paid` 면 **같은 결과를 다시 돌려줌(중복 부여 안 함, IF-6)** → ③ 요청 금액과 서버가 정한 금액 비교 → ④ 결제사 승인 요청 → ⑤ 한 트랜잭션으로 `paid` 변경 + 이용권 연장
```json
{ "status": "paid", "already_processed": false,
  "premium_until": "2026-12-03T14:07:11+09:00",
  "payment": { "order_id": "svc-3f9a1c0e5b2d4e78", "amount": 4900, "approved_at": "2026-11-03T14:07:11+09:00" } }
```
- 이용권 연장: `max(지금, 현재 만료 시각) + pass_days일`. 이미 이용권이 있으면 남은 기간 뒤에 이어 붙는다. (데이터 설계서 DD-7)
- 오류: 404 `ORDER_NOT_FOUND`, 400 `AMOUNT_MISMATCH`, 402 `PAYMENT_FAILED`(실패 시 `payments.status=failed`, `failure_code` 저장), 502 `PAYMENT_PROVIDER_ERROR`(상태는 `pending` 유지, 다시 확인 요청 가능)
- 결제사 승인 요청의 주소·인증 방식·응답 모양은 구현 때 공식 문서로 확인한다. `[구현 시 확인]`

**GET `/api/payments?limit=20`** — 인증 필요 · FR-SUB-04
```json
{ "items": [ { "order_id": "svc-3f9a...", "amount": 4900, "status": "paid", "pass_days": 30,
               "requested_at": "2026-11-03T14:06:40+09:00", "approved_at": "2026-11-03T14:07:11+09:00" } ] }
```
- 최신순, `limit` 1~50, 기본 20. 내 결제만 보인다.

### 4.7 시스템 (SYS)

**GET `/api/health`** — 인증 불필요 · FR-SYS-01
- 성공: **200** `{ "status": "ok", "db": "ok" }`
- DB 연결 실패: **503** `{ "status": "degraded", "db": "error" }` (이 API 만 일반 오류 모양과 다름)

## 5. 화면 경로와 API 연결 (참고)

| 화면 경로 | 사용하는 API |
|---|---|
| `/login`, `/signup` | auth/login, auth/signup |
| `/` (오늘 할 것) | auth/me, study/today |
| `/learn` (플래시카드) | study/new, study/flashcard |
| `/quiz` | quiz/queue, quiz/{id}/hint, quiz/{id}/answer |
| `/progress` | progress/summary |
| `/subscribe` | subscription, payments/orders |
| `/payment/success`, `/payment/fail` | payments/confirm |
| `/settings` | me/settings |

## 6. 설계 결정 기록 (ADR 성격)

| ID | 결정 | 배경·대안 | 결정 근거 |
|---|---|---|---|
| IF-1 | 모든 API 는 `/api` 아래 JSON, 필드는 `snake_case` | 대안: camelCase | 파이썬 서버와 DB 컬럼 이름이 같아 변환이 필요 없어 실수가 적음 |
| IF-2 | 오류 모양을 통일하고 코드 목록을 둔다 | 대안: 상황마다 제각각 | 화면이 `code` 로 일관되게 처리 가능. 서버 내부 정보 노출 방지 (FR-SYS-01) |
| IF-3 | 회원가입 직후 자동 로그인 | 대안: 가입 후 로그인 화면 이동 | 클릭 수를 줄임 (NFR-USE-01). 단점: 가입 API 가 이메일 중복 여부를 알려줌(허용, 무차별 확인 방어는 범위 밖) |
| IF-4 | 한 단어는 하루 한 번만 SM-2 반영, 나머지는 연습 | 대안: 제출마다 반영 / 오답 시 반영 보류 | 재시도(FR-QUIZ-03)를 허용하면서 중복 계산·간격 부풀리기를 막고, 새 표 없이 `review_logs` 만으로 판단 가능 |
| IF-5 | 힌트는 같은 날 같은 결과(결정적) | 대안: 요청마다 새 무작위 | 반복 요청으로 정답을 알아내는 것을 막음 |
| IF-6 | 결제 확인 재요청은 같은 결과를 돌려줌(멱등) | 대안: 두 번째는 오류 | 새로고침·중복 클릭에도 이용권이 두 번 늘어나지 않고 화면은 안전하게 성공으로 처리 가능 (FR-SUB-06) |
| IF-7 | 이용권이 만료돼도 이미 배운 단어는 복습 가능, 새 단어만 요금제 범위로 제한 | 대안: 만료 시 학습 전체 차단 | 배운 것을 잃게 하면 사용 경험이 나쁘고 서비스 신뢰를 해침. 유료 가치는 새 범위(250개 초과)와 통계에 둠 |
| IF-8 | 오답 시 정답을 알려주지 않음 | 대안: 오답 시 정답 공개 | 재시도와 단계 힌트 설계(기획 5.4)를 지키기 위해. 정답을 보려면 3단계 확인을 거침 |

## 7. 다른 문서에 반영할 사항

| 문서 | 반영 내용 |
|---|---|
| 요구사항 명세서 (v1.1 예정) | FR-WORD-05 에 "예문에 영단어가 그대로 들어 있는지 검사" 추가, FR-QUIZ-03 에 연습 규칙(IF-4) 참조 추가, 점수 변환표(FR-SRS-03) 확정 값 반영 |
| 데이터 설계서 | 변경 없음. IF-4 는 기존 `review_logs`, `user_words` 로 구현 가능 |
| 구현 계획서 | 이 문서의 API 단위로 세로 방식 순서를 정함 |

## 8. 발표 예상 질문과 답변

1. **API 를 왜 문서로 먼저 정했나요?**
   화면과 서버를 한 사람이 만들더라도 "주고받는 모양"이 흔들리면 오류가 나서 시간이 낭비됩니다. 먼저 약속을 정하고 구현하면 어디서 틀렸는지 바로 찾을 수 있습니다.
2. **퀴즈 정답을 반복 요청으로 알아낼 수는 없나요?**
   힌트를 같은 날 같은 결과로 고정해서, 반복 요청해도 새로운 글자가 공개되지 않습니다. 정답은 3단계 확인 때만 나가고 그 경우 정답 확인으로 따로 기록됩니다.
3. **결제 확인 버튼을 두 번 누르면 이용권이 두 배가 되나요?**
   아닙니다. 같은 주문번호는 한 번만 처리하고, 두 번째 요청에는 같은 결과를 돌려줍니다.
4. **오답을 내면 바로 복습 간격이 줄어드나요? 다시 시도하면 어떻게 되나요?**
   첫 제출이 그날의 결과로 기록되고, 이후 다시 시도는 연습으로 처리해 기록을 바꾸지 않습니다. 한 번의 실수가 여러 번 반영되는 것을 막기 위한 규칙입니다.
5. **한계는 무엇인가요?**
   힌트를 본 뒤 단계를 0으로 속여 제출하면 본인의 복습 기록이 부정확해집니다. 본인에게만 영향이라 이번 범위에서는 허용했고, 확장 단계에서 서버에 힌트 사용을 기록하는 방식으로 막을 수 있습니다.

## 9. 미결 사항

| # | 항목 | 상태 |
|---|---|---|
| 1 | 비밀번호 규칙(8~64자, 영문·숫자 포함) | `[설계 확정]` |
| 2 | 힌트 공개 비율 40%, 만료 7일, 설정 범위 1~50 | `[설계 확정]` |
| 3 | 플래시카드·퀴즈 점수 변환값 | `[설계 확정]` |
| 4 | 가격 4,900원 | 확정 (11-03), 근거 약함. 설정으로 변경 가능 |
| 5 | 결제사 승인 API 상세, 주문번호 규칙 | `[구현 시 확인]` |
| 6 | 오타 허용(한 글자 차이) | 이번 범위 제외 |

## 10. 다음 산출물

1. 구현 계획서: 위 API 를 세로 방식 기능 순서로 묶어 하루 단위 계획과 환경 준비 정리
2. 요구사항 명세서 v1.1 반영
3. ADR 요약 (발표용)
