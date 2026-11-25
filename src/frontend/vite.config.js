// 2026-11-03 - smart-voca - Vite 설정: 개발 서버 포트와 /api 요청을 백엔드로 넘기는 프록시 (아키텍처 AD-10)
// 파일 위치: src/frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: './', // 파일 주소를 상대 경로로 만든다 (서버가 /2026/voca-학번/ 아래로 옮겨도 동작)
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true, // 5173 이 이미 사용 중이면 다른 포트로 몰래 바꾸지 않고 오류를 낸다
    proxy: {
      // 브라우저는 항상 5173 으로만 요청한다. /api 로 시작하는 요청은 Vite 가 백엔드(8000)로 대신 전달한다.
      // 이렇게 하면 브라우저 입장에서 같은 주소라서 쿠키와 CORS 문제가 단순해진다.
      // localhost 대신 127.0.0.1 을 쓰는 이유: Windows 에서 localhost 가 IPv6(::1)로 해석돼 연결이 실패하는 경우를 피하기 위함
      '/api': {
        target: 'http://127.0.0.1:8000',
      },
    },
  },
})
