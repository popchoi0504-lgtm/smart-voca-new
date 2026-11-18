# 테스트 정의서 (Test Specification)

**파일 위치**: `docs/테스트_261118_테스트 정의서(Test Specification) v1.0.md`
**작성일**: 2026-11-18
**버전**: v1.0 (초안, 대표 검토 전)
**설명**: smart-voca 백엔드·화면의 테스트 범위, 실행 방법, 모듈별 테스트 시나리오(BDD 형식), 미비점을 정리한다.

> 이 문서는 방법론 §2 "테스트 정의서(Test Specification)" 산출물의 초안이다. 옛 버전 방법론(`docs/개발방법론.md`) 기준으로 작성했다.
> 실행 결과는 이 PC에 백엔드 가상환경(`.venv`)과 테스트용 DB가 없어서 **아직 실행하지 않았다**. 실행 결과 칸은 비워 두었다.

---

## 1. 목적과 범위

- **목적**: 요구사항(Requirement Spec)에 적힌 규칙이 코드에서 실제로 지켜지는지 자동으로 확인한다. 보안·개인정보 규칙(로그에 비밀번호·이메일이 남지 않음)도 확인한다.
- **포함**: 백엔드 단위 테스트(규칙 계산, 외부 연동 응답 해석), 백엔드 통합 테스트(API 호출 → DB 저장 → 응답 확인).
- **제외(현재 없음)**: 화면(프론트엔드) 자동 테스트, 브라우저 끝단 테스트(E2E). 화면은 직접 확인(같은 동작 2회 이상)으로 대신한다. 9장 참조.

## 2. 테스트 수준

| 수준 | 대상 | 특징 | 예 |
|------|------|------|-----|
| 단위 테스트 (Unit) | `core_logic/`의 순수 계산 규칙 | DB·네트워크 없이 빠르게 실행 | SM-2 복습 간격, 힌트 생성, 연속 학습 일수 |
| 통합 테스트 (Integration) | `routers/` + `services/` + DB | 실제 API를 호출하고 DB 결과를 확인 | 로그인, 학습 저장, 결제 확인 |
| 인터페이스 테스트 (Interface) | 외부 연동 응답 해석 (`payments/toss_provider.py`, `ai/gemini_provider.py`) | 외부 서비스 대신 가짜 응답을 넣어 확인 | 토스 취소 실패, Gemini 응답 형식 오류 |
| 보안·로그 테스트 | 암호화, 토큰, 로그 출력 | 비밀값이 로그·응답에 없는지 확인 | 로그에 이메일·키가 없는지 |

## 3. 실행 방법

- **위치**: `src/backend` 폴더
- **명령**: `.\.venv\Scripts\python.exe -m pytest -v`
- **DB**: 테스트 전용 `smart_voca_test`만 사용한다. 개발 DB `smart_voca`는 건드리지 않는다. 시작할 때 Alembic으로 표를 지우고 처음부터 다시 만든다. DB 이름이 다르면 테스트가 스스로 멈춘다(`TEST_DATABASE_URL` 확인).
- **외부 연동**: 토스·Gemini는 실제로 호출하지 않는다. 가짜 응답(fake provider, 가짜 전송 객체)을 쓴다.

## 4. 테스트 파일별 범위 (백엔드)

개수는 `pytest --collect-only` 로 수집한 값이다 (2026-11-18). 실행 결과(통과/실패)는 3장 명령으로 확인해야 한다.

