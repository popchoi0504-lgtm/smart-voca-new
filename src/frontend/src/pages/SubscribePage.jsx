// 2026-11-05 - smart-voca - 구독 화면: 요금제 비교, 이용권 만료일, 구매(토스 결제위젯 또는 가짜 결제), 결제 내역 (FR-SUB-01·02·04·05)
// 파일 위치: src/frontend/src/pages/SubscribePage.jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { createOrder, getPayments, getSubscription } from '../api/subscription'
import { loadTossSdk } from '../payments/loadToss'

const STATUS_LABEL = { pending: '결제 대기', paid: '결제 완료', failed: '실패', canceled: '취소' }

function formatDate(isoText) {
  return new Date(isoText).toLocaleDateString('ko-KR')
}

export default function SubscribePage() {
  const [subscription, setSubscription] = useState(null)
  const [payments, setPayments] = useState([])
  const [order, setOrder] = useState(null) // 만든 주문. 있으면 결제 단계 화면을 보여 준다
  const [widgets, setWidgets] = useState(null) // 토스 결제위젯 객체
  const [errorMessage, setErrorMessage] = useState('')
  const [isBusy, setIsBusy] = useState(false)

  useEffect(() => {
    getSubscription().then(setSubscription).catch((error) => setErrorMessage(error.message))
    getPayments(10).then(setPayments).catch(() => {})
  }, [])

  // 구매 버튼: 서버에 주문을 만들고(금액은 서버가 정함), 토스면 결제위젯을 그린다
  async function startPurchase() {
    setErrorMessage('')
    setIsBusy(true)
    try {
      const newOrder = await createOrder()
      setOrder(newOrder)
      if (newOrder.provider === 'toss') {
        const TossPayments = await loadTossSdk()
        const tossWidgets = TossPayments(newOrder.client_key).widgets({ customerKey: newOrder.customer_key })
        await tossWidgets.setAmount({ currency: 'KRW', value: newOrder.amount })
        await Promise.all([
          tossWidgets.renderPaymentMethods({ selector: '#payment-method', variantKey: 'DEFAULT' }),
          tossWidgets.renderAgreement({ selector: '#agreement', variantKey: 'AGREEMENT' }),
        ])
        setWidgets(tossWidgets)
      }
    } catch (error) {
      setOrder(null)
      setErrorMessage(error.message)
    }
    setIsBusy(false)
  }

  // 토스: 결제창을 열고, 끝나면 토스가 successUrl 로 이동시킨다(주소 끝에 paymentKey, orderId, amount 가 붙음)
  async function payWithToss() {
    setErrorMessage('')
    setIsBusy(true)
    try {
      await widgets.requestPayment({
        orderId: order.order_id,
        orderName: order.order_name,
        successUrl: `${window.location.origin}/payment/success`,
        failUrl: `${window.location.origin}/payment/fail`,
      })
    } catch (error) {
      // 구매자가 결제창을 닫은 경우 등
      setErrorMessage(error.message || '결제를 진행하지 못했어요.')
    }
    setIsBusy(false)
  }

  // 가짜 결제: 토스와 같은 모양의 주소로 이동시켜서 이후 흐름(승인 확인)은 똑같이 지나가게 한다
  function payWithFake() {
    const query = new URLSearchParams({ paymentKey: `fake_${order.order_id}`, orderId: order.order_id, amount: String(order.amount) })
    window.location.assign(`/payment/success?${query}`)
  }

  if (!subscription) {
    return (
      <main className="page">
        <h1 className="page-title">프리미엄</h1>
        {errorMessage ? <p className="form-error" role="alert">{errorMessage}</p> : <p>불러오는 중…</p>}
      </main>
    )
  }

  const [freePlan, premiumPlan] = subscription.plans
  const isPremium = subscription.current.plan === 'premium'

  return (
    <main className="page">
      <h1 className="page-title">프리미엄</h1>
      <p className="page-subtitle">
        {isPremium ? `이용권이 ${formatDate(subscription.current.premium_until)} 까지예요.` : '지금은 무료 요금제예요.'}
      </p>

      <section className="plan-grid">
        <div className={`card plan ${!isPremium ? 'plan-current' : ''}`}>
          <h2>{freePlan.name}</h2>
          <p className="plan-price">0원</p>
          <p>단어 {freePlan.word_limit}개까지</p>
        </div>
        <div className={`card plan ${isPremium ? 'plan-current' : ''}`}>
          <h2>{premiumPlan.name}</h2>
          <p className="plan-price">{premiumPlan.price_krw.toLocaleString('ko-KR')}원 / {premiumPlan.pass_days}일</p>
          <p>단어 {premiumPlan.word_limit}개 전체</p>
        </div>
      </section>

      {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}

      {!order && (
        <button className="btn btn-primary btn-block" type="button" onClick={startPurchase} disabled={isBusy}>
          {isBusy ? '준비 중…' : isPremium ? `이용권 ${premiumPlan.pass_days}일 더 구매하기` : `이용권 ${premiumPlan.pass_days}일 구매하기`}
        </button>
      )}

      {order && (
        <section className="card">
          <h2>{order.order_name}</h2>
          <p><strong>{order.amount.toLocaleString('ko-KR')}원</strong></p>
          {order.provider === 'toss' && (
            <>
              <p className="hint-text">테스트 결제예요. 실제로 돈이 빠져나가지 않아요.</p>
              <div id="payment-method" />
              <div id="agreement" />
              <button className="btn btn-primary btn-block" type="button" onClick={payWithToss} disabled={isBusy || !widgets}>
                {widgets ? '결제하기' : '결제 수단을 불러오는 중…'}
              </button>
            </>
          )}
          {order.provider === 'fake' && (
            <>
              <p className="hint-text">가짜 결제예요(개발용). 실제로 돈이 빠져나가지 않아요.</p>
              <button className="btn btn-primary btn-block" type="button" onClick={payWithFake}>가짜 결제로 구매하기</button>
            </>
          )}
        </section>
      )}

      {payments.length > 0 && (
        <section className="card">
          <h2>결제 내역</h2>
          {payments.map((item) => (
            <div className="status-row" key={item.order_id}>
              <span>{formatDate(item.requested_at)} · {item.amount.toLocaleString('ko-KR')}원</span>
              <span>{STATUS_LABEL[item.status] ?? item.status}</span>
            </div>
          ))}
        </section>
      )}

      <div className="button-row">
        <Link className="btn" to="/">처음으로</Link>
      </div>
    </main>
  )
}
