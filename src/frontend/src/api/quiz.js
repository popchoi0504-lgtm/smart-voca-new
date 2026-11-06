// 2026-11-04 - smart-voca - 복습 퀴즈 문제 목록·힌트·답 제출 API 호출 함수 (인터페이스 정의서 4.4)
// 파일 위치: src/frontend/src/api/quiz.js
import { apiFetch } from './client'

/** 복습 대상 문제 목록. { items, remaining_due_count } — 정답 영단어는 들어 있지 않다. */
export function getQuizQueue(limit = 10) {
  return apiFetch(`/quiz/queue?limit=${limit}`)
}

/** 새 단어를 배운 직후 확인 퀴즈. 내가 배운 단어 번호(최대 10개)를 주면 같은 모양의 { items, remaining_due_count } 를 준다. */
export function getCheckQuiz(wordIds) {
  return apiFetch(`/quiz/check?word_ids=${wordIds.join(',')}`)
}

/** level: 1(철자 섞기) | 2(빈칸) | 3(정답). 서버는 저장하지 않는다. */
export function getHint(wordId, level) {
  return apiFetch(`/quiz/${wordId}/hint`, { method: 'POST', body: { level } })
}

/** maxHintLevel: 이 문제에서 연 가장 높은 힌트 단계(0~3). 3이면 answer 는 null 이어도 된다. */
export function submitAnswer(wordId, answer, maxHintLevel) {
  return apiFetch(`/quiz/${wordId}/answer`, { method: 'POST', body: { answer, max_hint_level: maxHintLevel } })
}
