// 2026-11-06 - smart-voca - AI 선생님 질문 API 호출 함수 (AI 선생님 설계서 5장)
// 파일 위치: src/frontend/src/api/ai.js
import { apiFetch } from './client'

/**
 * kind: simple / compare / example / ask(직접 질문, question 필요), context: study(새 단어) / quiz(퀴즈)
 * 성공하면 { answer, remaining_today, daily_limit }. 실패(한도 초과·AI 불가 등)는 ApiError.
 */
export function askTeacher({ wordId, kind, context, question }) {
  const body = { word_id: wordId, kind, context }
  if (kind === 'ask') body.question = question
  return apiFetch('/ai/teacher', { method: 'POST', body })
}
