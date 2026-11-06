# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - 가입 동의 규칙: 현재 약관·개인정보처리방침 버전 (가입 동의 설계서 3~4장, FR-CONSENT-01·02)
# 파일 위치: src/backend/app/core_logic/consent_rules.py

# 약관이나 처리방침 문구를 바꿀 때 이 값을 올리고, 화면의 src/frontend/src/legal/version.js 도 같은 값으로 바꾼다
# (두 값이 같은지는 tests/test_consent.py 가 검사한다)
TERMS_VERSION = "2026-11-06"
