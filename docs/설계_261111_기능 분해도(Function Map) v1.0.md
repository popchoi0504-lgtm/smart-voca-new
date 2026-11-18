# 기능 분해도 (Function Map)

**파일 위치**: `docs/설계_261111_기능 분해도(Function Map) v1.0.md`
**작성일**: 2026-11-11
**버전**: v1.0
**설명**: smart-voca 의 모든 기능을 영역 → 기능 → 원자 기능(더 쪼갤 수 없는 단위) 3단계로 나누고, 각 원자 기능이 어느 요구사항·API·화면과 이어지는지 한눈에 보이게 정리한다.

---

## 1. 이 문서의 목적과 읽는 법

- **방법론 2.3절의 "기능 분해도"**: 시스템 기능을 원자 단위로 계층 분해한다. "원자 기능"은 사용자가 한 번에 하나씩 확인할 수 있는 가장 작은 기능이다.
- 요구사항 명세서(무엇을 해야 하나)와 인터페이스 정의서(어떻게 주고받나) 사이를 이어 주는 **목차 겸 연결표** 역할을 한다. 팀원이 "이 기능은 어디서 만들었지?"를 찾을 때 쓴다.
- **작성 순서 예외 기록**: 방법론 2.3절은 프로세스 설계서를 가장 먼저 쓰라고 정한다. 이 프로젝트는 구현을 먼저 하고 설계 문서를 나중에 역정리하는 중이라, 이 문서를 먼저 썼다. 프로세스 설계서는 바로 이어서 작성한다.
- 기준 시점: 2026-11-11 코드. 구현 완료된 기능만 적는다. 구현하지 않은 것은 7장에 따로 모았다.
- FR-PROFILE-xx 번호는 요구사항 명세서 v1.0 에는 없고 `설계_261106_프로필 설정 설계서`에 정의돼 있다(요구사항 v1.1 에 옮길 예정, 6장).
- 표의 열: **ID**(기능 번호) / **원자 기능** / **요구사항**(FR) / **API**(앞에 `/api` 생략) / **화면**(주소 경로) / **서버 코드**.

## 2. 한눈에 보는 구조

```
smart-voca
├─ A. 계정        (가입·로그인·로그아웃·로그인 유지)
├─ B. 프로필      (닉네임·아바타·비밀번호·동의·이용권 요약·탈퇴)
├─ C. 단어 데이터 (2,000개 적재·출처 표기·무료 범위 규칙)
├─ D. 학습        (오늘 할 것·새 단어 카드·결과 기록·하루 목표·발음·바로 확인 퀴즈)
├─ E. 퀴즈·힌트   (복습 문제·3단계 힌트·답 채점·틀린 단어 재도전)
├─ F. 복습 계산   (결과→점수·SM-2 다음 복습일·복습 대상 선정)   ← 화면 없음, 서버 로직
├─ G. 즐겨찾기    (담기·해제·목록·골라서 다시 학습)
├─ H. 학습 기록   (요약·배운 단어·연속 학습일·학습 달력)
├─ I. 구독·결제   (요금제·주문·승인 확인·내역·환불)
├─ J. AI 선생님   (단어 질문·하루 횟수 제한)
└─ K. 공통        (오류 형식·로그·설정 분리·상태 확인·약관 문서)
```

영역 11개, 원자 기능 69개.

## 3. 영역별 분해

### A. 계정 (AUTH)
| ID | 원자 기능 | FR | API | 화면 | 서버 코드 |
|---|---|---|---|---|---|
| A-01 | 이메일·비밀번호로 회원가입(필수 동의 3·선택 1 포함) | AUTH-01, 07 | `POST /auth/signup` | `/signup` | auth_service |
| A-02 | 로그인(실패 시 이메일/비밀번호 중 무엇이 틀렸는지 숨김) | AUTH-02 | `POST /auth/login` | `/login` | auth_service |
| A-03 | 로그아웃(로그인 쿠키 삭제) | AUTH-03 | `POST /auth/logout` | 상단 메뉴 | routers/auth |
| A-04 | 내 정보 확인(새로고침해도 로그인 유지) | AUTH-05 | `GET /auth/me` | 전체 | auth_service |
| A-05 | 비밀번호 암호화 저장(원문·로그 금지) | AUTH-04 | — | — | core/security |
| A-06 | 로그인 안 하면 보호 화면·API 접근 차단 | AUTH-06 | (모든 보호 API) | ProtectedRoute | core/dependencies |

