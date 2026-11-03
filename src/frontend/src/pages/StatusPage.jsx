// 2026-11-03 - smart-voca - 서버·DB 연결 상태를 보여주는 화면 (VS-0 뼈대 확인용, 이후 로그인 화면 등으로 대체)
// 파일 위치: src/frontend/src/pages/StatusPage.jsx
import { useEffect, useState } from 'react'

import { getHealth } from '../api/client'

function StatusRow({ label, value }) {
  const isOk = value === 'ok'
  return (
    <div className="status-row">
      <span>{label}</span>
      <span className={isOk ? 'status-ok' : 'status-error'}>{isOk ? '정상' : '문제 있음'}</span>
    </div>
  )
}

export default function StatusPage() {
  // 화면이 기억하는 값 3개: 서버 응답, 오류 메시지, 불러오는 중인지
  const [health, setHealth] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  // 화면이 처음 나타났을 때 한 번만 서버에 상태를 물어본다 (빈 배열 [] 이 "한 번만"이라는 뜻)
  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((error) => setErrorMessage(error.message))
      .finally(() => setIsLoading(false))
  }, [])

  return (
    <main className="page">
      <h1 className="page-title">smart-voca</h1>
      <p className="page-subtitle">서버 연결 확인 (VS-0)</p>
      <section className="card">
        {isLoading && <p>확인하는 중…</p>}
        {errorMessage && <p className="status-error">{errorMessage}</p>}
        {health && (
          <>
            <StatusRow label="서버" value={health.status === 'ok' || health.status === 'degraded' ? 'ok' : 'error'} />
            <StatusRow label="데이터베이스" value={health.db} />
          </>
        )}
      </section>
    </main>
  )
}
