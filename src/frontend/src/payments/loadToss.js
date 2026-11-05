// 2026-11-05 - smart-voca - 토스페이먼츠 결제위젯 스크립트(SDK v2)를 필요할 때 한 번만 불러온다 (FR-SUB-02)
// 파일 위치: src/frontend/src/payments/loadToss.js
// 가짜 결제(provider=fake)일 때는 이 파일을 쓰지 않으므로 외부 스크립트를 부르지 않는다.
const TOSS_SDK_URL = 'https://js.tosspayments.com/v2/standard'

let loadingPromise = null

export function loadTossSdk() {
  if (window.TossPayments) return Promise.resolve(window.TossPayments)
  if (!loadingPromise) {
    loadingPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script')
      script.src = TOSS_SDK_URL
      script.onload = () => resolve(window.TossPayments)
      script.onerror = () => {
        loadingPromise = null // 실패하면 다음에 다시 시도할 수 있게 비운다
        reject(new Error('결제 화면을 불러오지 못했어요. 잠시 후 다시 시도해 주세요.'))
      }
      document.head.appendChild(script)
    })
  }
  return loadingPromise
}
