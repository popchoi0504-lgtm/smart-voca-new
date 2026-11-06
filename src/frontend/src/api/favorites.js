// 2026-11-06 - smart-voca - 즐겨찾기 API 호출 함수 (이슈 #22)
// 파일 위치: src/frontend/src/api/favorites.js
import { apiFetch } from './client'

/** { total_count, items: [{ word_id, headword, part_of_speech, meaning_ko, example_en, example_ko, favorited_date, is_locked }] } 최근에 단 순 */
export function getFavorites() {
  return apiFetch('/favorites')
}

/** { items: 플래시카드용 단어들, total_available } 무작위, 이용권 밖 단어 제외. 복습 일정에는 영향 없는 연습용 */
export function getFavoriteStudyWords(limit = 10) {
  return apiFetch(`/favorites/study?limit=${limit}`)
}

export function addFavorite(wordId) {
  return apiFetch(`/favorites/${wordId}`, { method: 'PUT' })
}

export function removeFavorite(wordId) {
  return apiFetch(`/favorites/${wordId}`, { method: 'DELETE' })
}
