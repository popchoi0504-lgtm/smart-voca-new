// 2026-11-04 - smart-voca - 로그인 후 첫 화면 (VS-1: 로그인 확인용. VS-3 에서 "오늘 할 것" 화면으로 바뀐다)
// 파일 위치: src/frontend/src/pages/HomePage.jsx
import { useAuth } from '../auth/AuthContext'

export default function HomePage() {
  const { user, signOut } = useAuth()

  // 이용권이 있으면 만료일을 한국어 날짜로 보여준다 (서버가 한국 시간대로 내려 준다)
  const planText = user.is_premium
    ? `프리미엄 (${new Date(user.premium_until).toLocaleDateString('ko-KR')} 까지)`
    : '무료'

  return (
    <main className="page">
      <h1 className="page-title">smart-voca</h1>
      <p className="page-subtitle">안녕하세요, {user.email} 님</p>
      <section className="card">
        <div className="status-row">
          <span>요금제</span>
          <span>{planText}</span>
        </div>
        <div className="status-row">
          <span>하루 새 단어</span>
          <span>{user.daily_new_limit}개</span>
        </div>
        <p className="page-subtitle">학습 기능은 다음 단계에서 이 화면에 들어옵니다.</p>
        <button className="btn" type="button" onClick={signOut}>
          로그아웃
        </button>
      </section>
    </main>
  )
}
