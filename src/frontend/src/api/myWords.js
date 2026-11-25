// 2026-11-25 - smart-voca - 내 단어 API 호출 함수 (이슈 #24, VOCA-FR-001~004)
// 파일 위치: src/frontend/src/api/myWords.js
import { apiFetch } from './client'

/** { total_count, page, page_size, items: [{ id, headword, meaning_ko, next_review_date, created_date }] } */
export function getMyWords(query = '', page = 1) {
  return apiFetch(`/my-words?q=${encodeURIComponent(query)}&page=${page}`)
}

export function createMyWord(headword, meaningKo) {
  return apiFetch('/my-words', { method: 'POST', body: { headword, meaning_ko: meaningKo } })
}

export function updateMyWord(id, headword, meaningKo) {
  return apiFetch(`/my-words/${id}`, { method: 'PUT', body: { headword, meaning_ko: meaningKo } })
}

export function deleteMyWord(id) {
  return apiFetch(`/my-words/${id}`, { method: 'DELETE' })
}

/** CSV 파일 내용(글자)을 보낸다. { inserted, updated, duplicate_in_file, total_count } */
export function importMyWordsCsv(csvText) {
  return apiFetch('/my-words/import', { method: 'POST', body: { csv_text: csvText } })
}

/** { due_total, items: [{ id, headword, meaning_ko }] } 오늘 공부할 차례인 단어(최대 20개) */
export function getMyWordStudy() {
  return apiFetch('/my-words/study')
}

/** rating: 'dont_know' | 'unsure' | 'know' */
export function reviewMyWord(id, rating) {
  return apiFetch(`/my-words/${id}/review`, { method: 'POST', body: { rating } })
}
