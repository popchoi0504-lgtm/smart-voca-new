// 2026-11-04 - smart-voca - 플래시카드 화면: 앞면 영단어 → 뒷면 뜻·예문 → 몰랐음/애매함/알았음 (FR-STUDY-02·03·06)
// 파일 위치: src/frontend/src/pages/FlashcardPage.jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { ApiError } from '../api/client'
import { getNewWords, getToday, submitFlashcard } from '../api/study'
import SpeakButton from '../components/SpeakButton'
import { useTeacherTarget } from '../teacher/TeacherContext'

const RATINGS = [
  { value: 'dont_know', label: '몰랐음' },
  { value: 'unsure', label: '애매함' },
  { value: 'know', label: '알았음' },
]

export default function FlashcardPage() {
  const [words, setWords] = useState(null) // 이번 세션의 단어 목록 (null 이면 불러오는 중)
  const [index, setIndex] = useState(0) // 지금 몇 번째 카드인지
  const [isFlipped, setIsFlipped] = useState(false) // 뒷면(뜻)을 보고 있는지
  const [isSending, setIsSending] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [hasMore, setHasMore] = useState(false) // 세션을 마친 뒤 더 배울 새 단어가 남았는지

  useEffect(() => {
    getNewWords(10).then(setWords).catch((error) => setErrorMessage(error.message))
  }, [])

  // 세션을 모두 마치면 오늘 남은 목표를 다시 물어봐서 "이어서 하기" 버튼을 보여줄지 정한다
  const isFinished = words !== null && index >= words.length
  useEffect(() => {
    if (isFinished && words.length > 0) {
      getToday().then((today) => setHasMore(today.new_target_count > 0)).catch(() => setHasMore(false))
    }
  }, [isFinished, words])

  // AI 선생님에게 "지금 보는 단어"를 알려 준다 (세션을 마쳤거나 단어가 없으면 등록하지 않음)
  const currentWord = words && index < words.length ? words[index] : null
  useTeacherTarget(
    currentWord ? { wordId: currentWord.word_id, label: currentWord.headword, context: 'study', ready: true } : null,
  )

  async function handleRate(rating) {
    setErrorMessage('')
    setIsSending(true)
    try {
      await submitFlashcard(words[index].word_id, rating)
    } catch (error) {
      // 이미 학습한 카드(409)는 성공처럼 다음 카드로 넘어간다 (인터페이스 정의서 3.1)
      if (!(error instanceof ApiError && error.code === 'WORD_ALREADY_LEARNED')) {
        setErrorMessage(error.message)
        setIsSending(false)
        return
      }
    }
    setIsSending(false)
    setIsFlipped(false)
    setIndex(index + 1)
  }

  function startNextSession() {
    setWords(null)
    setIndex(0)
    setHasMore(false)
    getNewWords(10).then(setWords).catch((error) => setErrorMessage(error.message))
  }

  if (errorMessage && words === null) {
    return (
      <main className="page">
        <p className="form-error" role="alert">{errorMessage}</p>
        <Link to="/">오늘 할 것으로</Link>
      </main>
    )
  }
  if (words === null) return <main className="page"><p>불러오는 중…</p></main>

  if (words.length === 0) {
    return (
      <main className="page">
        <h1 className="page-title">새 단어</h1>
        <p className="notice">지금 배울 새 단어가 없어요.</p>
        <Link className="btn" to="/">오늘 할 것으로</Link>
      </main>
    )
  }

  if (isFinished) {
    return (
      <main className="page">
        <h1 className="page-title">수고했어요! 🎉</h1>
        <p className="page-subtitle">새 단어 {words.length}개를 배웠어요. 내일 복습 목록에 나와요.</p>
        <div className="button-row">
          {/* 방금 배운 단어를 바로 확인한다. 건너뛰어도 되고, 복습 일정은 바뀌지 않는 연습이다 */}
          <Link className="btn btn-primary" to="/quiz/check" state={{ wordIds: words.map((item) => item.word_id) }}>
            바로 확인 퀴즈
          </Link>
          {hasMore && <button className="btn btn-primary" type="button" onClick={startNextSession}>이어서 더 배우기</button>}
          <Link className="btn" to="/">오늘 할 것으로</Link>
        </div>
      </main>
    )
  }

  const word = words[index]
  return (
    <main className="page">
      <p className="page-subtitle">{index + 1} / {words.length}</p>
      <section className="card flashcard" aria-live="polite">
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

      {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}

      {!isFlipped ? (
        <button className="btn btn-primary btn-block" type="button" onClick={() => setIsFlipped(true)}>
          뜻 보기
        </button>
      ) : (
        <div className="button-row">
          {RATINGS.map((rating) => (
            <button
              key={rating.value}
              className="btn"
              type="button"
              disabled={isSending}
              onClick={() => handleRate(rating.value)}
            >
              {rating.label}
            </button>
          ))}
        </div>
      )}
    </main>
  )
}
