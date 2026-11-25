// 2026-11-06 - smart-voca - 홈·로그인 화면에 쓰는 토익 분위기 사진 4장(듣기·회의·답안지·출장). Unsplash 무료 사진, 출처는 SourceNotice 에 표기
// 파일 위치: src/frontend/src/components/HeroPhotos.jsx
// 사진 파일은 public/photos/ 에 있다(주소는 /photos/파일명). 사진을 바꾸려면 파일을 같은 이름으로 교체하고 SourceNotice 의 작가 이름도 고친다.

export const PHOTO_CREDITS = [
  { name: 'thinhpham', url: 'https://unsplash.com/photos/es0h8aBUNQ8' },
  { name: 'silverkblack', url: 'https://unsplash.com/photos/AIdnnF7oKws' },
  { name: 'nguyendhn', url: 'https://unsplash.com/photos/qDgTQOYk6B8' },
  { name: 'yousefalfuhigi', url: 'https://unsplash.com/photos/bMIlyKZHKMY' },
]

export function ListeningScene() {
  return <img src="photos/listening.jpg" alt="헤드폰을 쓰고 듣고 있는 여성" loading="lazy" />
}

export function MeetingScene() {
  return <img src="photos/meeting.jpg" alt="악수하는 두 사업가" loading="lazy" />
}

export function AnswerSheetScene() {
  return <img src="photos/answer-sheet.jpg" alt="OMR 답안지에 연필로 쓰는 손" loading="lazy" />
}

export function TripScene() {
  return <img src="photos/trip.jpg" alt="공항에서 짐을 든 사람의 실루엣" loading="lazy" />
}
