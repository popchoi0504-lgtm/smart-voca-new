# -*- coding: utf-8 -*-
# 2026-11-06 - smart-voca - 프로필 수정, 비밀번호 변경, 이용권 요약, 회원 탈퇴(익명화)의 업무 규칙 (FR-PROFILE-01~05)
# 파일 위치: src/backend/app/services/profile_service.py
import logging

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import hash_password, verify_password
from app.core.timeutil import now_utc, to_kst
from app.models.ai_usage import AiUsage
from app.models.review_log import ReviewLog
from app.models.user import User
from app.models.user_word import UserWord
from app.schemas.profile import PasswordChangeRequest, PlanSummaryResponse, ProfileRequest
from app.services import ai_service

logger = logging.getLogger("smart_voca.profile")

# 해시 형식이 아닌 고정 문자열: verify_password 가 항상 False → 탈퇴한 행으로는 어떤 비밀번호로도 로그인할 수 없다
UNUSABLE_PASSWORD_HASH = "!"
DELETED_EMAIL_DOMAIN = "deleted.invalid"  # .invalid 는 실제로 존재할 수 없는 주소 영역


def update_profile(db: Session, user: User, request: ProfileRequest) -> User:
    """보낸 칸(닉네임·색)만 바꾼다."""
    if "nickname" in request.model_fields_set:
        user.nickname = request.nickname
    if "avatar_color" in request.model_fields_set:
        user.avatar_color = request.avatar_color
    db.commit()
    db.refresh(user)
    logger.info("프로필 수정 user_id=%s", user.id)  # 닉네임·이메일 원문은 남기지 않는다
    return user


def _require_password(user: User, password: str) -> None:
    if not verify_password(user.password_hash, password):
        logger.warning("본인 확인 실패(비밀번호 불일치) user_id=%s", user.id)
        raise AppError(400, "WRONG_PASSWORD", "현재 비밀번호가 올바르지 않습니다.")


def change_password(db: Session, user: User, request: PasswordChangeRequest) -> None:
    """현재 비밀번호를 확인한 뒤 새 비밀번호의 해시로 바꾼다. 이미 발급된 증표는 만료까지 유효하다(설계서 6장)."""
    _require_password(user, request.current_password)
    user.password_hash = hash_password(request.new_password)
    db.commit()
    logger.info("비밀번호 변경 user_id=%s", user.id)


def update_consent(db: Session, user: User, marketing_agreed: bool) -> User:
    """마케팅 수신 동의를 바꾼다(철회도 동의만큼 쉬워야 한다, FR-CONSENT-04). 필수 동의는 여기서 바꿀 수 없다."""
    user.marketing_agreed = marketing_agreed
    db.commit()
    db.refresh(user)
    logger.info("마케팅 동의 변경 user_id=%s 값=%s", user.id, marketing_agreed)
    return user


def get_plan_summary(db: Session, user: User) -> PlanSummaryResponse:
    """요금제·만료일·AI 선생님 오늘 남은 횟수. 기존 계산(요금제 판단, 한도)을 그대로 재사용한다."""
    is_premium = user.premium_until is not None and user.premium_until > now_utc()
    limit, used = ai_service.get_usage_today(db, user)
    return PlanSummaryResponse(
        plan="premium" if is_premium else "free",
        premium_until=to_kst(user.premium_until) if user.premium_until else None,
        ai_daily_limit=limit,
        ai_used_today=used,
        ai_remaining_today=max(limit - used, 0),
    )


def withdraw(db: Session, user: User, password: str) -> None:
    """회원 탈퇴(익명화). 학습 기록·AI 횟수는 지우고, 회원 행은 누구인지 알 수 없게 바꿔 남긴다. 결제 기록은 건드리지 않는다.

    전부 한 번의 commit 으로 처리 → 중간에 실패하면 전부 취소(rollback)되어 반쯤 지워진 상태가 없다.
    """
    _require_password(user, password)
    user_id = user.id
    db.execute(delete(UserWord).where(UserWord.user_id == user_id))
    db.execute(delete(ReviewLog).where(ReviewLog.user_id == user_id))
    db.execute(delete(AiUsage).where(AiUsage.user_id == user_id))
    user.email = f"deleted-{user_id}@{DELETED_EMAIL_DOMAIN}"  # UNIQUE 를 지키려 회원마다 다르게
    user.password_hash = UNUSABLE_PASSWORD_HASH
    user.nickname = None
    user.avatar_color = None
    user.premium_until = None
    user.marketing_agreed = False  # 동의 시각·버전은 증빙으로 남긴다(설계서 AD-C7)
    user.deleted_at = now_utc()
    db.commit()
    logger.info("회원 탈퇴(익명화) user_id=%s", user_id)
