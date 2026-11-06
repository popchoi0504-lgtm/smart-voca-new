# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - 테스트에서 가입할 때 함께 보내는 동의 항목 (가입 동의 설계서 8장)
# 파일 위치: src/backend/tests/consent_helpers.py
from app.core_logic.consent_rules import TERMS_VERSION

# 가입 요청 본문에 합쳐서 쓴다: json={**CREDENTIALS, **SIGNUP_CONSENT}
SIGNUP_CONSENT = {"agree_age": True, "agree_terms": True, "agree_privacy": True, "terms_version": TERMS_VERSION}