### B. 프로필 (PROFILE)
| ID | 원자 기능 | FR | API | 화면 | 서버 코드 |
|---|---|---|---|---|---|
| B-01 | 닉네임 변경(2~12자) | PROFILE | `PATCH /me/profile` | `/settings` 프로필 탭 | profile_service |
| B-02 | 이니셜 아바타 색 고르기(6색) | PROFILE | `PATCH /me/profile` | 프로필 탭 | profile_rules |
| B-03 | 비밀번호 변경(현재 비밀번호 확인) | PROFILE | `POST /me/password` | 보안 탭 | profile_service |
| B-04 | 마케팅 수신 동의 켜기·끄기(바로 저장) | PROFILE | `PATCH /me/consent` | 학습·알림 탭 | consent_rules |
| B-05 | 이용권 요약(요금제·만료일·AI 남은 횟수) | PROFILE | `GET /me/plan` | 이용권 탭 | profile_service |
| B-06 | 회원 탈퇴(비밀번호+확인 문구, 개인정보 익명화) | PROFILE | `POST /me/withdraw` | 보안 탭 | profile_service |
| B-07 | 이용약관·개인정보처리방침 보기 | PROFILE | — | `/terms` `/privacy` | (화면 문서) |

### C. 단어 데이터 (WORD)
| ID | 원자 기능 | FR | API | 화면 | 서버 코드 |
|---|---|---|---|---|---|
| C-01 | 단어 2,000개 적재(여러 번 실행해도 중복 없음) | WORD-01, 05 | — (시드 스크립트) | — | word_import |
| C-02 | 단어 정보 보관(영단어·품사·뜻·예문·번역·순위) | WORD-02 | — | — | models/word |
| C-03 | 빈도 순서로 새 단어 제시 | WORD-06 | `GET /study/new` | `/study` | study_service |
| C-04 | 출처(TSL·NGSL, CC BY-SA 4.0) 표기 | WORD-04 | — | 화면 하단 | SourceNotice |
| C-05 | 무료 범위(순위 250) 밖 단어 잠금 | SUB-01 | (학습·즐겨찾기 API 공통) | — | subscription_service |

### D. 학습 (STUDY)
| ID | 원자 기능 | FR | API | 화면 | 서버 코드 |
|---|---|---|---|---|---|
| D-01 | 오늘 할 것 요약(복습 N개·새 단어 N개·목표 완료 표시) | STUDY-01 | `GET /study/today` | `/` | study_service |
| D-02 | 새 단어 최대 10개 묶음 가져오기 | STUDY-06 | `GET /study/new` | `/study` | study_service |
| D-03 | 플래시카드 학습(앞면 영단어 → 뒷면 뜻·예문) | STUDY-02 | — | `/study` | FlashcardPage |
| D-04 | 카드 결과 선택(몰랐음/애매함/알았음) 기록 | STUDY-03 | `POST /study/flashcard` | `/study` | study_service |
| D-05 | 하루에 배울 새 단어 수 설정(1~50) | STUDY-04 | `PATCH /me/settings` | `/settings` 학습·알림 탭 | study_service |
| D-06 | 발음 듣기(브라우저 내장 음성) | — | — | 카드·퀴즈 | SpeakButton |
| D-07 | 학습 완료 직후 "바로 확인 퀴즈" 이어가기 | — | (E-03 사용) | `/study` 완료 화면 | FlashcardPage |

