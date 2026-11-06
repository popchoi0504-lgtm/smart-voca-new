// 2026-11-05 - smart-voca - 구독 안내·주문·결제 확인·결제 내역 API 호출 함수 (인터페이스 정의서 4.6)
// 파일 위치: src/frontend/src/api/subscription.js
import { apiFetch } from './client'

export function getSubscription() {
  return apiFetch('/subscription')
}

/** 주문을 만든다. 금액은 보내지 않는다: 서버가 정한 금액이 응답으로 온다. */
export function createOrder() {
  return apiFetch('/payments/orders', { method: 'POST', body: { product: 'premium_30d' } })
}

/** 결제 성공 뒤 주소에 붙어 온 값을 서버에 넘겨 결제사 승인 확인을 요청한다. */
export function confirmPayment(paymentKey, orderId, amount) {
  return apiFetch('/payments/confirm', { method: 'POST', body: { payment_key: paymentKey, order_id: orderId, amount } })
}

/** 환불(결제 취소). 조건에 맞지 않으면 서버가 이유를 오류 메시지로 돌려준다. */
export function refundPayment(orderId) {
  return apiFetch(`/payments/${encodeURIComponent(orderId)}/refund`, { method: 'POST' })
}

export async function getPayments(limit = 20) {
  const data = await apiFetch(`/payments?limit=${limit}`)
  return data.items
}
