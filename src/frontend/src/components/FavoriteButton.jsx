// 2026-11-06 - smart-voca - 즐겨찾기 별표 버튼: 눌러서 켜고 끈다 (이슈 #22)
// 파일 위치: src/frontend/src/components/FavoriteButton.jsx

export default function FavoriteButton({ isOn, onToggle, headword }) {
  const label = isOn ? '즐겨찾기 해제' : '즐겨찾기에 담기'
  return (
    <button
      className={`star-btn${isOn ? ' is-on' : ''}`}
      type="button"
      aria-pressed={isOn}
      aria-label={headword ? `${label}: ${headword}` : label}
      title={label}
      onClick={onToggle}
    >
      <span aria-hidden="true">{isOn ? '★' : '☆'}</span>
    </button>
  )
}
