// 2026-11-06 - smart-voca - 로그인·회원가입 공통 배치: 왼쪽에 입력 폼, 오른쪽에 토익 장면 그림
// 파일 위치: src/frontend/src/components/AuthLayout.jsx
import { ListeningScene } from './HeroPhotos'

export default function AuthLayout({ children }) {
  return (
    <main className="auth">
      <div className="auth-form">{children}</div>
      <div className="auth-photo" aria-hidden="false">
        <ListeningScene />
        <span className="photo-chip">토익 빈출 단어 2,000개</span>
      </div>
    </main>
  )
}
