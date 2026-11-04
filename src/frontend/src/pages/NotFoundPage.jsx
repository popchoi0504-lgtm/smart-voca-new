// 2026-11-04 - smart-voca - 없는 주소로 들어왔을 때 보여주는 화면
// 파일 위치: src/frontend/src/pages/NotFoundPage.jsx
import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <main className="page">
      <h1 className="page-title">페이지를 찾을 수 없어요</h1>
      <p className="page-subtitle">주소를 다시 확인해 주세요.</p>
      <Link to="/">처음 화면으로</Link>
    </main>
  )
}
