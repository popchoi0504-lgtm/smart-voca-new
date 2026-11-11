// 2026-11-04 - smart-voca - 설정 화면: 프로필(닉네임·아바타), 이용권 요약, 하루 새 단어 수, 비밀번호 변경, 회원 탈퇴 (FR-STUDY-04, FR-PROFILE-01~05)
// 2026-11-11 - 세로로 길게 쌓이던 카드 6개를 가로 탭 4개(프로필·이용권·학습·알림·보안)로 재배치. 저장·검사 동작은 그대로.
// 파일 위치: src/frontend/src/pages/SettingsPage.jsx
import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { changePassword, getPlanSummary, updateMarketingConsent, updateProfile, withdrawAccount } from '../api/profile'
import { fieldErrorsOf } from '../api/client'
import { updateDailyNewLimit } from '../api/study'
import { useAuth } from '../auth/AuthContext'
import Avatar, { AVATAR_COLORS } from '../components/Avatar'
import FormField from '../components/FormField'

const WITHDRAW_CONFIRM_TEXT = '탈퇴합니다' // 서버도 같은 문구를 다시 검사한다

/** 저장 요청을 보내는 공통 흐름: 중복 클릭 방지, 칸별 오류와 일반 오류 분리, 성공 문구 */
function useSubmit() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [savedMessage, setSavedMessage] = useState('')

  async function submit(action, successMessage) {
    setIsSubmitting(true)
    setErrorMessage('')
    setFieldErrors({})
    setSavedMessage('')
    try {
      await action()
      setSavedMessage(successMessage)
      return true
    } catch (error) {
      const fields = fieldErrorsOf(error)
      setFieldErrors(fields)
      if (Object.keys(fields).length === 0) setErrorMessage(error.message)
      return false
    } finally {
      setIsSubmitting(false)
    }
  }

  return { submit, isSubmitting, errorMessage, fieldErrors, savedMessage }
}

function Messages({ errorMessage, savedMessage }) {
  return (
    <>
      {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}
      {savedMessage && <p className="status-ok" role="status">{savedMessage}</p>}
    </>
  )
}

function ProfileSection() {
  const { user, setUser } = useAuth()
  const [nickname, setNickname] = useState(user.nickname ?? '')
  const [color, setColor] = useState(user.avatar_color)
  const form = useSubmit()
  const previewName = nickname.trim() || user.display_name

  function handleSubmit(event) {
    event.preventDefault()
    // 닉네임 칸이 비어 있으면 닉네임은 보내지 않고 색만 바꾼다(닉네임을 지우는 기능은 없다)
    const changes = { avatar_color: color }
    if (nickname.trim() !== '') changes.nickname = nickname
    form.submit(async () => setUser(await updateProfile(changes)), '저장했어요.')
  }

  return (
    <form className="card form" onSubmit={handleSubmit}>
      <h2>프로필</h2>
      <div className="profile-preview">
        <Avatar name={previewName} color={color} size="lg" />
        <div>
          <strong>{previewName}</strong>
          <small>{user.email}</small>
        </div>
      </div>
      <FormField
        label="닉네임"
        name="nickname"
        value={nickname}
        onChange={(event) => setNickname(event.target.value)}
        error={form.fieldErrors.nickname}
        hint="2~12자. 다른 사람과 같아도 괜찮아요."
        autoComplete="nickname"
      />
      <div className="field">
        <label id="avatar-color-label">아바타 색</label>
        <div className="color-picker" role="group" aria-labelledby="avatar-color-label">
          {AVATAR_COLORS.map((item) => (
            <button key={item.value} type="button" aria-label={item.label} aria-pressed={color === item.value} onClick={() => setColor(item.value)}>
              <Avatar name={previewName} color={item.value} size="sm" />
            </button>
          ))}
        </div>
      </div>
      <Messages errorMessage={form.errorMessage} savedMessage={form.savedMessage} />
      <button className="btn btn-primary" type="submit" disabled={form.isSubmitting}>
        {form.isSubmitting ? '저장 중…' : '프로필 저장'}
      </button>
    </form>
  )
}

