// 2026-11-05 - smart-voca - 결제 성공 페이지: 주소에 붙어 온 값을 서버에 넘겨 승인 확인을 받고 이용권 만료일을 보여 준다 (FR-SUB-03·06)
// 파일 위치: src/frontend/src/pages/PaymentSuccessPage.jsx
// 주의: 이 화면에 왔다고 해서 결제가 끝난 게 아니다. 서버가 결제사에 확인해 준 뒤에만 이용권이 생긴다.
import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { getMe } from '../api/auth'
import { confirmPayment } from '../api/subscription'
import { useAuth } from '../auth/AuthContext'

export default function PaymentSuccessPage() {
  const [params] = useSearchParams()
  const { setUser } = useAuth()
  const [result, setResult] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')
  const alreadyRequested = useRef(false)

  useEffect(() => {
    // 개발 모드에서는 효과가 두 번 실행될 수 있어, 한 번만 요청하게 막는다 (서버도 중복 요청을 안전하게 처리하지만 이중 장치)
    if (alreadyRequested.current) return
    alreadyRequested.current = true

    const paymentKey = params.get('paymentKey')
    const orderId = params.get('orderId')
    const amount = Number(params.get('amount'))
    if (!paymentKey || !orderId || !Number.isInteger(amount)) {
      setErrorMessage('결제 정보가 올바르지 않아요.')
      return
    }
    confirmPayment(paymentKey, orderId, amount)
      .then(async (response) => {
        setResult(response)
        setUser(await getMe()) // 홈 화면의 요금제 표시도 최신으로
      })
      .catch((error) => setErrorMessage(error.message))
  }, [params, setUser])

  return (
    <main className="page">
      <h1 className="page-title">결제 확인</h1>
      {!result && !errorMessage && <p>결제를 확인하는 중이에요…</p>}
      {errorMessage && (
        <>
          <p className="form-error" role="alert">{errorMessage}</p>
          <Link className="btn btn-block" to="/subscribe">구독 화면으로</Link>
        </>
      )}
      {result && (
        <section className="card">
          <p className="status-ok" role="status">
            {result.already_processed ? '이미 처리된 결제예요.' : '결제가 완료됐어요. 🎉'}
          </p>
          <div className="status-row">
            <span>결제 금액</span>
            <strong>{result.payment.amount.toLocaleString('ko-KR')}원</strong>
          </div>
          <div className="status-row">
            <span>이용권 만료일</span>
            <strong>{new Date(result.premium_until).toLocaleDateString('ko-KR')}</strong>
          </div>
          <Link className="btn btn-primary btn-block" to="/">학습하러 가기</Link>
        </section>
      )}
    </main>
  )
}
