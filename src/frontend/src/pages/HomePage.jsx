// 2026-11-04 - smart-voca - "오늘 할 것" 화면: 복습할 단어 수와 새로 배울 단어 수 (FR-STUDY-01)
// 파일 위치: src/frontend/src/pages/HomePage.jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { getToday } from '../api/study'
import { useAuth } from '../auth/AuthContext'

export default function HomePage() {
  const { user, signOut } = useAuth()
  const [today, setToday] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')

  // 화면을 열 때 한 번 서버에서 오늘 할 것을 가져온다 (돌아올 때마다 새로 계산되므로 이어하기도 된다, DD-4)
  useEffect(() => {
    getToday().then(setToday).catch((error) => setErrorMessage(error.message))
  }, [])

  const planText = user.is_premium
    ? `프리미엄 (${new Date(user.premium_until).toLocaleDateString('ko-KR')} 까지)`
    : '무료'

  return (
    <main className="page">
      <h1 className="page-title">오늘 할 것</h1>
      <p className="page-subtitle">안녕하세요, {user.email} 님 · {planText}</p>

      {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}
      {!today && !errorMessage && <p>불러오는 중…</p>}

      {today && (
        <section className="card">
          <div className="status-row">
            <span>복습할 단어</span>
            <strong>{today.review_due_count}개</strong>
          </div>
          <div className="status-row">
            <span>오늘 더 배울 새 단어</span>
            <strong>{today.new_target_count}개</strong>
          </div>
          <div className="status-row">
            <span>오늘 배운 새 단어 / 목표</span>
            <span>{today.new_learned_today} / {today.daily_new_limit}개</span>
          </div>

          {today.new_target_count > 0 && (
            <Link className="btn btn-primary btn-block" to="/study">
              새 단어 {Math.min(today.new_target_count, 10)}개 배우기
            </Link>
          )}
          {today.new_target_count === 0 && today.new_locked_by_plan && (
            <p className="notice" role="status">
              무료 단어 {today.plan_word_limit}개를 모두 배웠어요. 더 배우려면 프리미엄이 필요해요.{' '}
              <Link to="/subscribe">프리미엄 보기</Link>
            </p>
          )}
          {today.new_target_count === 0 && !today.new_locked_by_plan && (
            <p className="notice" role="status">오늘 새 단어 목표를 채웠어요. 🎉</p>
          )}
          {today.review_due_count > 0 && (
            <Link className="btn btn-primary btn-block" to="/quiz">
              복습 퀴즈 풀기 ({Math.min(today.review_due_count, 10)}개)
            </Link>
          )}
        </section>
      )}

      <div className="button-row">
        <Link className="btn" to="/progress">학습 기록</Link>
        <Link className="btn" to="/subscribe">프리미엄</Link>
        <Link className="btn" to="/settings">설정</Link>
        <button className="btn" type="button" onClick={signOut}>로그아웃</button>
      </div>
    </main>
  )
}