| 파일 | 개수 | 대상 | 수준 |
|------|------|------|------|
| `test_sm2.py` | 16 | SM-2 복습 간격·쉬움 정도 계산 | 단위 |
| `test_hints.py` | 49 | 힌트(글자 섞기·가리기), 시드 규칙, 품질 값 표 | 단위 |
| `test_progress_rules.py` | 21 | 연속 학습 일수(KST 자정 기준), 숙달 기준 21일 | 단위 |
| `test_profile_rules.py` | 15 | 닉네임 규칙(글자 수), 자동 색 | 단위 |
| `test_payment_rules.py` | 12 | 결제 규칙 | 단위 |
| `test_toss_provider.py` | 13 | 토스 응답 해석(승인·취소·오류) | 인터페이스 |
| `test_gemini_provider.py` | 17 | Gemini 응답 해석·길이 제한·오류 | 인터페이스 |
| `test_auth.py` | 25 | 가입·로그인·로그아웃·쿠키 | 통합 |
| `test_study.py` | 40 | 오늘의 단어, 평가 저장, 하루 목표 | 통합 |
| `test_quiz.py` | 41 | 복습 큐, 정답 확인, 힌트 사용, 확인 퀴즈 | 통합 |
| `test_progress.py` | 23 | 학습 요약, 연속 일수, 달력, 배운 단어 목록 | 통합 |
| `test_subscription.py` | 39 | 구독 주문·확인·환불·결제 내역 | 통합 |
| `test_profile.py` | 34 | 닉네임·비밀번호 변경·이용권 요약·회원 탈퇴 | 통합 |
| `test_consent.py` | 25 | 가입 동의(필수 3·선택 1), 약관 버전, 마케팅 동의 변경 | 통합 |
| `test_favorites.py` | 11 | 즐겨찾기 추가·삭제·목록·무료 범위 차단 | 통합 |
| `test_ai_teacher.py` | 18 | AI 선생님 호출 횟수 제한, 개인정보 미전송 | 통합 |
| `test_word_import.py` | 16 | 단어 CSV 가져오기 | 통합 |
| `test_security.py` | 11 | 비밀번호 해시(argon2id), 토큰 서명·만료 | 단위(보안) |
| `test_log_safety.py` | 3 | 로그에 비밀값·이메일이 없는지 | 보안 |
| `test_health.py` | 4 | 상태 확인 API, 오류 응답 형식 | 통합 |

**합계**: 433개 (conftest 제외, 2026-11-18 `pytest --collect-only` 수집 기준). 테스트를 추가하거나 줄이면 이 표와 7장의 개수를 함께 고친다.

## 5. 모듈별 테스트 시나리오 (BDD 형식 요약)

형식: **Given**(주어진 상황) / **When**(행동) / **Then**(기대 결과). 아래는 테스트 함수 이름에서 뽑은 대표 시나리오다.

### 5.1 SM-2 복습 간격 (`test_sm2.py`)
- **Given** 처음 맞혔을 때 **When** 계산하면 **Then** 다음 복습은 1일 뒤다.
- **Given** 두 번째로 맞혔을 때 **Then** 다음 복습은 6일 뒤다.
- **Given** 품질 점수가 낮을 때(0~2) **When** 계산하면 **Then** 처음부터 다시 시작한다.
- **Given** 쉬움 정도(ease factor)가 최솟값 아래로 내려가려 할 때 **Then** 최솟값에서 멈춘다.
- **Given** 범위 밖 품질 값(예: 6) **Then** 오류가 난다.

### 5.2 힌트 (`test_hints.py`)
- **Given** 같은 단어·같은 날·같은 사용자 **When** 힌트를 여러 번 만들면 **Then** 항상 같은 결과가 나온다(날짜가 바뀌면 달라진다).
- **Given** 다른 사용자 **Then** 힌트가 달라진다.
- **Given** 3글자 이하 단어 **Then** 글자 섞기 힌트를 건너뛴다. 4글자부터는 적용한다.
- **Given** 공백·하이픈이 있는 단어 **Then** 그 자리는 그대로 둔다.
- **Given** 가리기 힌트 **Then** 첫 글자는 항상 보이고, 가려진 글자는 최소 1개다.

### 5.3 연속 학습 일수 (`test_progress_rules.py`, `test_progress.py`)
- **Given** 오늘 학습했음 **Then** 연속 일수가 이어진다.
- **Given** 어제까지 학습하고 오늘은 아직 안 함 **Then** 어제까지의 연속 일수가 그대로 유지된다.
- **Given** 하루라도 건너뜀 **Then** 연속 일수가 끊기고, 가장 최근 연속 구간만 센다.
- **Given** 한국 시간 자정 전후 **Then** 날짜 경계는 한국 시간 기준으로 정한다.
- **Given** 21일 이상 맞힌 단어 **Then** 숙달로 센다(경계값 포함 테스트).

