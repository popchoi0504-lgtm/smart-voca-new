// 2026-11-06 - smart-voca - "지금 화면이 어떤 단어를 보여 주고 있는지"를 AI 선생님 아이콘에 알려 주는 연결 장치 (FR-AI-02~04)
// 파일 위치: src/frontend/src/teacher/TeacherContext.jsx
// 새 단어·퀴즈 화면이 useTeacherTarget 으로 현재 단어를 등록하면, 오른쪽 아래 선생님이 그 단어를 기준으로 답한다.
import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const TeacherContext = createContext({ target: null, setTarget: () => {} })

export function TeacherProvider({ children }) {
  const [target, setTarget] = useState(null)
  const value = useMemo(() => ({ target, setTarget }), [target])
  return <TeacherContext.Provider value={value}>{children}</TeacherContext.Provider>
}

export function useTeacher() {
  return useContext(TeacherContext)
}

/**
 * 화면이 쓰는 함수. target = { wordId, label, context(study 또는 quiz), ready, notReadyMessage } 또는 null.
 * ready 가 false 면 선생님이 notReadyMessage 만 보여 준다(예: 퀴즈를 풀기 전).
 * 화면을 떠나면 자동으로 등록이 풀린다.
 */
export function useTeacherTarget(target) {
  const { setTarget } = useTeacher()
  const wordId = target?.wordId
  const label = target?.label
  const context = target?.context
  const ready = target?.ready
  const notReadyMessage = target?.notReadyMessage

  useEffect(() => {
    setTarget(wordId == null ? null : { wordId, label, context, ready, notReadyMessage })
    return () => setTarget(null)
  }, [setTarget, wordId, label, context, ready, notReadyMessage])
}