function PlanSection() {
  const [summary, setSummary] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    getPlanSummary().then(setSummary).catch((error) => setErrorMessage(error.message))
  }, [])

  return (
    <section className="card">
      <h2>이용권</h2>
      {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}
      {!summary && !errorMessage && <p className="field-hint">불러오는 중…</p>}
      {summary && (
        <dl className="summary-list">
          <div><dt>요금제</dt><dd>{summary.plan === 'premium' ? '프리미엄' : '무료'}</dd></div>
          <div>
            <dt>만료일</dt>
            <dd>{summary.plan === 'premium' ? new Date(summary.premium_until).toLocaleDateString('ko-KR') : '—'}</dd>
          </div>
          <div>
            <dt>AI 선생님 오늘 남은 횟수</dt>
            <dd>{summary.ai_remaining_today} / {summary.ai_daily_limit}회</dd>
          </div>
        </dl>
      )}
      <p className="field-hint"><Link to="/subscribe">요금제 보기</Link></p>
    </section>
  )
}

function StudySection() {
  const { user, setUser } = useAuth()
  const [limitText, setLimitText] = useState(String(user.daily_new_limit))
  const [clientError, setClientError] = useState('')
  const form = useSubmit()

  function handleSubmit(event) {
    event.preventDefault()
    setClientError('')
    // 입력칸의 값은 글자라서 정수로 바꾼다. 범위(1~50)의 최종 검사는 서버가 한다
    const value = Number(limitText)
    if (limitText.trim() === '' || !Number.isInteger(value)) {
      setClientError('1~50 사이의 정수를 입력해 주세요.')
      return
    }
    form.submit(async () => setUser(await updateDailyNewLimit(value)), '저장했어요.')
  }

  return (
    <form className="card form" onSubmit={handleSubmit}>
      <h2>학습</h2>
      <FormField
        label="하루에 배울 새 단어 수"
        name="daily_new_limit"
        type="number"
        value={limitText}
        onChange={(event) => setLimitText(event.target.value)}
        error={clientError || form.fieldErrors.daily_new_limit}
        hint="1~50개. 한 번에는 최대 10개씩 보여 드려요."
      />
      <Messages errorMessage={form.errorMessage} savedMessage={form.savedMessage} />
      <button className="btn btn-primary" type="submit" disabled={form.isSubmitting}>
        {form.isSubmitting ? '저장 중…' : '저장'}
      </button>
    </form>
  )
}

function ConsentSection() {
  const { user, setUser } = useAuth()
  const form = useSubmit()

  // 체크하면 바로 저장한다(철회도 동의만큼 쉬워야 한다). 실패하면 서버 값 그대로라 체크도 그대로 남는다
  function handleChange(event) {
    const checked = event.target.checked
    form.submit(async () => setUser(await updateMarketingConsent(checked)), checked ? '수신에 동의했어요.' : '수신 동의를 철회했어요.')
  }

  return (
    <section className="card form">
      <h2>알림</h2>
      <label className="consent-row">
        <input type="checkbox" checked={user.marketing_agreed} onChange={handleChange} disabled={form.isSubmitting} />
        <span>서비스 소식 수신에 동의합니다. (선택)</span>
      </label>
      <Messages errorMessage={form.errorMessage} savedMessage={form.savedMessage} />
      <p className="field-hint"><Link to="/privacy">개인정보처리방침</Link> · <Link to="/terms">이용약관</Link></p>
    </section>
  )
}

