// 2026-11-05 - smart-voca - 학습 기록 요약 API 호출 함수 (인터페이스 정의서 4.5)
// 파일 위치: src/frontend/src/api/progress.js
import { apiFetch } from './client'

/** { today, total_learned_count, total_word_count, current_streak_days, mastery } */
export function getProgressSummary() {
  return apiFetch('/progress/summary')
}

/** { total_count, items: [{ word_id, headword, part_of_speech, meaning_ko, example_en, example_ko, mastery, first_learned_date }] } 최근에 배운 순 */
export function getLearnedWords() {
  return apiFetch('/progress/words')
}

/** { start_date, end_date, days: [{ date, count }], longest_streak_days, studied_days_this_month } 학습한 날만 들어 있다 */
export function getProgressCalendar(days = 84) {
  return apiFetch(`/progress/calendar?days=${days}`)
}
