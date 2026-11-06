// 2026-11-06 - smart-voca - 모든 화면의 바깥 틀: 연회색 바탕 위 큰 흰 패널, 맨 위 상단 메뉴(로고·알약 메뉴·로그아웃)
// 파일 위치: src/frontend/src/components/AppShell.jsx
import { Link, NavLink } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import Avatar from './Avatar'
import { TeacherProvider } from '../teacher/TeacherContext'
import TeacherWidget from '../teacher/TeacherWidget'

const MENU = [
  { to: '/', label: '홈', end: true },
  { to: '/progress', label: '학습 기록' },
  { to: '/subscribe', label: '프리미엄' },
  { to: '/settings', label: '설정' },
]

export default function AppShell({ children }) {
  const { user, signOut } = useAuth()

  return (
    <TeacherProvider>
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
          <div className="topbar-right">
            <Link className="me-chip" to="/settings" aria-label="내 프로필 설정">
              <Avatar name={user.display_name} color={user.avatar_color} size="sm" />
              <span>{user.display_name}</span>
            </Link>
            <button className="pill" type="button" onClick={signOut}>로그아웃</button>
          </div>
        ) : (
          <Link className="pill" to="/login">로그인</Link>
        )}
      </nav>
      {children}
      </div>
      {/* 오른쪽 아래 AI 선생님: 로그인한 화면에만 (FR-AI-01) */}
      {user && <TeacherWidget />}
    </TeacherProvider>
  )
}