### 5.4 오늘의 학습·평가 저장 (`test_study.py`)
- **Given** 새 사용자 **When** 오늘의 단어를 요청하면 **Then** 순위가 낮은(흔한) 단어부터 나오고, 이미 배운 단어는 빠진다.
- **Given** 무료 범위 밖 단어 **When** 학습을 저장하면 **Then** 거부된다(프리미엄은 허용).
- **Given** 같은 평가를 두 번 보냄 **Then** 409 응답이며 데이터는 바뀌지 않는다.
- **Given** 하루 목표를 올림 **Then** 차이만큼 새 단어가 추가된다.
- **Given** 무료 사용자가 무료 범위를 다 끝냄 **Then** 잠긴다(하루 목표는 막는 기준이 아니라 목표다).

### 5.5 복습 큐·정답 확인·확인 퀴즈 (`test_quiz.py`)
- **Given** 복습할 단어가 없음 **Then** 빈 큐가 나온다.
- **Given** 큐 응답 **Then** 정답 단어가 포함되지 않는다(응답 안전 확인).
- **Given** 큐 정렬 **Then** 가장 오래 밀린 단어가 먼저 나온다.
- **Given** 대소문자·앞뒤 공백이 다른 정답 **Then** 맞은 것으로 본다.
- **Given** 오답 **Then** 정답은 숨긴 채 실패를 기록한다. 같은 요청을 두 번 보내면 한 번만 센다.
- **Given** 힌트를 쓴 뒤 정답 **Then** 품질 점수가 낮게 기록된다. 힌트 공개는 오답과 따로 기록한다.
- **Given** 확인 퀴즈 요청 **Then** 배운 단어만, 최대 10개, 다른 사용자 단어는 거부한다. 확인 퀴즈는 일정과 기록을 바꾸지 않는다.

### 5.6 구독·결제 (`test_subscription.py`, `test_payment_rules.py`, `test_toss_provider.py`)
- **Given** 주문 생성 **Then** 금액은 서버가 정한다(클라이언트 값 무시).
- **Given** 결제 확인 금액이 주문과 다름 **Then** 외부 호출 없이 거부한다.
- **Given** 같은 결제 확인을 두 번 **Then** 기간이 두 번 늘지 않는다.
- **Given** 외부 서비스 점검 중 **Then** 주문은 대기 상태로 남고 다시 시도할 수 있다.
- **Given** 결제 후 프리미엄 단어를 학습함 **Then** 환불이 막힌다(무료 단어만 학습했으면 가능).
- **Given** 환불 2회 **Then** 두 번째는 막히고 외부 취소는 1회만 호출된다.
- **Given** 환불 가능 기간 지남 **Then** 막힌다.

### 5.7 회원 정보 (`test_profile.py`, `test_consent.py`, `test_auth.py`)
- **Given** 닉네임 규칙 위반 **Then** 거부한다. 글자 수는 바이트가 아니라 글자 기준으로 센다.
- **Given** 비밀번호 변경 시 현재 비밀번호 틀림 **Then** 아무것도 바뀌지 않는다.
- **Given** 회원 탈퇴 **Then** 개인 정보는 익명 처리되고 학습 기록은 삭제되며, 같은 이메일로 다시 가입할 수 있다. 다른 회원 데이터는 그대로다.
- **Given** 가입 시 필수 동의 중 하나라도 빠짐 **Then** 거부한다.
- **Given** 약관 버전 불일치 **Then** 409 응답이다. 서버와 화면의 약관 버전이 같은지도 테스트한다.
- **Given** 로그인 실패 **Then** 이메일이 틀렸는지 비밀번호가 틀렸는지 알려주지 않는다.
- **Given** 위조되거나 만료된 쿠키 **Then** 거부한다.

### 5.8 즐겨찾기·AI 선생님·보안·로그
- **Given** 무료 사용자가 프리미엄 단어를 즐겨찾기 **Then** 거부한다. 구독 만료 후에도 즐겨찾기 목록은 남지만 잠긴다.
- **Given** AI 선생님 무료 사용자 하루 10회 초과 **Then** 거부한다. 실패한 호출은 횟수에 세지 않는다.
- **Given** AI 선생님 요청 **Then** 단어 정보만 보내고 개인 정보는 보내지 않는다.
- **Given** 정상 흐름·로그인 실패·예외 발생 **Then** 로그에 비밀번호·이메일·API 키가 없다.
- **Given** 비밀번호 저장 **Then** argon2id 해시로 저장하고, 같은 비밀번호도 매번 다른 해시가 나온다.

