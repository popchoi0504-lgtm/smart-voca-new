// 2026-11-25 - smart-voca - 내 단어 화면: 직접 등록·검색·수정·삭제·CSV 가져오기 (이슈 #24, VOCA-FR-001~004)
// 파일 위치: src/frontend/src/pages/MyWordsPage.jsx
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { ApiError } from '../api/client'
import { createMyWord, deleteMyWord, getMyWords, importMyWordsCsv, updateMyWord } from '../api/myWords'

const MAX_CSV_BYTES = 900_000 // 서버 한도(글자 100만 자)보다 조금 작게: 너무 큰 파일은 올리기 전에 알려 준다

/** 서버 오류를 화면 문구로. CSV 오류는 몇 째 줄이 문제인지도 함께 보여 준다. */
function messageOf(error) {
  if (error instanceof ApiError && error.fields?.length) {
    return `${error.message} (${error.fields.map((item) => `${item.field}: ${item.message}`).join(' / ')})`
  }
  return error.message
}

export default function MyWordsPage() {
  const [result, setResult] = useState(null) // 목록 응답 (null 이면 불러오는 중)
  const [searchText, setSearchText] = useState('') // 입력칸에 쓰는 중인 검색어
  const [query, setQuery] = useState('') // 실제로 검색에 쓰인 검색어
  const [page, setPage] = useState(1)
  const [headword, setHeadword] = useState('')
  const [meaning, setMeaning] = useState('')
  const [editingId, setEditingId] = useState(null) // 수정 중인 단어 번호 (없으면 새로 등록)
  const [message, setMessage] = useState('') // 성공 안내
  const [errorMessage, setErrorMessage] = useState('')
  const [isBusy, setIsBusy] = useState(false)
  const fileInput = useRef(null)
  const headwordInput = useRef(null)

  const load = useCallback(() => {
    getMyWords(query, page).then(setResult).catch((error) => setErrorMessage(messageOf(error)))
  }, [query, page])
  useEffect(load, [load])

  function resetForm() {
    setEditingId(null)
    setHeadword('')
    setMeaning('')
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setErrorMessage('')
    setMessage('')
    setIsBusy(true)
    try {
      if (editingId === null) {
        await createMyWord(headword, meaning)
        setMessage(`'${headword.trim()}' 단어를 등록했어요.`)
      } else {
        await updateMyWord(editingId, headword, meaning)
        setMessage('단어를 수정했어요.')
      }
      resetForm()
      load()
      headwordInput.current?.focus()
    } catch (error) {
      setErrorMessage(messageOf(error))
    } finally {
      setIsBusy(false)
    }
  }

  function startEdit(item) {
    setEditingId(item.id)
    setHeadword(item.headword)
    setMeaning(item.meaning_ko)
    setMessage('')
    setErrorMessage('')
    headwordInput.current?.focus()
  }

  async function handleDelete(item) {
    // 실수로 지우지 않도록 한 번 더 확인한다
    if (!window.confirm(`'${item.headword}' 단어를 지울까요? 되돌릴 수 없어요.`)) return
    setErrorMessage('')
    setMessage('')
    try {
      await deleteMyWord(item.id)
      if (editingId === item.id) resetForm()
      setMessage(`'${item.headword}' 단어를 지웠어요.`)
      // 마지막 쪽의 마지막 단어를 지웠다면 앞 쪽으로 돌아간다
      if (result.items.length === 1 && page > 1) setPage(page - 1)
      else load()
    } catch (error) {
      setErrorMessage(messageOf(error))
    }
  }

  function handleSearch(event) {
    event.preventDefault()
    setPage(1)
    setQuery(searchText.trim())
  }

  async function handleCsvFile(event) {
    const file = event.target.files?.[0]
    event.target.value = '' // 같은 파일을 다시 골라도 동작하도록 비워 둔다
    if (!file) return
    setErrorMessage('')
    setMessage('')
    if (file.size > MAX_CSV_BYTES) {
      setErrorMessage('파일이 너무 커요. 1MB 이하의 CSV 파일을 골라 주세요.')
      return
    }
    setIsBusy(true)
    try {
      // file.text() 는 UTF-8 로 읽고 맨 앞의 BOM 표시는 자동으로 떼 준다(서버도 한 번 더 확인한다)
      const summary = await importMyWordsCsv(await file.text())
      setMessage(
        `가져오기 완료: 새 단어 ${summary.inserted}개, 뜻을 덮어쓴 단어 ${summary.updated}개` +
          (summary.duplicate_in_file ? `, 파일 안 중복 ${summary.duplicate_in_file}개(나중 줄 사용)` : '') +
          `. 내 단어는 모두 ${summary.total_count}개예요.`,
      )
      setPage(1)
      load()
    } catch (error) {
      setErrorMessage(messageOf(error))
    } finally {
      setIsBusy(false)
    }
  }

  const lastPage = result ? Math.max(1, Math.ceil(result.total_count / result.page_size)) : 1

  return (
    <main className="page">
      <h1 className="page-title">내 단어</h1>
      <p className="page-subtitle">
        직접 넣은 단어예요{result ? ` (${query ? '검색 결과' : '전체'} ${result.total_count}개)` : ''}.
        {' '}<Link to="/my-words/study">내 단어 공부하기 →</Link>
      </p>

      <form className="card my-word-form" onSubmit={handleSubmit}>
        <h2 className="section-title">{editingId === null ? '새 단어 등록' : '단어 수정'}</h2>
        <div className="field">
          <label htmlFor="my-headword">영단어</label>
          <input id="my-headword" ref={headwordInput} value={headword} maxLength={100} autoComplete="off"
            onChange={(event) => setHeadword(event.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="my-meaning">뜻</label>
          <input id="my-meaning" value={meaning} maxLength={200} autoComplete="off"
            onChange={(event) => setMeaning(event.target.value)} />
        </div>
        <div className="button-row">
          <button className="btn btn-primary" type="submit" disabled={isBusy}>
            {editingId === null ? '등록' : '수정 저장'}
          </button>
          {editingId !== null && <button className="btn" type="button" onClick={resetForm}>수정 취소</button>}
        </div>
      </form>

      <section className="card my-word-csv">
        <h2 className="section-title">CSV 로 한꺼번에 등록</h2>
        <p className="field-hint">
          첫 줄이 <code>영단어,뜻</code> 인 CSV 파일(UTF-8)을 골라 주세요. 이미 있는 영단어(대소문자 무시)는 뜻을 새 파일의 뜻으로 덮어써요.
          파일 안에 같은 단어가 여러 번 있으면 나중 줄을 써요.
        </p>
        <input ref={fileInput} type="file" accept=".csv,text/csv" hidden onChange={handleCsvFile} aria-label="CSV 파일 선택" />
        <button className="btn" type="button" disabled={isBusy} onClick={() => fileInput.current?.click()}>
          CSV 파일 고르기
        </button>
      </section>

      {message && <p className="notice" role="status">{message}</p>}
      {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}

      <form className="my-word-search" role="search" onSubmit={handleSearch}>
        <input id="my-search" type="search" aria-label="영단어 또는 뜻 검색" placeholder="영단어 또는 뜻으로 검색" value={searchText}
          onChange={(event) => setSearchText(event.target.value)} />
        <button className="btn" type="submit">검색</button>
        {query && (
          <button className="btn" type="button" onClick={() => { setSearchText(''); setQuery(''); setPage(1) }}>
            전체 보기
          </button>
        )}
      </form>

      {result === null ? (
        <p>불러오는 중…</p>
      ) : result.items.length === 0 ? (
        <p className="notice">
          {query ? `'${query}' 에 맞는 단어가 없어요.` : '아직 등록한 단어가 없어요. 위에서 단어를 등록해 보세요.'}
        </p>
      ) : (
        <ul className="learned-list" aria-label="내 단어 목록">
          {result.items.map((item) => (
            <li key={item.id} className="learned-item">
              <div className="learned-head">
                <strong className="learned-word">{item.headword}</strong>
                <span className="learned-badge">
                  <button className="btn" type="button" onClick={() => startEdit(item)}>수정</button>{' '}
                  <button className="btn btn-danger" type="button" onClick={() => handleDelete(item)}>삭제</button>
                </span>
              </div>
              <p className="learned-meaning">{item.meaning_ko}</p>
            </li>
          ))}
        </ul>
      )}

      {result && lastPage > 1 && (
        <div className="button-row" aria-label="쪽 이동">
          <button className="btn" type="button" disabled={page <= 1} onClick={() => setPage(page - 1)}>이전</button>
          <span className="page-subtitle">{page} / {lastPage}</span>
          <button className="btn" type="button" disabled={page >= lastPage} onClick={() => setPage(page + 1)}>다음</button>
        </div>
      )}
    </main>
  )
}