### E. 퀴즈·힌트 (QUIZ, HINT)
| ID | 원자 기능 | FR | API | 화면 | 서버 코드 |
|---|---|---|---|---|---|
| E-01 | 오늘 복습 문제 목록(예문 속 정답 가림) | QUIZ-01 | `GET /quiz/queue` | `/quiz` | quiz_service |
| E-02 | 영단어를 직접 입력해 답하기 | QUIZ-01 | `POST /quiz/{id}/answer` | `/quiz` | quiz_service |
| E-03 | 방금 배운 단어 확인 퀴즈(복습 일정 안 바뀜) | — | `GET /quiz/check` | `/quiz/check` | quiz_service |
| E-04 | 힌트 1단계: 철자 섞기 | HINT-01 | `POST /quiz/{id}/hint` | `/quiz` | core_logic/hints |
| E-05 | 힌트 2단계: 빈칸 힌트 | HINT-02 | `POST /quiz/{id}/hint` | `/quiz` | core_logic/hints |
| E-06 | 힌트 3단계: 정답 확인("힌트 사용"으로 별도 기록) | HINT-03 | `POST /quiz/{id}/hint` | `/quiz` | core_logic/hints |
| E-07 | 힌트는 1→2→3 순서로만 열기, 사용한 최고 단계 저장 | HINT-04 | `POST /quiz/{id}/hint` | `/quiz` | quiz_service |
| E-08 | 짧은 단어·공백 포함 표현의 힌트 예외 처리 | HINT-05 | — | — | core_logic/hints |
| E-09 | 틀린 단어만 모아 다시 풀기 | — | (받은 문제에서 거름) | `/quiz`, `/quiz/check` | QuizPage |

### F. 복습 계산 (SRS) — 화면 없는 서버 로직
| ID | 원자 기능 | FR | API | 화면 | 서버 코드 |
|---|---|---|---|---|---|
| F-01 | 결과(힌트 단계·정답 여부)를 0~5점으로 바꾸기 | SRS-03 | (E-02, D-04 가 사용) | — | core_logic/quality |
| F-02 | SM-2 규칙으로 다음 복습일·간격·난이도 계산 | SRS-02 | (위와 같음) | — | core_logic/sm2 |
| F-03 | 단어별 복습 상태 저장(다음 복습일·간격·ease·연속 성공) | SRS-01 | — | — | models/user_word |
| F-04 | 오늘 복습 대상 선정(오래 밀린 순) | SRS-04 | `GET /quiz/queue` | — | quiz_service |
| F-05 | 한 번에 보여 줄 양 제한 | SRS-05 | `GET /quiz/queue` | — | quiz_service |

### G. 즐겨찾기 (FAVORITE)
| ID | 원자 기능 | FR | API | 화면 | 서버 코드 |
|---|---|---|---|---|---|
| G-01 | 별표로 단어 담기(무료 범위 밖은 거부) | — | `PUT /favorites/{id}` | 카드·퀴즈 정답 후 | favorite_service |
| G-02 | 별표 해제(잠긴 단어도 해제는 가능) | — | `DELETE /favorites/{id}` | 카드·목록 | favorite_service |
| G-03 | 즐겨찾기 목록 보기 | — | `GET /favorites` | `/favorites` | favorite_service |
| G-04 | 골라서 다시 학습(무작위 최대 20, 복습 일정 안 바뀜) | — | `GET /favorites/study` | `/favorites/study` | favorite_service |

### H. 학습 기록 (PROG)
| ID | 원자 기능 | FR | API | 화면 | 서버 코드 |
|---|---|---|---|---|---|
| H-01 | 모든 학습·퀴즈 결과 기록(단어·시각·결과·힌트 단계) | PROG-01 | (D-04, E-02 가 저장) | — | models/review_log |
| H-02 | 오늘·누적 학습 단어 수 | PROG-02 | `GET /progress/summary` | `/progress` | progress_service |
| H-03 | 연속 학습일 계산 | PROG-03 | `GET /progress/summary` | `/progress` | progress_rules |
| H-04 | 숙련도(새 단어/학습 중/익숙함)별 개수 | PROG-04 | `GET /progress/summary` | `/progress` | progress_service |
| H-05 | 전체 2,000개 중 진행 정도 | PROG-05 | `GET /progress/summary` | `/progress` | progress_service |
| H-06 | 배운 단어 목록(최근 순·숙련도 배지) | — | `GET /progress/words` | `/progress` | progress_service |
| H-07 | 학습 달력(12주 잔디, 최장 연속) | — | `GET /progress/calendar` | `/progress` | progress_rules |

