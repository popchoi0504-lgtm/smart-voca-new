// 2026-11-05 - smart-voca - 학습 기록 화면: 오늘 학습량, 누적, 연속 학습일, 숙련도 분포, 진행 바 (FR-PROG-02~05)
// 파일 위치: src/frontend/src/pages/ProgressPage.jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { getProgressSummary } from '../api/progress'

// 숫자를 0~100 퍼센트로 바꾼다. 전체가 0이면 0 (0 으로 나누기 방지)
function percent(part, whole) {
  return whole > 0 ? Math.round((part / whole) * 100) : 0
}

function streakMessage(streakDays, studiedToday) {
  if (streakDays === 0) return '오늘 학습하면 연속 학습이 시작돼요.'
  if (!studiedToday) return '오늘 학습하면 연속 기록이 이어져요.'
  return '오늘도 학습했어요. 내일도 이어가 봐요!'
}

export default function ProgressPage() {
  const [summary, setSummary] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    getProgressSummary().then(setSummary).catch((error) => setErrorMessage(error.message))
  }, [])

  return (
    <main className="page">
      <h1 className="page-title">학습 기록</h1>
      <p className="page-subtitle">지금까지 배운 내용을 한눈에 봐요.</p>

      {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}
      {!summary && !errorMessage && <p>불러오는 중…</p>}

      {summary && <ProgressContent summary={summary} />}

      <div className="button-row">
        <Link className="btn" to="/">홈으로</Link>
      </div>
    </main>
  )
}

function ProgressContent({ summary }) {
  const { today, total_learned_count: learned, total_word_count: total, current_streak_days: streak, mastery } = summary
  const learnedPercent = percent(learned, total)

  return (
    <>
      <section className="card">
        <div className="streak">
          <span className="streak-number">{streak}</span>
          <span className="streak-unit">일 연속 학습</span>
        </div>
        <p className="hint-text">{streakMessage(streak, today.reviewed_count > 0)}</p>
      </section>

      <section className="card">
        <h2 className="section-title">오늘 ({today.date})</h2>
        <div className="status-row">
          <span>학습한 단어</span>
          <strong>{today.reviewed_count}개</strong>
        </div>
        <div className="status-row">
          <span>그중 새로 배운 단어</span>
          <strong>{today.new_learned_count}개</strong>
        </div>
      </section>

      <section className="card">
        <h2 className="section-title">전체 진행</h2>
        <div className="status-row">
          <span>배운 단어</span>
          <strong>{learned} / {total}개 ({learnedPercent}%)</strong>
        </div>
        <div className="bar" role="progressbar" aria-label="전체 단어 중 배운 비율"
          aria-valuemin={0} aria-valuemax={total} aria-valuenow={learned}>
          <div className="bar-fill bar-fill-learned" style={{ width: `${learnedPercent}%` }} />
        </div>
      </section>

      <section className="card">
        <h2 className="section-title">숙련도</h2>
        <div className="bar" role="img"
          aria-label={`새 단어 ${mastery.new_count}개, 학습 중 ${mastery.learning_count}개, 익숙함 ${mastery.familiar_count}개`}>
          <div className="bar-fill bar-fill-familiar" style={{ width: `${percent(mastery.familiar_count, total)}%` }} />
          <div className="bar-fill bar-fill-learning" style={{ width: `${percent(mastery.learning_count, total)}%` }} />
        </div>
        {/* 색만으로 구분하지 않도록 이름과 숫자를 함께 적는다 */}
        <div className="status-row">
          <span><i className="legend legend-familiar" />익숙함</span>
          <strong>{mastery.familiar_count}개</strong>
        </div>
        <div className="status-row">
          <span><i className="legend legend-learning" />학습 중</span>
          <strong>{mastery.learning_count}개</strong>
        </div>
        <div className="status-row">
          <span><i className="legend legend-new" />새 단어</span>
          <strong>{mastery.new_count}개</strong>
        </div>
        <p className="hint-text">복습 간격이 21일 이상이면 익숙함, 그보다 짧으면 학습 중이에요.</p>
      </section>
    </>
  )
}
