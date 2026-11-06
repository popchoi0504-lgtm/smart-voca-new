// 2026-11-06 - smart-voca - 발음 듣기 버튼: 브라우저 내장 음성합성(Web Speech API)으로 영어 텍스트를 읽어 준다
// 파일 위치: src/frontend/src/components/SpeakButton.jsx
import { useEffect, useState } from 'react'

// 이 브라우저가 음성합성을 지원하는지 (지원하지 않으면 버튼을 아예 숨긴다)
const isSupported = typeof window !== 'undefined' && 'speechSynthesis' in window

// 영어 목소리를 고른다. 미국식(en-US)을 우선하고, 없으면 아무 영어 목소리나 쓴다.
function pickEnglishVoice() {
  const voices = window.speechSynthesis.getVoices()
  return voices.find((voice) => voice.lang === 'en-US') || voices.find((voice) => voice.lang.startsWith('en')) || null
}

export default function SpeakButton({ text, label = '발음 듣기', rate = 0.9 }) {
  const [isSpeaking, setIsSpeaking] = useState(false)

  // 카드가 넘어가거나 화면을 떠나면 읽던 소리를 멈춘다
  useEffect(() => {
    return () => {
      if (isSupported) window.speechSynthesis.cancel()
    }
  }, [text])

  if (!isSupported) return null

  function handleSpeak() {
    window.speechSynthesis.cancel() // 이전 소리가 남아 있으면 끊고 새로 시작
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'en-US'
    utterance.rate = rate // 학습용이라 조금 천천히
    const voice = pickEnglishVoice()
    if (voice) utterance.voice = voice
    utterance.onstart = () => setIsSpeaking(true)
    utterance.onend = () => setIsSpeaking(false)
    utterance.onerror = () => setIsSpeaking(false)
    window.speechSynthesis.speak(utterance)
  }

  return (
    <button
      className={`speak-btn${isSpeaking ? ' is-speaking' : ''}`}
      type="button"
      aria-label={`${label}: ${text}`}
      title={label}
      onClick={handleSpeak}
    >
      <span aria-hidden="true">🔊</span>
    </button>
  )
}
