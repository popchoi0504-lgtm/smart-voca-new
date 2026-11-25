// 2026-11-04 - smart-voca - React 시작점: 주소 처리(HashRouter)와 로그인 상태(AuthProvider)로 App 을 감싼다
// 파일 위치: src/frontend/src/main.jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter } from 'react-router-dom'

import App from './App'
import { AuthProvider } from './auth/AuthContext'
import './styles/tokens.css'
import './styles/app.css'
import './styles/home.css'
import './styles/profile.css'
import './styles/legal.css'
import './styles/teacher.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <HashRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </HashRouter>
  </StrictMode>,
)
