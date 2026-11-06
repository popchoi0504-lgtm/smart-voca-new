// 2026-11-04 - smart-voca - 회원가입 화면 (FR-AUTH-01·07)
// 파일 위치: src/frontend/src/pages/SignupPage.jsx
import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'

import { fieldErrorsOf } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import AuthLayout from '../components/AuthLayout'
import FormField from '../components/FormField'

export default function SignupPage() {
  const { user, signUp } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fieldErrors, setFieldErrors] = useState({}) // 칸별 오류 { email: '...', password: '...' }
  const [errorMessage, setErrorMessage] = useState('') // 칸에 속하지 않는 오류 (예: 이미 가입된 이메일)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // 가입에 성공하면 서버가 바로 로그인 상태로 만들어 주므로(user 가 채워짐) 첫 화면으로 이동한다
  if (user) return <Navigate to="/" replace />

  async function handleSubmit(event) {
    event.preventDefault()
    setFieldErrors({})
    setErrorMessage('')
    setIsSubmitting(true)
    try {
      await signUp(email, password)
    } catch (error) {
      // 입력 형식 오류는 해당 칸 아래에, 그 밖의 오류는 버튼 위에 보여준다.
      // 화면에서는 규칙을 다시 검사하지 않는다: 규칙의 기준은 서버 하나로 두어 어긋나지 않게 하기 위함
      const errors = fieldErrorsOf(error)
      if (Object.keys(errors).length > 0) setFieldErrors(errors)
      else setErrorMessage(error.message)
      setIsSubmitting(false)
    }
  }

  return (
    <AuthLayout>
      <h1 className="page-title">회원가입</h1>
      <p className="page-subtitle">이메일과 비밀번호만 있으면 시작할 수 있어요</p>
      <form className="card form" onSubmit={handleSubmit} noValidate>
        <FormField
          label="이메일"
          name="email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          error={fieldErrors.email}
          autoComplete="email"
        />
        <FormField
          label="비밀번호"
          name="password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          error={fieldErrors.password}
          hint="8~64자, 영문과 숫자를 각각 1자 이상 포함"
          autoComplete="new-password"
        />
        {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}
        <button className="btn btn-primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? '가입하는 중…' : '가입하기'}
        </button>
        <p className="form-footer">
          이미 계정이 있으신가요? <Link to="/login">로그인</Link>
        </p>
      </form>
    </AuthLayout>
  )
}