### I. 구독·결제 (SUB)
| ID | 원자 기능 | FR | API | 화면 | 서버 코드 |
|---|---|---|---|---|---|
| I-01 | 요금제 범위 정의(무료 250 / 프리미엄 2,000) | SUB-01 | `GET /subscription` | `/subscribe` | subscription_service |
| I-02 | 결제 주문 만들기 | SUB-02 | `POST /payments/orders` | `/subscribe` | subscription_service |
| I-03 | 결제창 열기(토스 결제위젯, 테스트 키) | SUB-02 | — | `/subscribe` | payments/toss_provider |
| I-04 | 결제 승인 확인(서버가 결제사에 직접 확인한 뒤에만 이용권 부여) | SUB-03, 06 | `POST /payments/confirm` | `/payment/success` | subscription_service |
| I-05 | 이용권 30일 부여·만료일 표시·만료 시 무료로 복귀 | SUB-05 | `GET /subscription` | `/subscribe` | payment_rules |
| I-06 | 결제 내역 보기(결제 대기 건 제외) | SUB-04 | `GET /payments` | `/subscribe` | subscription_service |
| I-07 | 환불(가장 최근·7일 이내·프리미엄 단어 미학습) | — | `POST /payments/{id}/refund` | `/subscribe` | subscription_service |
| I-08 | 결제 실패 안내 | SUB-06 | — | `/payment/fail` | PaymentFailPage |
| I-09 | 결제사 교체 가능 구조(진짜 토스 ↔ 가짜 담당자) | SUB-08 | — | — | payments/provider |

### J. AI 선생님 (AI)
| ID | 원자 기능 | FR | API | 화면 | 서버 코드 |
|---|---|---|---|---|---|
| J-01 | 단어에 대해 질문하고 설명 받기(Gemini) | — | `POST /ai/teacher` | 화면 오른쪽 아래 창 | ai_service |
| J-02 | 하루 질문 횟수 제한(무료 10 / 프리미엄 50) | — | `POST /ai/teacher` | 같음 | ai_service |
| J-03 | AI 담당자 교체 가능 구조(진짜 Gemini ↔ 가짜) | — | — | — | ai/provider |

### K. 공통 (SYS)
| ID | 원자 기능 | FR | API | 화면 | 서버 코드 |
|---|---|---|---|---|---|
| K-01 | 이해할 수 있는 오류 메시지(서버 내부 내용 숨김) | SYS-01 | (모든 API) | 전체 | core/errors |
| K-02 | 주요 사건 로그(비밀번호·카드 정보 제외) | SYS-02 | — | — | core/logging |
| K-03 | 설정 값을 `.env` 로 분리 | SYS-03 | — | — | core/config |
| K-04 | 서버 상태 확인 | — | `GET /health` | `/status` | routers/health |
| K-05 | 핵심 로직 자동 테스트 | SYS-05 | — | — | tests/ (총 400여 개) |
| K-06 | 시연용 데모 계정 만들기·초기화 | — | — | — | ai-agent/scripts/seed_demo.py |
| K-07 | DB 백업·복원 도구 | — | — | — | ai-agent/scripts/db_backup.py |

## 4. 화면 기준으로 다시 보기

| 화면 | 주소 | 들어 있는 기능 |
|---|---|---|
| 홈 | `/` | D-01, D-07 진입 |
| 새 단어 학습 | `/study` | C-03, D-02~D-04, D-06, D-07, G-01 |
| 복습 퀴즈 | `/quiz` | E-01, E-02, E-04~E-09, G-01 |
| 바로 확인 퀴즈 | `/quiz/check` | E-03, E-09 |
| 즐겨찾기 | `/favorites`, `/favorites/study` | G-02~G-04 |
| 학습 기록 | `/progress` | H-02~H-07 |
| 프리미엄 | `/subscribe` | I-01~I-07 |
| 결제 결과 | `/payment/success`, `/payment/fail` | I-04, I-08 |
| 설정 | `/settings` (탭 4개) | B-01~B-06, D-05 |
| 가입·로그인 | `/signup`, `/login` | A-01, A-02, B-07 |
| 약관·방침 | `/terms`, `/privacy` | B-07 |
| 상태 | `/status` | K-04 |
| AI 선생님 | (모든 화면 공통 창) | J-01~J-03 |