## 6. 요구사항 추적성 (미완성)

방법론과 이슈 #11에 따라 요구사항 명세서(`docs/분석_261118_요구사항 명세서(Requirement Spec) v1.1.md`)의 FR ID별로 대응 테스트를 정리한다.

**상태 기호**: ✅ 자동 테스트가 해당 규칙을 다룸 / ⚠️ 일부만 다룸(세부 확인 필요) / 🖐 수동 확인 / ❌ 대응 테스트 없음

| FR ID | 요구사항 요지 | 대응 테스트 (파일: 함수 일부) | 상태 |
|-------|---------------|-------------------------------|------|
| FR-AUTH-01 | 회원가입, 이메일 중복 거부 | `test_auth.py`: signup_creates_user, signup_rejects_duplicate_email | ✅ |
| FR-AUTH-02 | 로그인, 실패 시 어느 쪽이 틀렸는지 숨김 | `test_auth.py`: login_succeeds…, login_failures_do_not_reveal… | ✅ |
| FR-AUTH-03 | 로그아웃 | `test_auth.py`: logout_clears_login | ✅ |
| FR-AUTH-04 | 비밀번호 해시 저장, 원문·로그 미기록 | `test_security.py`: hash_is_argon2id…; `test_log_safety.py` | ✅ |
| FR-AUTH-05 | 토큰 만료 시간 | `test_security.py`: expired_token_is_rejected; `test_auth.py`: expired_cookie_is_rejected | ✅ |
| FR-AUTH-06 | 로그인 없으면 접근 불가 | `test_auth.py`: me_requires_login; `test_study.py`, `test_quiz.py`, `test_progress.py`, `test_subscription.py`: requires_login | ✅ |
| FR-AUTH-07 | 서버에서 입력 검증 | `test_auth.py`: signup_rejects_weak_password, bad_email, login_rejects_absurdly_long_input | ✅ |
| FR-WORD-01 | 단어 2,000개 저장 | 자동 테스트 없음 (시드 후 개수 확인 필요) | ❌ |
| FR-WORD-02 | 단어 항목(영단어·뜻·예문 등) | `test_word_import.py` (CSV 읽기) | ⚠️ |
| FR-WORD-03 | TSL 뼈대, 샘플 검수 | 데이터 검수 (`표본검수_100.md`) | 🖐 |
| FR-WORD-04 | TSL 출처 표기 | 화면 확인 | 🖐 |
| FR-WORD-05 | 시드 여러 번 실행해도 중복 없음 | `test_word_import.py` (중복 처리 여부 세부 확인 필요) | ⚠️ |
| FR-WORD-06 | 빈도 순서로 새 단어 제시 | `test_study.py`: new_words_come_in_rank_order | ✅ |
| FR-STUDY-01 | 오늘 할 것: 복습·새 단어 수 | `test_study.py`: today_for_new_user | ✅ |
| FR-STUDY-02 | 플래시카드 학습 | `test_study.py`: flashcard_validation (화면 자체는 🖐) | ⚠️ |
| FR-STUDY-03 | 몰랐음·애매함·알았음 → 복습 계산 | `test_study.py`: rating_ten_new_words…, rating_is_converted_to_quality, dont_know_keeps_ease_factor | ✅ |
| FR-STUDY-04 | 하루 새 단어 수 설정 | `test_study.py`: daily_limit_setting…, daily_limit_boundaries | ✅ |
| FR-STUDY-05 | 중간에 나가도 이어서 학습 | 자동 테스트 없음 | 🖐 |
| FR-STUDY-06 | 한 세션 단어 수 제한 | `test_study.py`: new_words_limit_validation; `test_quiz.py`: queue_limits_one_session | ⚠️ |
| FR-QUIZ-01 | 복습 대상으로 퀴즈, 영단어 입력 | `test_quiz.py`: queue_*, answer_* | ✅ |
| FR-QUIZ-02 | 정답 처리·계산 반영 | `test_quiz.py`: correct_without_hint…, answer_ignores_case… | ✅ |
| FR-QUIZ-03 | 오답 시 재시도·힌트 | `test_quiz.py`: wrong_answer_hides…, retry_after_wrong_is_practice… | ✅ |
| FR-HINT-01 | 1단계 철자 섞기 (같으면 재섞기) | `test_hints.py`: scramble_* | ✅ |
| FR-HINT-02 | 2단계 빈칸 힌트 (첫 글자 공개, 약 40%) | `test_hints.py`: mask_* | ✅ |
| FR-HINT-03 | 3단계 정답 확인은 오답과 별도 기록 | `test_quiz.py`: revealed_is_recorded_separately_from_wrong | ✅ |
| FR-HINT-04 | 1→2→3 순서, 최고 단계 저장 | `test_quiz.py`: hint_levels_return_expected_shapes | ⚠️ (순서 강제 세부 확인) |
| FR-HINT-05 | 3글자 이하·같은 글자 예외, 공백·하이픈 고정 | `test_hints.py`: scramble_skipped_for_short…, keeps_space_and_hyphen…, mask_keeps_space_and_hyphen | ✅ |
| FR-HINT-06 | 힌트 로직 단독 테스트 가능 | `test_hints.py` 전체 (화면·DB 없이 실행) | ✅ |
| FR-SRS-01 | 단어별 복습 상태 저장 | `test_quiz.py`: next_day_the_word_is_due…; `test_sm2.py` | ⚠️ |
| FR-SRS-02 | 점수로 다음 복습 날짜 계산 | `test_sm2.py` 전체, `test_quiz.py`: correct_without_hint… | ✅ |
| FR-SRS-03 | 결과 → SM-2 점수 규칙 | `test_hints.py`: quiz_quality_table, quiz_quality_rejects_invalid; `test_sm2.py`: flashcard_rating_to_quality | ✅ |
| FR-SRS-04 | 오늘 이전 복습 대상, 오래 밀린 순 | `test_quiz.py`: queue_orders_most_overdue_first, queue_only_shows_own_words | ✅ |
| FR-SRS-05 | 많으면 한 세션 분량씩 | `test_quiz.py`: queue_limits_one_session_but_reports_total | ✅ |
| FR-SRS-06 | SM-2 로직 단독 테스트 | `test_sm2.py` 전체 | ✅ |
| FR-PROG-01 | 모든 결과 기록 | `test_quiz.py`, `test_study.py`: 기록 확인 항목 | ⚠️ |
| FR-PROG-02 | 오늘·누적 학습 단어 수 | `test_progress.py`: reviewed_counts_distinct_words…, yesterdays_logs_do_not_count_as_today | ✅ |
| FR-PROG-03 | 연속 학습일 | `test_progress_rules.py` 전체, `test_progress.py`: streak_* | ✅ |
| FR-PROG-04 | 숙련도 3단계 개수 | `test_progress.py`: three_groups_always_add_up…, mastery_boundary_at_21_days | ✅ |
| FR-PROG-05 | 전체 2,000개 중 진행률 시각화 | `test_progress.py` 수치 확인, 막대 그래프는 🖐 | ⚠️ |
| FR-SUB-01 | 요금제·범위 (무료 250, 30일 4,900원) | `test_subscription.py`: subscription_shows_plans…; `test_payment_rules.py` | ✅ |
| FR-SUB-02 | 이용권 구매 (결제위젯 테스트 키) | `test_subscription.py`: order_is_pending_and_amount_is_set_by_server | ✅ (실제 위젯은 🖐) |
| FR-SUB-03 | 서버가 결제사에 승인 확인 후 부여 | `test_subscription.py`: confirm_grants_pass_once; `test_toss_provider.py` | ✅ |
| FR-SUB-04 | 결제 내역 조회 | `test_subscription.py`: payment_list_is_mine_and_newest_first | ✅ |
| FR-SUB-05 | 만료일 표시, 만료 후 무료 복귀 | `test_subscription.py`: expired_pass_is_free_again, pass_unlocks_premium_words… | ✅ (표시는 🖐) |
| FR-SUB-06 | 취소·실패·중복에도 잘못 부여 안 됨 | `test_subscription.py`: confirm_twice…, amount_mismatch…, refund_twice…, provider_outage_keeps_pending… | ✅ |
| FR-SUB-07 | 자동 갱신은 구현하지 않음 | 대상 아님 (설계 설명으로 확인) | — |
| FR-SUB-08 | 결제 부분 분리 (가짜 결제 대체 가능) | `test_subscription.py`: default_provider_without_fake_override_is_toss (가짜 결제 전환 동작은 세부 확인 필요) | ⚠️ |
| FR-SYS-01 | 오류 메시지, 내부 내용 비노출 | `test_health.py`: unknown_route_uses_standard_error_shape; `test_log_safety.py`: unexpected_error_hides_details… | ✅ |
| FR-SYS-02 | 주요 이벤트 로그, 비밀값 미기록 | `test_log_safety.py` 3개 | ✅ |
| FR-SYS-03 | `.env` 분리, `.env.example` 만 커밋 | 자동 테스트 없음 (`.gitignore` 확인 필요) | 🖐 |
| FR-SYS-04 | 처음부터 실행하는 문서 | 운영·배포 정의서 절차 실행 (이슈 #12) | 🖐 |
| FR-SYS-05 | 핵심 로직 자동 테스트 | SM-2, 힌트, 결제 검증, 인증 테스트 전체 | ✅ |
| NFR-QA-01 | 핵심 로직 자동 테스트 + BDD 작성 | 이 문서 5장 (BDD 요약) | ✅ |

**요약**: 자동 테스트로 확인되는 FR은 대부분이다. 빈칸(❌)은 FR-WORD-01(2,000개 개수 확인)뿐이다. 수동 확인(🖐)은 화면 표시, 단어 검수, 실행 절차 등이다.

## 7. 실행 결과

| 항목 | 결과 |
|------|------|
| 실행 일시 | 2026-11-18 (대표 PC 아님, 작업 PC 에서 실행) |
| 전체 개수 | 433개 수집 |
| 통과 / 실패 | **433개 통과, 0개 실패** (경고 1개: FastAPI 테스트 도구의 httpx 사용 중단 안내, 기능 영향 없음) |
| 실행 환경 | Windows 11, Python 3.11.1 (가상환경), PostgreSQL 17 (Docker 컨테이너, 로컬 전용), 테스트 DB `smart_voca_test` |
| 실행 명령 | `cd src/backend` → `$env:PYTHONUTF8=1` (또는 `set PYTHONUTF8=1`) → `.\.venv\Scripts\python.exe -m pytest -q` |
| 발견한 문제와 조치 | `alembic.ini` 의 한국어 주석을 Windows 기본 인코딩(cp949)으로 읽다가 테스트 준비 단계에서 261개가 오류. 주석을 영어로 바꿔 해결 (2026-11-18) |

**참고**: 4장의 파일별 개수는 이 실행과 같은 날 수집한 값이다(합계 433).

## 8. 알려진 함정

- Windows 경로에서 `curl`로 확인할 때 `/`로 시작하는 문자열이 경로로 바뀔 수 있다(표시 문제).
- 테스트는 `smart_voca_test`를 지우고 다시 만든다. 개발 DB 이름을 넣지 않도록 주의한다.

## 9. 빠진 부분과 다음 할 일

1. **화면 테스트가 없다.** 프론트엔드에는 자동 테스트 파일이 없다. 화면은 직접 확인에 기대고 있다. 이후 핵심 화면(로그인, 학습, 퀴즈) 자동 테스트를 추가할지 결정이 필요하다.
2. **실행 결과는 기록되었다.** 2026-11-18 실행에서 433개 통과. 다음 실행 때 7장을 갱신한다.
3. **요구사항 ID 연결은 초안만 완료.** 6장은 FR ID별로 채웠지만, ⚠️ 항목은 테스트 파일을 직접 읽어 세부를 확인해야 한다. 이슈 #11의 "슬라이스별 누적" 방식에 맞춰 이후 슬라이스마다 갱신한다.
4. **테스트 개수 관리.** 테스트를 추가하면 4장 표와 7장을 같이 고친다.
5. **끝단(E2E) 테스트가 없다.** 가입부터 학습, 결제까지 이어지는 흐름은 자동으로 확인하지 않는다.

---

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-11-18 | 초안 작성. 테스트 파일과 함수 이름을 기준으로 작성, 실행 결과 미포함 |
