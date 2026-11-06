// 2026-11-06 - smart-voca - 모든 화면의 바깥 틀: 연회색 바탕 위 큰 흰 패널, 맨 위 상단 메뉴(로고·알약 메뉴·로그아웃)
// 파일 위치: src/frontend/src/components/AppShell.jsx
import { Link, NavLink } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'

const MENU = [
  { to: '/', label: '홈', end: true },
  { to: '/progress', label: '학습 기록' },
  { to: '/subscribe', label: '프리미엄' },
  { to: '/settings', label: '설정' },
]

export default function AppShell({ children }) {
  const { user, signOut } = useAuth()

  return (
    <div className="panel">
      <nav className="topbar" aria-label="주 메뉴">
        <Link className="brand" to="/"><i className="brand-mark" aria-hidden="true" />smart-voca</Link>
        {user && (
          <div className="menu">
            {MENU.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end} className={({ isActive }) => (isActive ? 'on' : undefined)}>
                {item.label}
              </NavLink>
            ))}
          </div>
        )}
        {user ? (
          <button className="pill" type="button" onClick={signOut}>로그아웃</button>
        ) : (
          <Link className="pill" to="/login">로그인</Link>
        )}
      </nav>
      {children}
    </div>
  )
}
