// 2026-11-06 - smart-voca - 프로필 수정·비밀번호 변경·이용권 요약·탈퇴 API 호출 함수 (프로필 설정 설계서 3장)
// 파일 위치: src/frontend/src/api/profile.js
import { apiFetch } from './client'

/** 보낸 칸만 바뀐다. 예: { nickname: '듀니' }, { avatar_color: 'pink' }. 성공하면 최신 user. */
export async function updateProfile(changes) {
  const data = await apiFetch('/me/profile', { method: 'PATCH', body: changes })
  return data.user
}

/** 선택 동의(마케팅)만 바꾼다. 성공하면 최신 user. */
export async function updateMarketingConsent(marketingAgreed) {
  const data = await apiFetch('/me/consent', { method: 'PATCH', body: { marketing_agreed: marketingAgreed } })
  return data.user
}

export function changePassword(currentPassword, newPassword) {
  return apiFetch('/me/password', { method: 'POST', body: { current_password: currentPassword, new_password: newPassword } })
}

/** { plan, premium_until, ai_daily_limit, ai_used_today, ai_remaining_today } */
export function getPlanSummary() {
  return apiFetch('/me/plan')
}

export function withdrawAccount(password, confirmText) {
  return apiFetch('/me/withdraw', { method: 'POST', body: { password, confirm_text: confirmText } })
}
