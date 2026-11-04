// 2026-11-04 - smart-voca - 오늘 할 것·새 단어·플래시카드·설정 API 호출 함수 (인터페이스 정의서 4.2·4.3)
// 파일 위치: src/frontend/src/api/study.js
import { apiFetch } from './client'

export function getToday() {
  return apiFetch('/study/today')
}

export async function getNewWords(limit = 10) {
  const data = await apiFetch(`/study/new?limit=${limit}`)
  return data.items
}

/** rating: 'dont_know' | 'unsure' | 'know' */
export function submitFlashcard(wordId, rating) {
  return apiFetch('/study/flashcard', { method: 'POST', body: { word_id: wordId, rating } })
}

export async function updateDailyNewLimit(dailyNewLimit) {
  const data = await apiFetch('/me/settings', { method: 'PATCH', body: { daily_new_limit: dailyNewLimit } })
  return data.user
}
