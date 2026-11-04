// 2026-11-04 - smart-voca - 회원가입·로그인·로그아웃·내 정보 API 호출 함수 (인터페이스 정의서 4.2)
// 파일 위치: src/frontend/src/api/auth.js
import { apiFetch, ApiError } from './client'

export function signup(email, password) {
  return apiFetch('/auth/signup', { method: 'POST', body: { email, password } })
}

export function login(email, password) {
  return apiFetch('/auth/login', { method: 'POST', body: { email, password } })
}

export function logout() {
  return apiFetch('/auth/logout', { method: 'POST' })
}

/**
 * 지금 로그인한 회원을 돌려준다. 로그인하지 않았으면(401) 오류 대신 null 을 돌려준다.
 * (화면을 처음 열 때 "로그인 상태인가?"를 확인하는 용도라서 401 은 정상적인 경우다)
 */
export async function getMe() {
  try {
    const data = await apiFetch('/auth/me')
    return data.user
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null
    throw error
  }
}
