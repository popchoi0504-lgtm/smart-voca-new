// 2026-11-04 - smart-voca - "오늘 할 것" 화면: 복습할 단어 수와 새로 배울 단어 수 (FR-STUDY-01). 2026-11-06 디자인 개편: 큰 제목 + 알약 버튼 + 토익 장면 카드
// 파일 위치: src/frontend/src/pages/HomePage.jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { getToday } from '../api/study'
import { useAuth } from '../auth/AuthContext'
import { AnswerSheetScene, ListeningScene, MeetingScene, TripScene } from '../components/HeroPhotos'
import PhotoCard from '../components/PhotoCard'

function ArrowIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 12L12 4M5.5 4H12v6.5" />
    </svg>
  )
}

// 알약 모양 큰 버튼(오른쪽 끝에 화살표 원)
function PillLink({ to, dark, children }) {
  return (
    <Link className={`cta ${dark ? 'cta-dark' : 'cta-light'}`} to={to}>
      {children}
      <span className="cta-go"><ArrowIcon /></span>
    </Link>
  )
}

export default function HomePage() {
  const { user } = useAuth()
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
    <main className="home">
      <section className="home-left">
        <p className="home-hello">안녕하세요, {user.display_name} 님 · {planText}</p>
        <h1 className="home-title">
          토익 단어를<br />하루 <span>{user.daily_new_limit}개씩</span>,<br />가볍게.
        </h1>

        {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}
        {!today && !errorMessage && <p className="home-lead">불러오는 중…</p>}

        {today && (
          <>
            <p className="home-lead">
              오늘 복습할 단어 <strong>{today.review_due_count}개</strong>, 새로 배울 단어 <strong>{today.new_target_count}개</strong>가 준비돼 있어요.
              오늘 배운 새 단어는 {today.new_learned_today} / {today.daily_new_limit}개예요.
            </p>
            <div className="home-actions">
              {today.new_target_count > 0 && (
                <PillLink to="/study" dark>새 단어 {Math.min(today.new_target_count, 10)}개 배우기</PillLink>
              )}
              {today.review_due_count > 0 && (
                <PillLink to="/quiz" dark={today.new_target_count === 0}>복습 퀴즈 풀기 ({Math.min(today.review_due_count, 10)}개)</PillLink>
              )}
            </div>
            {today.new_target_count === 0 && today.new_locked_by_plan && (
              <p className="notice" role="status">
                무료 단어 {today.plan_word_limit}개를 모두 배웠어요. 더 배우려면 프리미엄이 필요해요.{' '}
                <Link to="/subscribe">프리미엄 보기</Link>
              </p>
            )}
            {today.new_target_count === 0 && !today.new_locked_by_plan && (
              <p className="notice" role="status">오늘 새 단어 목표를 채웠어요. 🎉</p>
            )}
          </>
        )}

        <div className="home-tags" aria-label="서비스 특징">
          <span className="tag tag-mint">{user.is_premium ? '프리미엄 전체 단어' : `무료 ${today?.plan_word_limit ?? 250}개`}</span>
          <span className="tag">단어 2,000개</span>
          <span className="tag">토익 빈출</span>
          <span className="tag">간격 복습</span>
        </div>
      </section>

      {/* 가운데 원형 바로가기: 마우스를 올리면 이름이 보인다 */}
      <nav className="dock" aria-label="바로가기">
        <Link to="/progress" aria-label="학습 기록">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M4 20V10M10 20V4M16 20v-8M22 20H2" /></svg>
          <span className="dock-tip">학습 기록</span>
        </Link>
        <Link to="/subscribe" aria-label="프리미엄">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" /></svg>
          <span className="dock-tip">프리미엄</span>
        </Link>
        <Link to="/settings" aria-label="설정">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3" /><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1" /></svg>
          <span className="dock-tip">설정</span>
        </Link>
      </nav>

      <div className="stage">
        <div className="stage-col">
          <PhotoCard scene={<ListeningScene />} caption="복습 퀴즈 풀기" to="/quiz" />
          <PhotoCard scene={<AnswerSheetScene />} caption="학습 기록 보기" to="/progress" square />
        </div>
        <div className="stage-col stage-col-lower">
          <PhotoCard scene={<MeetingScene />} caption="새 단어 배우기" to="/study" bubble={{ word: 'negotiate', meaning: '협상하다 · 계약 조건을 협상하다' }} />
          <PhotoCard scene={<TripScene />} caption="프리미엄 보기" to="/subscribe" square />
        </div>
      </div>
    </main>
  )
}
