// 2026-11-06 - smart-voca - 오른쪽 아래 AI 선생님 아이콘과 대화 패널 (FR-AI-01~07)
// 파일 위치: src/frontend/src/teacher/TeacherWidget.jsx
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { ApiError } from '../api/client'
import { askTeacher } from '../api/ai'
import { useTeacher } from './TeacherContext'

const QUICK_BUTTONS = [
  { kind: 'simple', label: '쉽게 설명해줘' },
  { kind: 'compare', label: '비슷한 단어와 차이' },
  { kind: 'example', label: '다른 예문' },
]
const QUESTION_MAX_LENGTH = 200

function TeacherIcon() {
  // 졸업모자 그림(단순한 도형)
  return (
    <svg width="30" height="30" viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <path d="M16 5L3 11l13 6 13-6z" fill="currentColor" />
      <path d="M8 14.5V20c0 2.2 3.6 4 8 4s8-1.8 8-4v-5.5l-8 3.7z" fill="currentColor" opacity="0.8" />
      <path d="M29 11v7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

export default function TeacherWidget() {
  const { target } = useTeacher()
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([]) // { role: me 또는 teacher, text } — 단어가 바뀌면 비운다
  const [questionText, setQuestionText] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState(null) // ApiError 또는 null
  const [limitInfo, setLimitInfo] = useState(null) // { remaining, limit }
  const listEndRef = useRef(null)

  // 다른 단어로 넘어가면 이전 대화는 지운다(단어가 섞이면 헷갈리므로)
  const wordKey = target ? `${target.context}-${target.wordId}` : null
  useEffect(() => {
    setMessages([])
    setError(null)
    setQuestionText('')
  }, [wordKey])

  useEffect(() => {
    listEndRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'end' })
  }, [messages, isSending])

  async function send(kind, label, question) {
    if (isSending || !target?.ready) return
    setError(null)
    setIsSending(true)
    setMessages((previous) => [...previous, { role: 'me', text: label }])
    try {
      const response = await askTeacher({ wordId: target.wordId, kind, context: target.context, question })
      setMessages((previous) => [...previous, { role: 'teacher', text: response.answer }])
      setLimitInfo({ remaining: response.remaining_today, limit: response.daily_limit })
    } catch (caught) {
      setError(caught instanceof ApiError ? caught : new ApiError(0, 'UNKNOWN', '답을 받지 못했어요.'))
      if (caught instanceof ApiError && caught.code === 'AI_LIMIT_REACHED') {
        setLimitInfo((previous) => ({ remaining: 0, limit: previous?.limit }))
      }
    }
    setIsSending(false)
  }

  function handleSubmit(event) {
    event.preventDefault()
    const question = questionText.trim()
    if (!question) return
    setQuestionText('')
    send('ask', question, question)
  }

  return (
    <div className="teacher">
      {isOpen && (
        <section className="teacher-panel" aria-label="AI 선생님">
          <header className="teacher-header">
            <div>
              <strong>AI 선생님</strong>
              {target?.label && <span className="teacher-word">{target.label}</span>}
            </div>
            <button className="teacher-close" type="button" onClick={() => setIsOpen(false)} aria-label="닫기">×</button>
          </header>

          {!target && <p className="teacher-empty">새 단어나 퀴즈 화면에서 단어를 보면서 물어봐 주세요.</p>}
          {target && !target.ready && (
            <p className="teacher-empty">{target.notReadyMessage ?? '지금은 물어볼 수 없어요.'}</p>
          )}

          {target?.ready && (
            <>
              <div className="teacher-messages" aria-live="polite">
                {messages.length === 0 && <p className="teacher-hint">이 단어에 대해 궁금한 걸 골라 보세요.</p>}
                {messages.map((message, index) => (
                  <p key={index} className={`teacher-message teacher-message-${message.role}`}>{message.text}</p>
                ))}
                {isSending && <p className="teacher-message teacher-message-teacher">생각하는 중…</p>}
                <div ref={listEndRef} />
              </div>

              {error && (
                <p className="teacher-error" role="alert">
                  {error.message}{' '}
                  {error.code === 'AI_LIMIT_REACHED' && <Link to="/subscribe">프리미엄 보기</Link>}
                </p>
              )}

              <div className="teacher-quick">
                {QUICK_BUTTONS.map((button) => (
                  <button key={button.kind} type="button" disabled={isSending} onClick={() => send(button.kind, button.label)}>
                    {button.label}
                  </button>
                ))}
              </div>

              <form className="teacher-form" onSubmit={handleSubmit}>
                <input
                  value={questionText}
                  onChange={(event) => setQuestionText(event.target.value)}
                  maxLength={QUESTION_MAX_LENGTH}
                  placeholder="직접 물어보기 (개인정보는 입력하지 마세요)"
                  aria-label="질문 입력"
                  autoComplete="off"
                />
                <button type="submit" disabled={isSending || !questionText.trim()}>보내기</button>
              </form>
              <p className="teacher-footnote">
                AI 설명은 틀릴 수 있어요.
                {limitInfo && limitInfo.limit != null && ` 오늘 ${limitInfo.remaining}/${limitInfo.limit}회 남았어요.`}
              </p>
            </>
          )}
        </section>
      )}

      <button
        className="teacher-fab"
        type="button"
        onClick={() => setIsOpen((previous) => !previous)}
        aria-label={isOpen ? 'AI 선생님 닫기' : 'AI 선생님 열기'}
        aria-expanded={isOpen}
      >
        <TeacherIcon />
        <span className="teacher-fab-text">AI 선생님</span>
      </button>
    </div>
  )
}
