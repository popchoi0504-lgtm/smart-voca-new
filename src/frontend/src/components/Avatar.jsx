// 2026-11-06 - smart-voca - 이니셜 아바타: 표시 이름의 첫 글자를 색 원 안에 보여 준다 (FR-PROFILE-02)
// 파일 위치: src/frontend/src/components/Avatar.jsx

// 서버가 정한 색 이름 6종 (색값은 profile.css 의 .avatar-색이름)
export const AVATAR_COLORS = [
  { value: 'mint', label: '민트' },
  { value: 'lavender', label: '라벤더' },
  { value: 'yellow', label: '노랑' },
  { value: 'pink', label: '분홍' },
  { value: 'sky', label: '하늘' },
  { value: 'orange', label: '주황' },
]

export default function Avatar({ name, color, size = 'md' }) {
  // Array.from: 이모지처럼 두 칸을 차지하는 글자도 한 글자로 센다
  const initial = (Array.from(name ?? '')[0] ?? '?').toUpperCase()
  return (
    <span className={`avatar avatar-${size} avatar-${color}`} aria-hidden="true">
      {initial}
    </span>
  )
}
