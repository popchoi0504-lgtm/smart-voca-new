// 2026-11-04 - smart-voca - 화면 경로(주소별로 어떤 화면을 보여줄지) 정의 (VS-1)
// 파일 위치: src/frontend/src/App.jsx
import { Route, Routes } from 'react-router-dom'

import ProtectedRoute from './components/ProtectedRoute'
import SourceNotice from './components/SourceNotice'
import FlashcardPage from './pages/FlashcardPage'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import SettingsPage from './pages/SettingsPage'
import SignupPage from './pages/SignupPage'
import StatusPage from './pages/StatusPage'

export default function App() {
  return (
    <>
      <Routes>
        {/* 로그인해야 볼 수 있는 화면은 ProtectedRoute 로 감싼다 */}
        <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
        <Route path="/study" element={<ProtectedRoute><FlashcardPage /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/status" element={<StatusPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      {/* 모든 화면 하단에 단어 출처(CC BY-SA 4.0) 표기 */}
      <SourceNotice />
    </>
  )
}
