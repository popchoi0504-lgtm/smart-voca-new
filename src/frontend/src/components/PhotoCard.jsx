// 2026-11-06 - smart-voca - 장면 그림 위에 라벨(chip)과 알약 모양 이동 버튼(caption)을 얹은 둥근 카드
// 파일 위치: src/frontend/src/components/PhotoCard.jsx
import { Link } from 'react-router-dom'

function ArrowIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 12L12 4M5.5 4H12v6.5" />
    </svg>
  )
}

/**
 * scene: 그림 부품(<ListeningScene /> 등), chip: 왼쪽 위 라벨, caption/to: 아래 알약 버튼 글자와 이동 주소(없으면 버튼 없음)
 * square: 정사각형 비율, bubble: 그림 위에 띄울 말풍선 { word, meaning }
 */
export default function PhotoCard({ scene, chip, caption, to, square = false, bubble }) {
  return (
    <div className={`photo ${square ? 'photo-square' : ''}`}>
      {scene}
      {chip && <span className="photo-chip">{chip}</span>}
      {bubble && (
        <div className="photo-bubble">
          <strong>{bubble.word}</strong>
          {bubble.meaning}
        </div>
      )}
      {caption && to && (
        <Link className="photo-caption" to={to}>
          {caption}
          <span className="photo-go"><ArrowIcon /></span>
        </Link>
      )}
    </div>
  )
}
