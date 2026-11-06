// 2026-11-04 - smart-voca - 회원가입 화면 (FR-AUTH-01·07)
// 파일 위치: src/frontend/src/pages/SignupPage.jsx
import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'

import { fieldErrorsOf } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import AuthLayout from '../components/AuthLayout'
import FormField from '../components/FormField'
import { TERMS_VERSION } from '../legal/version'

export default function SignupPage() {
  const { user, signUp } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [agree, setAgree] = useState({ age: false, terms: false, privacy: false, marketing: false })
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
      await signUp(email, password, {
        agree_age: agree.age,
        agree_terms: agree.terms,
        agree_privacy: agree.privacy,
        agree_marketing: agree.marketing,
        terms_version: TERMS_VERSION, // 화면이 보여 준 약관 버전: 서버가 현재 버전과 대조한다
      })
    } catch (error) {
      // 입력 형식 오류는 해당 칸 아래에, 그 밖의 오류는 버튼 위에 보여준다.
      // 화면에서는 규칙을 다시 검사하지 않는다: 규칙의 기준은 서버 하나로 두어 어긋나지 않게 하기 위함
      const errors = fieldErrorsOf(error)
      if (Object.keys(errors).length > 0) setFieldErrors(errors)
      else setErrorMessage(error.message)
      setIsSubmitting(false)
    }
  }

  const requiredAgreed = agree.age && agree.terms && agree.privacy
  const allAgreed = requiredAgreed && agree.marketing
  const toggle = (name) => (event) => setAgree({ ...agree, [name]: event.target.checked })
  const toggleAll = (event) => {
    const checked = event.target.checked
    setAgree({ age: checked, terms: checked, privacy: checked, marketing: checked })
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
        <fieldset className="consent">
          <legend>약관 동의</legend>
          <label className="consent-row consent-all">
            <input type="checkbox" checked={allAgreed} onChange={toggleAll} />
            전체 동의 (선택 항목 포함)
          </label>
          <label className="consent-row">
            <input type="checkbox" checked={agree.age} onChange={toggle('age')} />
            <span>(필수) 만 14세 이상입니다.</span>
          </label>
          <label className="consent-row">
            <input type="checkbox" checked={agree.terms} onChange={toggle('terms')} />
            <span>(필수) 이용약관에 동의합니다.<Link to="/terms" target="_blank">보기</Link></span>
          </label>
          <label className="consent-row">
            <input type="checkbox" checked={agree.privacy} onChange={toggle('privacy')} />
            <span>(필수) 개인정보 수집·이용에 동의합니다.<Link to="/privacy" target="_blank">보기</Link></span>
          </label>
          <label className="consent-row">
            <input type="checkbox" checked={agree.marketing} onChange={toggle('marketing')} />
            <span>(선택) 서비스 소식 수신에 동의합니다.</span>
          </label>
          {(fieldErrors.agree_age || fieldErrors.agree_terms || fieldErrors.agree_privacy) && (
            <p className="field-error">필수 항목에 모두 동의해 주세요.</p>
          )}
        </fieldset>
        {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}
        <button className="btn btn-primary" type="submit" disabled={isSubmitting || !requiredAgreed}>
          {isSubmitting ? '가입하는 중…' : '가입하기'}
        </button>
        <p className="form-footer">
          이미 계정이 있으신가요? <Link to="/login">로그인</Link>
        </p>
      </form>
    </AuthLayout>
  )
}
