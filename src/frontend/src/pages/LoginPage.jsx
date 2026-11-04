// 2026-11-04 - smart-voca - 로그인 화면 (FR-AUTH-02)
// 파일 위치: src/frontend/src/pages/LoginPage.jsx
import { useState } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import FormField from '../components/FormField'

export default function LoginPage() {
  const { user, signIn } = useAuth()
  const location = useLocation()
  // 로그인이 필요한 화면에서 넘어왔다면 그 화면으로, 아니면 첫 화면으로 돌려보낸다
  const redirectTo = location.state?.from?.pathname ?? '/'

  // 입력칸의 값은 React 가 기억한다(useState). 글자를 칠 때마다 이 값이 바뀌고 화면이 다시 그려진다.
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // 이미 로그인한 상태이거나, 방금 로그인에 성공해 user 가 채워지면 자동으로 이동한다
  if (user) return <Navigate to={redirectTo} replace />

  async function handleSubmit(event) {
    event.preventDefault() // 폼의 기본 동작(페이지 새로고침)을 막는다
    setErrorMessage('')
    setIsSubmitting(true)
    try {
      await signIn(email, password)
    } catch (error) {
      setErrorMessage(error.message)
      setIsSubmitting(false)
    }
  }

  return (
    <main className="page">
      <h1 className="page-title">로그인</h1>
      <p className="page-subtitle">smart-voca 에 오신 것을 환영합니다</p>
      <form className="card form" onSubmit={handleSubmit}>
        <FormField
          label="이메일"
          name="email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          autoComplete="email"
        />
        <FormField
          label="비밀번호"
          name="password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
        />
        {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}
        <button className="btn btn-primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? '로그인 중…' : '로그인'}
        </button>
        <p className="form-footer">
          계정이 없으신가요? <Link to="/signup">회원가입</Link>
        </p>
      </form>
    </main>
  )
}
