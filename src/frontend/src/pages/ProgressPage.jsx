// 2026-11-05 - smart-voca - 학습 기록 화면: 오늘 학습량, 누적, 연속 학습일, 숙련도 분포, 진행 바 (FR-PROG-02~05)
// 파일 위치: src/frontend/src/pages/ProgressPage.jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { getLearnedWords, getProgressCalendar, getProgressSummary } from '../api/progress'
import SpeakButton from '../components/SpeakButton'

// 숫자를 0~100 퍼센트로 바꾼다. 전체가 0이면 0 (0 으로 나누기 방지)
function percent(part, whole) {
  return whole > 0 ? Math.round((part / whole) * 100) : 0
}

function streakMessage(streakDays, studiedToday) {
  if (streakDays === 0) return '오늘 학습하면 연속 학습이 시작돼요.'
  if (!studiedToday) return '오늘 학습하면 연속 기록이 이어져요.'
  return '오늘도 학습했어요. 내일도 이어가 봐요!'
}

export default function ProgressPage() {
  const [summary, setSummary] = useState(null)
  const [calendar, setCalendar] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    getProgressSummary().then(setSummary).catch((error) => setErrorMessage(error.message))
    // 달력은 없어도 나머지 화면이 동작해야 하므로 실패해도 오류를 띄우지 않고 그 카드만 숨긴다
    getProgressCalendar(84).then(setCalendar).catch(() => {})
  }, [])

  return (
    <main className="page">
      <h1 className="page-title">학습 기록</h1>
      <p className="page-subtitle">지금까지 배운 내용을 한눈에 봐요.</p>

      {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}
      {!summary && !errorMessage && <p>불러오는 중…</p>}

      {summary && <ProgressContent summary={summary} calendar={calendar} />}

      <div className="button-row">
        <Link className="btn" to="/">홈으로</Link>
      </div>
    </main>
  )
}

function ProgressContent({ summary, calendar }) {
  const { today, total_learned_count: learned, total_word_count: total, current_streak_days: streak, mastery } = summary
  const learnedPercent = percent(learned, total)
  const [isListOpen, setIsListOpen] = useState(false)

  return (
    <>
      <section className="card">
        <div className="streak">
          <span className="streak-number">{streak}</span>
          <span className="streak-unit">일 연속 학습</span>
        </div>
        <p className="hint-text">{streakMessage(streak, today.reviewed_count > 0)}</p>
        {calendar && <WeekDots calendar={calendar} />}
      </section>

      {calendar && <HeatmapCard calendar={calendar} />}

      <section className="card">
        <h2 className="section-title">오늘 ({today.date})</h2>
        <div className="status-row">
          <span>학습한 단어</span>
          <strong>{today.reviewed_count}개</strong>
        </div>
        <div className="status-row">
          <span>그중 새로 배운 단어</span>
          <strong>{today.new_learned_count}개</strong>
        </div>
      </section>

      <section className="card">
        <h2 className="section-title">전체 진행</h2>
        {/* 눌러서 펼치면 지금까지 배운 단어 목록이 나온다 */}
        <button className="status-row status-row-button" type="button" aria-expanded={isListOpen}
          aria-controls="learned-words" onClick={() => setIsListOpen(!isListOpen)}>
          <span>배운 단어 {isListOpen ? '▲' : '▼'}</span>
          <strong>{learned} / {total}개 ({learnedPercent}%)</strong>
        </button>
        <div className="bar" role="progressbar" aria-label="전체 단어 중 배운 비율"
          aria-valuemin={0} aria-valuemax={total} aria-valuenow={learned}>
          <div className="bar-fill bar-fill-learned" style={{ width: `${learnedPercent}%` }} />
        </div>
        {isListOpen && <LearnedWordList />}
      </section>

      <section className="card">
        <h2 className="section-title">숙련도</h2>
        <div className="bar" role="img"
          aria-label={`새 단어 ${mastery.new_count}개, 학습 중 ${mastery.learning_count}개, 익숙함 ${mastery.familiar_count}개`}>
          <div className="bar-fill bar-fill-familiar" style={{ width: `${percent(mastery.familiar_count, total)}%` }} />
          <div className="bar-fill bar-fill-learning" style={{ width: `${percent(mastery.learning_count, total)}%` }} />
        </div>
        {/* 색만으로 구분하지 않도록 이름과 숫자를 함께 적는다 */}
        <div className="status-row">
          <span><i className="legend legend-familiar" />익숙함</span>
          <strong>{mastery.familiar_count}개</strong>
        </div>
        <div className="status-row">
          <span><i className="legend legend-learning" />학습 중</span>
          <strong>{mastery.learning_count}개</strong>
        </div>
        <div className="status-row">
          <span><i className="legend legend-new" />새 단어</span>
          <strong>{mastery.new_count}개</strong>
        </div>
        <p className="hint-text">복습 간격이 21일 이상이면 익숙함, 그보다 짧으면 학습 중이에요.</p>
      </section>
    </>
  )
}

