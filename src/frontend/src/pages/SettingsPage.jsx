// 2026-11-04 - smart-voca - 설정 화면: 하루에 배울 새 단어 수 (FR-STUDY-04)
// 파일 위치: src/frontend/src/pages/SettingsPage.jsx
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { fieldErrorsOf } from '../api/client'
import { updateDailyNewLimit } from '../api/study'
import { useAuth } from '../auth/AuthContext'
import FormField from '../components/FormField'

export default function SettingsPage() {
  const { user, setUser } = useAuth()
  const [limitText, setLimitText] = useState(String(user.daily_new_limit))
  const [errorMessage, setErrorMessage] = useState('')
  const [fieldError, setFieldError] = useState('')
  const [savedMessage, setSavedMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setErrorMessage('')
    setFieldError('')
    setSavedMessage('')
    // 입력칸의 값은 글자라서 정수로 바꾼다. 범위(1~50)의 최종 검사는 서버가 한다
    const value = Number(limitText)
    if (limitText.trim() === '' || !Number.isInteger(value)) {
      setFieldError('1~50 사이의 정수를 입력해 주세요.')
      return
    }
    setIsSubmitting(true)
    try {
      setUser(await updateDailyNewLimit(value))
      setSavedMessage('저장했어요.')
    } catch (error) {
      setFieldError(fieldErrorsOf(error).daily_new_limit ?? '')
      if (!fieldErrorsOf(error).daily_new_limit) setErrorMessage(error.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="page">
      <h1 className="page-title">설정</h1>
      <form className="card form" onSubmit={handleSubmit}>
        <FormField
          label="하루에 배울 새 단어 수"
          name="daily_new_limit"
          type="number"
          value={limitText}
          onChange={(event) => setLimitText(event.target.value)}
          error={fieldError}
          hint="1~50개. 한 번에는 최대 10개씩 보여 드려요."
        />
        {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}
        {savedMessage && <p className="status-ok" role="status">{savedMessage}</p>}
        <button className="btn btn-primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? '저장 중…' : '저장'}
        </button>
      </form>
      <p><Link to="/">← 오늘 할 것으로</Link></p>
    </main>
  )
}
