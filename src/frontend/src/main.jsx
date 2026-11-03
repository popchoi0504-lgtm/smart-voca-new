// 2026-11-03 - smart-voca - React 시작점: index.html 의 #root 에 App 을 그린다
// 파일 위치: src/frontend/src/main.jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import App from './App'
import './styles/tokens.css'
import './styles/app.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
