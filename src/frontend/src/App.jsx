// 2026-11-04 - smart-voca - 화면 경로(주소별로 어떤 화면을 보여줄지) 정의 (VS-1)
// 파일 위치: src/frontend/src/App.jsx
import { Route, Routes } from 'react-router-dom'

import ProtectedRoute from './components/ProtectedRoute'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import SignupPage from './pages/SignupPage'
import StatusPage from './pages/StatusPage'

export default function App() {
  return (
    <Routes>
      {/* 로그인해야 볼 수 있는 화면은 ProtectedRoute 로 감싼다 */}
      <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/status" element={<StatusPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
