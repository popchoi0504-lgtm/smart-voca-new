// 2026-11-06 - smart-voca - 별표가 켜진 단어 번호 모음을 불러오고 켜기/끄기를 처리하는 훅 (이슈 #22)
// 파일 위치: src/frontend/src/favorites/useFavoriteIds.js
import { useCallback, useEffect, useState } from 'react'

import { addFavorite, getFavorites, removeFavorite } from '../api/favorites'

/**
 * 화면에서 별표 상태를 쓰기 위한 도구.
 * - isFavorite(wordId): 별표가 켜져 있는지
 * - toggle(wordId): 켜져 있으면 끄고, 꺼져 있으면 켠다. 화면은 먼저 바꾸고(빠른 반응), 서버가 실패하면 되돌린다.
 * - errorMessage: 마지막 실패 메시지 (예: 무료 범위 밖 단어)
 */
export default function useFavoriteIds() {
  const [ids, setIds] = useState(() => new Set())
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    // 목록을 못 불러와도 학습은 계속할 수 있어야 하므로 조용히 빈 상태로 둔다
    getFavorites().then((data) => setIds(new Set(data.items.map((item) => item.word_id)))).catch(() => {})
  }, [])

  const isFavorite = useCallback((wordId) => ids.has(wordId), [ids])

  const toggle = useCallback(
    async (wordId) => {
      const wasOn = ids.has(wordId)
      const apply = (on) =>
        setIds((previous) => {
          const next = new Set(previous)
          if (on) next.add(wordId)
          else next.delete(wordId)
          return next
        })
      setErrorMessage('')
      apply(!wasOn)
      try {
        if (wasOn) await removeFavorite(wordId)
        else await addFavorite(wordId)
      } catch (error) {
        apply(wasOn) // 실패하면 원래대로
        setErrorMessage(error.message)
      }
    },
    [ids],
  )

  return { isFavorite, toggle, errorMessage }
}
