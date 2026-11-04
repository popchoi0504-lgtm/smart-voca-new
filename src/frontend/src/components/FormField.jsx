// 2026-11-04 - smart-voca - 라벨, 입력칸, 안내/오류 문구를 묶은 재사용 부품 (로그인·가입 화면에서 공용)
// 파일 위치: src/frontend/src/components/FormField.jsx
export default function FormField({ label, name, type = 'text', value, onChange, error, hint, autoComplete }) {
  return (
    <div className="field">
      <label htmlFor={name}>{label}</label>
      <input
        id={name}
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        autoComplete={autoComplete}
        aria-invalid={Boolean(error)}
      />
      {error ? <p className="field-error">{error}</p> : hint && <p className="field-hint">{hint}</p>}
    </div>
  )
}
