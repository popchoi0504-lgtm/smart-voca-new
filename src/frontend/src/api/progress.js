// 2026-11-05 - smart-voca - 학습 기록 요약 API 호출 함수 (인터페이스 정의서 4.5)
// 파일 위치: src/frontend/src/api/progress.js
import { apiFetch } from './client'

/** { today, total_learned_count, total_word_count, current_streak_days, mastery } */
export function getProgressSummary() {
  return apiFetch('/progress/summary')
}
