// 2026-11-06 - smart-voca - 즐겨찾기 다시 학습 화면: 별표 단어를 카드로 넘겨 본다. 복습 일정에는 영향 없는 연습 (이슈 #22)
// 파일 위치: src/frontend/src/pages/FavoriteStudyPage.jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { getFavoriteStudyWords } from '../api/favorites'
import FavoriteButton from '../components/FavoriteButton'
import SpeakButton from '../components/SpeakButton'
import useFavoriteIds from '../favorites/useFavoriteIds'

export default function FavoriteStudyPage() {
  const [data, setData] = useState(null) // { items, total_available }, null 이면 불러오는 중
  const [index, setIndex] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const favorites = useFavoriteIds()

  function load() {
    setData(null)
    setIndex(0)
    setIsFlipped(false)
    getFavoriteStudyWords(10).then(setData).catch((error) => setErrorMessage(error.message))
  }
  useEffect(load, [])

  if (errorMessage && data === null) {
    return (
      <main className="page">
        <p className="form-error" role="alert">{errorMessage}</p>
        <Link to="/favorites">즐겨찾기로</Link>
      </main>
    )
  }
  if (data === null) return <main className="page"><p>불러오는 중…</p></main>

  if (data.items.length === 0) {
    return (
      <main className="page">
        <h1 className="page-title">즐겨찾기 학습</h1>
        <p className="notice">다시 학습할 즐겨찾기 단어가 없어요.</p>
        <Link className="btn" to="/favorites">즐겨찾기로</Link>
      </main>
    )
  }

  if (index >= data.items.length) {
    return (
      <main className="page">
        <h1 className="page-title">수고했어요! ⭐</h1>
        <p className="page-subtitle">즐겨찾기 단어 {data.items.length}개를 다시 봤어요. (연습이라 복습 일정은 그대로예요)</p>
        <div className="button-row">
          <button className="btn btn-primary" type="button" onClick={load}>한 번 더 (무작위)</button>
          <Link className="btn" to="/favorites">즐겨찾기로</Link>
        </div>
      </main>
    )
  }

  const word = data.items[index]
  return (
    <main className="page">
      <p className="page-subtitle">
        {index + 1} / {data.items.length} · 연습이라 복습 일정은 바뀌지 않아요
      </p>
      <section className="card flashcard" aria-live="polite">
        <span className="card-star">
          <FavoriteButton isOn={favorites.isFavorite(word.word_id)} onToggle={() => favorites.toggle(word.word_id)} headword={word.headword} />
        </span>
        <p className="flashcard-word">
          {word.headword} <SpeakButton text={word.headword} />
        </p>
        <p className="field-hint">{word.part_of_speech}</p>
        {isFlipped && (
          <>
            <p className="flashcard-meaning">{word.meaning_ko}</p>
            <p className="flashcard-example">
              {word.example_en} <SpeakButton text={word.example_en} label="예문 듣기" />
            </p>
            <p className="field-hint">{word.example_ko}</p>
          </>
        )}
      </section>

      {favorites.errorMessage && <p className="form-error" role="alert">{favorites.errorMessage}</p>}

      {!isFlipped ? (
        <button className="btn btn-primary btn-block" type="button" onClick={() => setIsFlipped(true)}>뜻 보기</button>
      ) : (
        <button
          className="btn btn-primary btn-block"
          type="button"
          onClick={() => { setIsFlipped(false); setIndex(index + 1) }}
        >
          {index + 1 < data.items.length ? '다음 카드' : '마치기'}
        </button>
      )}
    </main>
  )
}