function PasswordSection() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [isOpen, setIsOpen] = useState(false) // 평소에는 접어 두고 "변경"을 눌렀을 때만 입력칸을 보인다
  const form = useSubmit()

  async function handleSubmit(event) {
    event.preventDefault()
    const ok = await form.submit(() => changePassword(currentPassword, newPassword), '비밀번호를 바꿨어요.')
    if (ok) {
      setCurrentPassword('')
      setNewPassword('')
      setIsOpen(false)
    }
  }

  function handleCancel() {
    setIsOpen(false)
    setCurrentPassword('')
    setNewPassword('')
  }

  if (!isOpen) {
    return (
      <section className="card">
        <div className="setting-row">
          <div>
            <h2>비밀번호</h2>
            <small className="field-hint">주기적으로 바꾸면 계정이 더 안전해요.</small>
          </div>
          <button className="btn" type="button" aria-expanded="false" aria-controls="password-form" onClick={() => setIsOpen(true)}>
            변경
          </button>
        </div>
        {form.savedMessage && <p className="status-ok" role="status">{form.savedMessage}</p>}
      </section>
    )
  }

  return (
    <form id="password-form" className="card form" onSubmit={handleSubmit}>
      <h2>비밀번호 변경</h2>
      <FormField
        label="현재 비밀번호"
        name="current_password"
        type="password"
        value={currentPassword}
        onChange={(event) => setCurrentPassword(event.target.value)}
        error={form.fieldErrors.current_password}
        autoComplete="current-password"
      />
      <FormField
        label="새 비밀번호"
        name="new_password"
        type="password"
        value={newPassword}
        onChange={(event) => setNewPassword(event.target.value)}
        error={form.fieldErrors.new_password}
        hint="8~64자, 영문과 숫자를 모두 포함해 주세요."
        autoComplete="new-password"
      />
      <Messages errorMessage={form.errorMessage} savedMessage={form.savedMessage} />
      <button className="btn btn-primary" type="submit" disabled={form.isSubmitting || !currentPassword || !newPassword}>
        {form.isSubmitting ? '바꾸는 중…' : '비밀번호 바꾸기'}
      </button>
      <button className="btn" type="button" aria-expanded="true" aria-controls="password-form" onClick={handleCancel} disabled={form.isSubmitting}>
        취소
      </button>
    </form>
  )
}

function WithdrawSection() {
  const { setUser } = useAuth()
  const [password, setPassword] = useState('')
  const [confirmText, setConfirmText] = useState('')
  const [isOpen, setIsOpen] = useState(false) // 기본은 접어 둬서 실수로 누르지 않게 한다
  const form = useSubmit()

  function handleClose() {
    setIsOpen(false)
    setPassword('')
    setConfirmText('')
  }

  async function handleSubmit(event) {
    event.preventDefault()
    // 성공하면 서버가 로그인 쿠키를 지웠으므로 화면도 로그아웃 상태로 바꾼다(보호된 화면이라 로그인 화면으로 이동)
    const ok = await form.submit(() => withdrawAccount(password, confirmText), '탈퇴했어요.')
    if (ok) setUser(null)
  }

  if (!isOpen) {
    // 눈에 덜 띄는 작은 글자 링크로 둔다(실수로 누르지 않게). 누르면 아래에서 경고와 확인 절차가 펼쳐진다
    return (
      <p className="danger-zone">
        더 이상 사용하지 않으시나요?{' '}
        <button className="link-danger" type="button" aria-expanded="false" aria-controls="withdraw-form" onClick={() => setIsOpen(true)}>
          회원 탈퇴
        </button>
      </p>
    )
  }

  return (
    <form id="withdraw-form" className="card card-danger form" onSubmit={handleSubmit}>
      <h2>회원 탈퇴</h2>
      <ul className="warning-list">
        <li>학습 기록과 AI 선생님 사용 기록이 모두 지워지고 되돌릴 수 없어요.</li>
        <li>이용권이 남아 있어도 사라져요. 환불 규정은 정식 출시 전에 정해요.</li>
        <li>결제 내역은 누구의 것인지 알 수 없게 바꿔 법정 기간 동안 보관해요.</li>
        <li>같은 이메일로 다시 가입할 수 있지만 기록은 이어지지 않아요.</li>
      </ul>
      <FormField
        label="비밀번호"
        name="withdraw_password"
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        error={form.fieldErrors.password}
        autoComplete="current-password"
      />
      <FormField
        label={`확인 문구: ${WITHDRAW_CONFIRM_TEXT}`}
        name="withdraw_confirm"
        value={confirmText}
        onChange={(event) => setConfirmText(event.target.value)}
        error={form.fieldErrors.confirm_text}
        hint={`"${WITHDRAW_CONFIRM_TEXT}"를 그대로 입력하면 버튼이 켜져요.`}
        autoComplete="off"
      />
      <Messages errorMessage={form.errorMessage} savedMessage={form.savedMessage} />
      <button className="btn btn-danger" type="submit" disabled={form.isSubmitting || !password || confirmText.trim() !== WITHDRAW_CONFIRM_TEXT}>
        {form.isSubmitting ? '처리 중…' : '탈퇴하기'}
      </button>
      <button className="btn" type="button" aria-expanded="true" aria-controls="withdraw-form" onClick={handleClose} disabled={form.isSubmitting}>
        접기
      </button>
    </form>
  )
}

