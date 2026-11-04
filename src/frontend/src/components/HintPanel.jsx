// 2026-11-04 - smart-voca - 퀴즈 힌트 패널: 1(철자 섞기) → 2(빈칸) → 3(정답 확인) 순서로만 연다 (FR-HINT-01~05)
// 파일 위치: src/frontend/src/components/HintPanel.jsx

const NEXT_LABELS = {
  1: '힌트 1: 철자 섞기',
  2: '힌트 2: 빈칸 보기',
  3: '정답 확인 (오답이 아니라 "정답 확인"으로 기록돼요)',
}

/**
 * hints: { 1: {...}, 2: {...} } 지금까지 받은 힌트 (서버 응답 그대로)
 * nextLevel: 다음에 열 수 있는 단계(1~3), 더 열 게 없으면 null
 * onOpen(level): 힌트 열기 요청
 */
export default function HintPanel({ hints, nextLevel, onOpen, disabled }) {
  return (
    <section className="hint-panel" aria-label="힌트">
      {hints[1] && (
        <p className="hint-line">
          {hints[1].skipped
            ? '이 단어는 글자가 적어 섞기 힌트가 없어요.'
            : <>섞인 철자: <strong className="hint-letters">{hints[1].scrambled}</strong></>}
        </p>
      )}
      {hints[2] && (
        <p className="hint-line">
          빈칸: <strong className="hint-letters">{hints[2].masked.join(' ')}</strong>
        </p>
      )}
      {hints[3] && (
        <p className="hint-line">
          정답: <strong className="hint-letters">{hints[3].answer}</strong>
        </p>
      )}
      {nextLevel && (
        <button className="btn" type="button" disabled={disabled} onClick={() => onOpen(nextLevel)}>
          {NEXT_LABELS[nextLevel]}
        </button>
      )}
    </section>
  )
}
