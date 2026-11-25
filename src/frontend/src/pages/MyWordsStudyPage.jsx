// 2026-11-25 - smart-voca - 내 단어 공부 화면: 영단어 → 뜻 확인 → 몰랐음/애매함/알았음 (이슈 #24, 복습 일정은 SM-2)
// 파일 위치: src/frontend/src/pages/MyWordsStudyPage.jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { getMyWordStudy, reviewMyWord } from '../api/myWords'
import SpeakButton from '../components/SpeakButton'

const RATINGS = [
  { value: 'dont_know', label: '몰랐음' },
  { value: 'unsure', label: '애매함' },
  { value: 'know', label: '알았음' },
]

export default function MyWordsStudyPage() {
  const [study, setStudy] = useState(null) // { due_total, items } (null 이면 불러오는 중)
  const [index, setIndex] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  function loadRound() {
    setStudy(null)
    setIndex(0)
    setIsFlipped(false)
    getMyWordStudy().then(setStudy).catch((error) => setErrorMessage(error.message))
  }
  useEffect(loadRound, [])

  async function handleRate(rating) {
    setErrorMessage('')
    setIsSending(true)
    try {
      await reviewMyWord(study.items[index].id, rating)
      setIsFlipped(false)
      setIndex(index + 1)
    } catch (error) {
      setErrorMessage(error.message)
    } finally {
      setIsSending(false)
    }
  }

  if (errorMessage && study === null) {
    return <main className="page"><p className="form-error" role="alert">{errorMessage}</p><Link to="/my-words">내 단어로</Link></main>
  }
  if (study === null) return <main className="page"><p>불러오는 중…</p></main>

  if (study.items.length === 0) {
    return (
      <main className="page">
        <h1 className="page-title">내 단어 공부</h1>
        <p className="notice">오늘 공부할 내 단어가 없어요. 단어를 등록하거나, 복습 날짜가 오면 다시 오세요.</p>
        <div className="button-row">
          <Link className="btn btn-primary" to="/my-words">내 단어 등록하러 가기</Link>
          <Link className="btn" to="/">홈으로</Link>
        </div>
      </main>
    )
  }

  if (index >= study.items.length) {
    const remaining = study.due_total - study.items.length
    return (
      <main className="page">
        <h1 className="page-title">수고했어요! 🎉</h1>
        <p className="page-subtitle">내 단어 {study.items.length}개를 공부했어요. 다음 복습 날짜는 단어마다 자동으로 정해졌어요.</p>
        <div className="button-row">
          {remaining > 0 && <button className="btn btn-primary" type="button" onClick={loadRound}>이어서 공부 (남은 {remaining}개)</button>}
          <Link className="btn" to="/my-words">내 단어 목록</Link>
          <Link className="btn" to="/">홈으로</Link>
        </div>
      </main>
    )
  }

  const word = study.items[index]
  return (
    <main className="page">
      <p className="page-subtitle">{index + 1} / {study.items.length} (오늘 남은 단어 {study.due_total - index}개)</p>
      <section className="card flashcard" aria-live="polite">
        <p className="flashcard-word">{word.headword} <SpeakButton text={word.headword} /></p>
        {isFlipped && <p className="flashcard-meaning">{word.meaning_ko}</p>}
      </section>

      {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}

      {!isFlipped ? (
        <button className="btn btn-primary btn-block" type="button" onClick={() => setIsFlipped(true)}>뜻 보기</button>
      ) : (
        <div className="button-row">
          {RATINGS.map((rating) => (
            <button key={rating.value} className="btn" type="button" disabled={isSending} onClick={() => handleRate(rating.value)}>
              {rating.label}
            </button>
          ))}
        </div>
      )}
    </main>
  )
}
