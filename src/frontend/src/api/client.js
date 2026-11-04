// 2026-11-03 - smart-voca - 서버 API 를 부르는 공통 함수와 오류 형태 (인터페이스 정의서 2~3장)
// 파일 위치: src/frontend/src/api/client.js

/** 서버가 돌려준 오류를 담는 객체. code 로 어떤 오류인지 구분한다. */
export class ApiError extends Error {
  constructor(status, code, message, fields, body) {
    super(message)
    this.status = status // HTTP 상태 코드 (예: 401)
    this.code = code // 오류 코드 (예: NOT_AUTHENTICATED)
    this.fields = fields // 입력 오류일 때 칸별 메시지
    this.body = body // 서버가 보낸 원본 응답 (예외적인 모양을 처리할 때 사용)
  }
}

/**
 * 서버 API 를 부르고 JSON 결과를 돌려준다. 실패하면 ApiError 를 던진다.
 * path 는 '/api' 를 뺀 나머지 (예: '/health').
 */
export async function apiFetch(path, { method = 'GET', body } = {}) {
  const options = { method, headers: {}, credentials: 'same-origin' }
  if (body !== undefined) {
    options.headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(body)
  }

  let response
  try {
    response = await fetch(`/api${path}`, options)
  } catch {
    // 서버가 꺼져 있거나 네트워크가 끊긴 경우
    throw new ApiError(0, 'NETWORK_ERROR', '서버에 연결할 수 없어요. 잠시 후 다시 시도해 주세요.')
  }

  if (response.status === 204) return null // 내용이 없는 성공 (예: 로그아웃)

  let data = null
  try {
    data = await response.json()
  } catch {
    // JSON 이 아닌 응답이면 data 는 null 로 둔다
  }

  if (!response.ok) {
    const error = data?.error
    throw new ApiError(
      response.status,
      error?.code ?? `HTTP_${response.status}`,
      error?.message ?? '요청을 처리하지 못했어요.',
      error?.fields,
      data,
    )
  }
  return data
}

/**
 * 서버가 알려 준 입력 오류(칸별 메시지)를 { email: '...', password: '...' } 모양으로 바꿔 화면에서 쓰기 쉽게 한다.
 */
export function fieldErrorsOf(error) {
  if (!(error instanceof ApiError) || !error.fields) return {}
  return Object.fromEntries(error.fields.map((item) => [item.field, item.message]))
}

/**
 * 서버·DB 상태 확인. DB 가 고장이면 서버가 503 과 함께 {status, db} 를 보내므로 그 내용도 그대로 돌려준다.
 */
export async function getHealth() {
  try {
    return await apiFetch('/health')
  } catch (error) {
    if (error instanceof ApiError && error.status === 503 && error.body) return error.body
    throw error
  }
}
