// 2026-11-04 - smart-voca - 로그인 상태를 모든 화면이 함께 쓰도록 담아 두는 "공용 게시판" (FR-AUTH-02·03·05)
// 파일 위치: src/frontend/src/auth/AuthContext.jsx
import { createContext, useContext, useEffect, useState } from 'react'

import { getMe, login, logout, signup } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null) // 로그인한 회원 (없으면 null)
  const [isLoading, setIsLoading] = useState(true) // 처음 열 때 로그인 상태를 확인하는 중인지

  // 화면을 처음 열 때 한 번: 쿠키가 남아 있으면 서버가 "누구인지" 알려 준다 (새로고침해도 로그인이 유지되는 이유)
  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false))
  }, [])

  async function signIn(email, password) {
    const data = await login(email, password)
    setUser(data.user)
  }

  async function signUp(email, password, consents) {
    const data = await signup(email, password, consents)
    setUser(data.user)
  }

  async function signOut() {
    await logout()
    setUser(null)
  }

  // setUser 도 내보낸다: 설정을 바꾼 뒤 서버가 돌려준 최신 회원 정보로 화면 전체를 갱신하기 위함
  return (
    <AuthContext.Provider value={{ user, isLoading, signIn, signUp, signOut, setUser }}>{children}</AuthContext.Provider>
  )
}

/** 어느 화면에서든 `const { user, signIn, ... } = useAuth()` 로 로그인 상태를 꺼내 쓴다. */
export function useAuth() {
  return useContext(AuthContext)
}