## 5. 요구사항 역추적 (빠진 요구사항 점검)

요구사항 명세서의 FR 번호가 위 표 어딘가에 모두 나오는지 확인했다.

| FR 묶음 | 연결된 기능 | 결과 |
|---|---|---|
| AUTH-01~07 | A-01~A-06 | 모두 연결 |
| WORD-01~06 | C-01~C-04 (WORD-03 뜻·예문 작성과 표본 검수는 데이터 작업이라 기능이 아님) | 연결 완료, 표본 검수 결과는 미반영 |
| STUDY-01~06 | D-01~D-05 (STUDY-05 "나가도 이어서"는 결과를 카드마다 저장하는 D-04 로 충족) | 연결 완료 |
| QUIZ-01~03, HINT-01~06 | E-01~E-08 | 모두 연결 |
| SRS-01~06 | F-01~F-05 | 모두 연결 |
| PROG-01~05 | H-01~H-05 | 모두 연결 |
| SUB-01~08 | I-01~I-09 (SUB-07 자동 갱신은 구현 안 함) | 연결 완료 |
| SYS-01~05 | K-01~K-05 (SYS-04 실행 문서는 README·운영 정의서) | 연결 완료 |

## 6. 요구사항에 없던 기능 (구현 중 추가)

요구사항 명세서 v1.0 이후 대표 요청으로 늘어난 기능이다. 요구사항 명세서 v1.1(이슈 #10)에 반영해야 한다.

| 기능 | 이슈 | 날짜 |
|---|---|---|
| 단어 500 → 2,000개 확장 | #14 | 11-05 |
| AI 선생님 (J) | #16 | 11-06 |
| 프로필 설정 (B-01~B-06) | #17 | 11-06 |
| 가입 동의·약관 (A-01 동의 부분, B-04, B-07) | #18 | 11-06 |
| 발음 듣기 (D-06) | #19 | 11-06 |
| 배운 단어 목록 (H-06) | #20 | 11-06 |
| 바로 확인 퀴즈·틀린 단어 재도전 (D-07, E-03, E-09) | #21 | 11-06 |
| 즐겨찾기 (G) | #22 | 11-06 |
| 환불 (I-07) | — | 11-06 |
| 학습 달력 (H-07) | — | 11-06 |
| 설정 화면 탭 재배치 | — | 11-11 |

## 7. 구현하지 않은 기능 (의도적)

| 기능 | 이유 |
|---|---|
| 자동 갱신(정기결제)·구독 해지 | FR-SUB-07. 환불로 대체. 계약 후 확장 가능한 구조로만 설명 |
| 소셜 로그인, 이메일 인증, 비밀번호 찾기 | 범위 밖(기획서). 정식 출시 전 과제 |
| 학습 알림(푸시·이메일) | 범위 밖. 설정의 "알림"은 마케팅 수신 동의만 있음 |
| 기존 회원 약관 재동의 | 정식 출시 전 과제 |
| 목표 설정("오늘 12/20")·성장 단계 | 기획에 없음. 학습 기록 스케치에서 제외 결정 |

## 8. 이 문서의 한계

- 원자 기능 수(69개)는 이 문서 기준의 셈법이다. 같은 API 를 쓰는 화면 동작을 하나로 보는지 둘로 보는지에 따라 달라질 수 있다.
- 서버 코드 열은 파일 단위까지만 적었다. 함수 단위 설명은 프로세스 설계서(설계_261111_프로세스 설계서)에서 다룬다.
- 테스트 개수는 일지 기준이며, 최신 개수는 `pytest` 로 확인한다.