// 탭 4개. 주소의 ?tab= 값으로 열린 탭을 기억해서, 새로고침하거나 링크로 들어와도 같은 탭이 열린다
const TABS = [
  { id: 'profile', label: '프로필' },
  { id: 'plan', label: '이용권' },
  { id: 'study', label: '학습·알림' },
  { id: 'security', label: '보안' },
]

export default function SettingsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const requestedTab = searchParams.get('tab')
  const activeTab = TABS.some((tab) => tab.id === requestedTab) ? requestedTab : TABS[0].id

  function selectTab(tabId) {
    setSearchParams({ tab: tabId }, { replace: true })
  }

  // 좌우 화살표로 탭을 옮길 수 있게 한다(키보드 사용자용)
  function handleTabKeyDown(event, index) {
    if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return
    event.preventDefault()
    const step = event.key === 'ArrowRight' ? 1 : -1
    const next = TABS[(index + step + TABS.length) % TABS.length]
    selectTab(next.id)
    document.getElementById(`settings-tab-${next.id}`)?.focus()
  }

  return (
    <main className="page">
      <h1 className="page-title">설정</h1>
      <div className="settings-tabs" role="tablist" aria-label="설정 구역">
        {TABS.map((tab, index) => (
          <button
            key={tab.id}
            id={`settings-tab-${tab.id}`}
            className="settings-tab"
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`settings-panel-${tab.id}`}
            tabIndex={activeTab === tab.id ? 0 : -1}
            onClick={() => selectTab(tab.id)}
            onKeyDown={(event) => handleTabKeyDown(event, index)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {/* 안 보이는 탭도 화면에는 올려 두고 숨기기만 한다 → 탭을 옮겨도 쓰던 입력이 사라지지 않는다 */}
      <div id="settings-panel-profile" role="tabpanel" aria-labelledby="settings-tab-profile" hidden={activeTab !== 'profile'}>
        <ProfileSection />
      </div>
      <div id="settings-panel-plan" role="tabpanel" aria-labelledby="settings-tab-plan" hidden={activeTab !== 'plan'}>
        <PlanSection />
      </div>
      <div id="settings-panel-study" role="tabpanel" aria-labelledby="settings-tab-study" hidden={activeTab !== 'study'}>
        <StudySection />
        <ConsentSection />
      </div>
      <div id="settings-panel-security" role="tabpanel" aria-labelledby="settings-tab-security" hidden={activeTab !== 'security'}>
        <PasswordSection />
        <WithdrawSection />
      </div>
      <p><Link to="/">← 오늘 할 것으로</Link></p>
    </main>
  )
}
