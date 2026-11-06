// 2026-11-04 - smart-voca - 화면 하단 단어 출처·라이선스 표기 (FR-WORD-04, CC BY-SA 4.0 의 "출처 표기" 의무). 2026-11-05 NGSL 추가
// 파일 위치: src/frontend/src/components/SourceNotice.jsx
// 이 부품은 App.jsx 에서 모든 화면 아래에 한 번만 넣는다. (페이지마다 따로 넣으면 빠뜨리기 쉬움)
import { Link } from 'react-router-dom'

import { PHOTO_CREDITS } from './HeroPhotos'

export default function SourceNotice() {
  return (
    <footer className="source-notice">
      단어 목록: Browne, C., Culligan, B. (2013). The TOEIC SERVICE List; Browne, C., Culligan, B., &amp; Phillips, J. (2013). The New General Service List.{' '}
      <a href="https://www.newgeneralservicelist.com" target="_blank" rel="noopener noreferrer">
        newgeneralservicelist.com
      </a>
      , 이용 허락{' '}
      <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.ko" target="_blank" rel="noopener noreferrer">
        CC BY-SA 4.0
      </a>
      . 단어 선별, 뜻, 예문은 본 서비스가 작성했습니다. 사진:{' '}
      {PHOTO_CREDITS.map((credit, index) => (
        <span key={credit.name}>
          {index > 0 && ', '}
          <a href={credit.url} target="_blank" rel="noopener noreferrer">{credit.name}</a>
        </span>
      ))}{' '}
      (Unsplash).
      <span className="legal-links">
        <Link to="/terms">이용약관</Link>
        <Link to="/privacy">개인정보처리방침</Link>
      </span>
    </footer>
  )
}