const WEEKDAY_LABELS = ['월', '화', '수', '목', '금', '토', '일']
const DAY_MS = 24 * 60 * 60 * 1000

// "YYYY-MM-DD" 를 시간대 영향 없이 날짜 숫자로 다룬다(UTC 자정 기준 밀리초)
function dayNumber(isoDate) {
  return Date.parse(`${isoDate}T00:00:00Z`) / DAY_MS
}

function formatDayNumber(number) {
  return new Date(number * DAY_MS).toISOString().slice(0, 10)
}

// 학습량(단어 수)을 색 진하기 단계 0~3 으로 바꾼다
function heatLevel(count) {
  if (count <= 0) return 0
  if (count < 10) return 1
  if (count < 20) return 2
  return 3
}

// 이번 주(월~일) 학습 여부를 동그라미로 보여 준다
function WeekDots({ calendar }) {
  const today = dayNumber(calendar.end_date)
  const mondayOffset = (new Date(today * DAY_MS).getUTCDay() + 6) % 7 // 월요일=0
  const monday = today - mondayOffset
  const studied = new Set(calendar.days.map((day) => day.date))
  return (
    <div className="week-dots" aria-label="이번 주 학습 여부">
      {WEEKDAY_LABELS.map((label, index) => {
        const iso = formatDayNumber(monday + index)
        const isStudied = studied.has(iso)
        const isFuture = monday + index > today
        return (
          <span key={label} className={`week-dot${isStudied ? ' week-dot-on' : ''}${isFuture ? ' week-dot-future' : ''}`}
            title={`${iso} ${isStudied ? '학습함' : isFuture ? '' : '학습 안 함'}`}>
            {label}
          </span>
        )
      })}
    </div>
  )
}

// 최근 12주를 주 단위 열로 그린 잔디. 맨 위 행이 월요일이다
function HeatmapCard({ calendar }) {
  const today = dayNumber(calendar.end_date)
  const start = dayNumber(calendar.start_date)
  const counts = new Map(calendar.days.map((day) => [day.date, day.count]))
  const firstMonday = start - ((new Date(start * DAY_MS).getUTCDay() + 6) % 7)
  const cells = []
  for (let day = firstMonday; day <= today; day += 1) {
    const iso = formatDayNumber(day)
    const count = day < start ? 0 : (counts.get(iso) ?? 0)
    cells.push({ iso, count, outside: day < start })
  }
  return (
    <section className="card">
      <h2 className="section-title">학습 달력</h2>
      <div className="heatmap" role="img" aria-label={`최근 12주 중 이번 달 ${calendar.studied_days_this_month}일 학습`}>
        {cells.map((cell) => (
          <i key={cell.iso} className={`heat heat-${cell.outside ? 'out' : heatLevel(cell.count)}`}
            title={`${cell.iso} · ${cell.count}개`} />
        ))}
      </div>
      <div className="heat-legend">
        <span>적게</span>
        {[0, 1, 2, 3].map((level) => <i key={level} className={`heat heat-${level}`} />)}
        <span>많이</span>
      </div>
      <div className="status-row">
        <span>이번 달 학습한 날</span>
        <strong>{calendar.studied_days_this_month}일</strong>
      </div>
      <div className="status-row">
        <span>최장 연속 학습</span>
        <strong>{calendar.longest_streak_days}일</strong>
      </div>
    </section>
  )
}

const MASTERY_LABELS = { learning: '학습 중', familiar: '익숙함' }

// 펼칠 때 처음 한 번만 불러온다 (접었다 펴도 다시 요청하지 않음)
function LearnedWordList() {
  const [list, setList] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    getLearnedWords().then(setList).catch((error) => setErrorMessage(error.message))
  }, [])

  if (errorMessage) return <p className="form-error" role="alert">{errorMessage}</p>
  if (!list) return <p className="hint-text">불러오는 중…</p>
  if (list.items.length === 0) return <p className="hint-text">아직 배운 단어가 없어요. 새 단어 학습을 시작해 보세요.</p>

  return (
    <ul id="learned-words" className="learned-list" aria-label="배운 단어 목록">
      {list.items.map((item) => (
        <li key={item.word_id} className="learned-item">
          <div className="learned-head">
            <strong className="learned-word">{item.headword}</strong>
            <span className="field-hint">{item.part_of_speech}</span>
            <SpeakButton text={item.headword} />
            <span className={`learned-badge learned-badge-${item.mastery}`}>{MASTERY_LABELS[item.mastery]}</span>
          </div>
          <p className="learned-meaning">{item.meaning_ko}</p>
          <p className="field-hint">{item.first_learned_date} 처음 배움</p>
        </li>
      ))}
    </ul>
  )
}
