// 2026-11-04 - smart-voca - 로그인하지 않은 사람을 로그인 화면으로 보내는 문지기 (FR-AUTH-06)
// 파일 위치: src/frontend/src/components/ProtectedRoute.jsx
// 주의: 이것은 사용자를 안내하는 편의 기능일 뿐, 진짜 보호는 서버가 한다. (화면 코드는 사용자가 조작할 수 있으므로)
import { Navigate, useLocation } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'

export default function ProtectedRoute({ children }) {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) return <main className="page"><p>불러오는 중…</p></main>
  // 로그인 후 원래 가려던 화면으로 돌아올 수 있게, 가려던 위치(from)를 같이 넘긴다
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />
  return children
}
