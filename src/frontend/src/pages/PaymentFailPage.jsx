// 2026-11-05 - smart-voca - 결제 실패 페이지: 토스가 failUrl 로 보낸 오류 코드·메시지를 안내한다 (FR-SUB-06)
// 파일 위치: src/frontend/src/pages/PaymentFailPage.jsx
import { Link, useSearchParams } from 'react-router-dom'

export default function PaymentFailPage() {
  const [params] = useSearchParams()
  const code = params.get('code')
  const canceled = code === 'PAY_PROCESS_CANCELED' // 구매자가 직접 닫음

  return (
    <main className="page">
      <h1 className="page-title">{canceled ? '결제를 취소했어요' : '결제하지 못했어요'}</h1>
      <section className="card">
        <p>{canceled ? '결제가 진행되지 않았고 이용권도 바뀌지 않았어요.' : (params.get('message') ?? '결제가 완료되지 않았어요.')}</p>
        {!canceled && code && <p className="hint-text">오류 코드: {code}</p>}
        <Link className="btn btn-primary btn-block" to="/subscribe">다시 시도하기</Link>
      </section>
    </main>
  )
}
