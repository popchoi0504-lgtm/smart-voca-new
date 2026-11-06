// 2026-11-06 - smart-voca - 즐겨찾기 목록 화면: 별표로 모은 단어 보기·해제·다시 학습 시작 (이슈 #22)
// 파일 위치: src/frontend/src/pages/FavoritesPage.jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { getFavorites, removeFavorite } from '../api/favorites'
import FavoriteButton from '../components/FavoriteButton'
import SpeakButton from '../components/SpeakButton'

export default function FavoritesPage() {
  const [list, setList] = useState(null) // null 이면 불러오는 중
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    getFavorites().then(setList).catch((error) => setErrorMessage(error.message))
  }, [])

  // 별표를 끄면 목록에서도 바로 사라진다. 서버가 실패하면 다시 불러와 원래대로 맞춘다.
  async function handleRemove(wordId) {
    setErrorMessage('')
    setList((previous) => ({
      total_count: previous.total_count - 1,
      items: previous.items.filter((item) => item.word_id !== wordId),
    }))
    try {
      await removeFavorite(wordId)
    } catch (error) {
      setErrorMessage(error.message)
      getFavorites().then(setList).catch(() => {})
    }
  }

  if (errorMessage && list === null) return <main className="page"><p className="form-error" role="alert">{errorMessage}</p></main>
  if (list === null) return <main className="page"><p>불러오는 중…</p></main>

  const studyableCount = list.items.filter((item) => !item.is_locked).length
  return (
    <main className="page">
      <h1 className="page-title">즐겨찾기</h1>
      <p className="page-subtitle">별표(★)를 눌러 모은 단어 {list.total_count}개</p>

      {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}

      {studyableCount > 0 && (
        <div className="button-row">
          <Link className="btn btn-primary" to="/favorites/study">즐겨찾기 단어 다시 학습 ({Math.min(studyableCount, 10)}개)</Link>
        </div>
      )}

      {list.items.length === 0 ? (
        <p className="notice">아직 즐겨찾기한 단어가 없어요. 단어를 배우다가 별표(☆)를 눌러 보세요.</p>
      ) : (
        <ul className="learned-list favorite-list" aria-label="즐겨찾기 단어 목록">
          {list.items.map((item) => (
            <li key={item.word_id} className={`learned-item favorite-item${item.is_locked ? ' is-locked' : ''}`}>
              <div className="learned-head">
                <strong className="learned-word">{item.headword}</strong>
                <span className="field-hint">{item.part_of_speech}</span>
                <SpeakButton text={item.headword} />
                <span className="learned-badge">
                  <FavoriteButton isOn onToggle={() => handleRemove(item.word_id)} headword={item.headword} />
                </span>
              </div>
              <p className="learned-meaning">{item.meaning_ko}</p>
              <p className="field-hint">
                {item.favorited_date} 담음{item.is_locked ? ' · 프리미엄이 필요한 단어예요(해제만 가능)' : ''}
              </p>
            </li>
          ))}
        </ul>
      )}
      <div className="button-row">
        <Link className="btn" to="/">오늘 할 것으로</Link>
      </div>
    </main>
  )
}
