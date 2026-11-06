// 2026-11-04 - smart-voca - 복습 퀴즈 화면: 뜻·빈칸 예문 → 영단어 입력 → 오답이면 재시도/힌트, 정답 확인은 별도 기록 (FR-QUIZ-01~03, FR-HINT-01~05)
// 파일 위치: src/frontend/src/pages/QuizPage.jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { getHint, getQuizQueue, submitAnswer } from '../api/quiz'
import HintPanel from '../components/HintPanel'
import { useTeacherTarget } from '../teacher/TeacherContext'

export default function QuizPage() {
  const [queue, setQueue] = useState(null) // { items, remaining_due_count }, null 이면 불러오는 중
  const [index, setIndex] = useState(0)
  const [answerText, setAnswerText] = useState('')
  const [hints, setHints] = useState({}) // 이 문제에서 받은 힌트 { 단계: 응답 }
  const [maxHint, setMaxHint] = useState(0) // 이 문제에서 연 가장 높은 힌트 단계
  const [result, setResult] = useState(null) // 마지막 제출 결과. correct/revealed 면 문제가 끝난 상태
  const [isSending, setIsSending] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [summary, setSummary] = useState({ correct: 0, revealed: 0 })

  function loadQueue() {
    setQueue(null)
    setIndex(0)
    resetQuestion()
    getQuizQueue(10).then(setQueue).catch((error) => setErrorMessage(error.message))
  }

  useEffect(loadQueue, [])

  function resetQuestion() {
    setAnswerText('')
    setHints({})
    setMaxHint(0)
    setResult(null)
    setErrorMessage('')
  }

  const isFinished = queue !== null && index >= queue.items.length
  const isSolved = result !== null && result.result !== 'wrong'

  // AI 선생님: 단어가 곧 정답이라 문제를 맞히거나 "정답 확인"을 한 뒤에만 물어볼 수 있다 (FR-AI-03)
  const currentQuestion = queue && index < queue.items.length ? queue.items[index] : null
  useTeacherTarget(
    currentQuestion
      ? {
          wordId: currentQuestion.word_id,
          label: isSolved ? result.correct_answer : '이 문제',
          context: 'quiz',
          ready: isSolved,
          notReadyMessage: '문제를 푼 뒤에 물어볼 수 있어요. 막히면 힌트를 써 보세요.',
        }
      : null,
  )

  async function sendAnswer(text, level) {
    setErrorMessage('')
    setIsSending(true)
    try {
      const response = await submitAnswer(queue.items[index].word_id, text, level)
      setResult(response)
      if (response.result !== 'wrong') {
        setSummary((previous) => ({ ...previous, [response.result]: previous[response.result] + 1 }))
      }
    } catch (error) {
      setErrorMessage(error.message)
    }
    setIsSending(false)
  }

  function handleSubmit(event) {
    event.preventDefault()
    if (!answerText.trim() || isSolved) return
    sendAnswer(answerText, maxHint)
  }

  async function handleOpenHint(level) {
    setErrorMessage('')
    setIsSending(true)
    try {
      const hint = await getHint(queue.items[index].word_id, level)
      setHints((previous) => ({ ...previous, [level]: hint }))
      setMaxHint(level)
      setIsSending(false)
      // 정답 확인(3단계)은 바로 "정답 확인"으로 기록한다: 보고 나서 맞힌 것으로 처리되면 안 되기 때문
      if (level === 3) await sendAnswer(null, 3)
      return
    } catch (error) {
      setErrorMessage(error.message)
    }
    setIsSending(false)
  }

  function handleNext() {
    resetQuestion()
    setIndex(index + 1)
  }

  if (errorMessage && queue === null) {
    return (
      <main className="page">
        <p className="form-error" role="alert">{errorMessage}</p>
        <Link to="/">오늘 할 것으로</Link>
      </main>
    )
  }
  if (queue === null) return <main className="page"><p>불러오는 중…</p></main>

  if (queue.items.length === 0) {
    return (
      <main className="page">
        <h1 className="page-title">복습 퀴즈</h1>
        <p className="notice">지금 복습할 단어가 없어요. 🎉</p>
        <Link className="btn" to="/">오늘 할 것으로</Link>
      </main>
    )
  }

  if (isFinished) {
    return (
      <main className="page">
        <h1 className="page-title">복습 끝! 🎉</h1>
        <p className="page-subtitle">
          정답 {summary.correct}개 · 정답 확인 {summary.revealed}개 · 오답 후 다시 맞힌 것도 정답에 포함돼요.
        </p>
        <div className="button-row">
          {queue.remaining_due_count > queue.items.length && (
            <button className="btn btn-primary" type="button" onClick={loadQueue}>남은 복습 이어서 하기</button>
          )}
          <Link className="btn" to="/">오늘 할 것으로</Link>
        </div>
      </main>
    )
  }

  const question = queue.items[index]
  const nextLevel = maxHint >= 3 ? null : maxHint + 1
  return (
    <main className="page">
      <p className="page-subtitle">{index + 1} / {queue.items.length}</p>
      <section className="card quiz-card" aria-live="polite">
        <p className="field-hint">{question.part_of_speech} · {question.letter_count}글자</p>
        <p className="flashcard-meaning">{question.meaning_ko}</p>
        {question.example_masked && <p className="flashcard-example">{question.example_masked}</p>}
      </section>

      {!isSolved && (
        <form className="quiz-form" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="quiz-answer">영단어를 입력하세요</label>
            <input
              id="quiz-answer"
              value={answerText}
              onChange={(event) => setAnswerText(event.target.value)}
              autoComplete="off"
              autoCapitalize="none"
              autoFocus
            />
          </div>
          <button className="btn btn-primary btn-block" type="submit" disabled={isSending || !answerText.trim()}>
            확인
          </button>
        </form>
      )}

      {result && result.result === 'wrong' && (
        <p className="form-error" role="status">
          {result.practice
            ? '아직 아니에요. (오늘 이미 기록돼서 연습으로 처리돼요) 다시 시도하거나 힌트를 써 보세요.'
            : '틀렸어요. 다시 시도하거나 힌트를 써 보세요.'}
        </p>
      )}
      {isSolved && (
        <div className="notice" role="status">
          <p>
            {result.result === 'correct' ? '정답이에요! ' : '정답을 확인했어요. '}
            <strong className="hint-letters">{result.correct_answer}</strong>
          </p>
          {result.practice ? (
            <p className="field-hint">오늘 이미 기록된 단어라 복습 일정은 바뀌지 않았어요(연습).</p>
          ) : (
            <p className="field-hint">다음 복습: {result.next_review_date} ({result.interval_days}일 뒤)</p>
          )}
        </div>
      )}

      {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}

      {!isSolved && (
        <HintPanel hints={hints} nextLevel={nextLevel} onOpen={handleOpenHint} disabled={isSending} />
      )}
      {isSolved && (
        <button className="btn btn-primary btn-block" type="button" onClick={handleNext}>
          {index + 1 < queue.items.length ? '다음 문제' : '마치기'}
        </button>
      )}
    </main>
  )
}
