import { useState } from 'react'

interface ChatBoxProps {
  onSend: (message: string) => void
  loading: boolean
}

export default function ChatBox({ onSend, loading }: ChatBoxProps) {
  const [text, setText] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim() || loading) return
    onSend(text.trim())
    setText('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        padding: '16px 28px 24px',
        background: '#fff',
        borderTop: '1px solid #ece8e3',
        display: 'flex',
        alignItems: 'flex-end',
        gap: '12px'
      }}
    >
      <div style={{ flex: 1, position: 'relative' }}>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="请输入问题，按 Enter 发送..."
          rows={2}
          style={{
            width: '100%',
            padding: '14px 18px',
            paddingRight: '50px',
            border: '1.5px solid #ece8e3',
            borderRadius: '20px',
            resize: 'none',
            fontSize: '14px',
            fontFamily: 'inherit',
            background: '#f7f5f2',
            color: '#2d2d2d',
            outline: 'none',
            transition: 'all 0.25s',
            lineHeight: 1.5
          }}
          onFocus={(e) => {
            e.currentTarget.style.background = '#fff'
            e.currentTarget.style.borderColor = '#3b82f6'
            e.currentTarget.style.boxShadow = '0 0 0 4px rgba(59,130,246,0.1)'
          }}
          onBlur={(e) => {
            e.currentTarget.style.background = '#f7f5f2'
            e.currentTarget.style.borderColor = '#ece8e3'
            e.currentTarget.style.boxShadow = 'none'
          }}
        />
      </div>
      <button
        type="submit"
        disabled={loading || !text.trim()}
        style={{
          width: '48px',
          height: '48px',
          borderRadius: '14px',
          background: loading
            ? '#d9d9d9'
            : '#eff6ff',
          color: loading ? '#fff' : '#2563eb',
          border: loading ? 'none' : '1.5px solid #bfdbfe',
          cursor: loading ? 'not-allowed' : 'pointer',
          fontSize: '18px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          transition: 'all 0.2s',
          boxShadow: loading
            ? 'none'
            : '0 2px 8px rgba(37,99,235,0.15)'
        }}
        onMouseEnter={(e) => {
          if (!loading && text.trim()) {
            e.currentTarget.style.background = '#dbeafe'
            e.currentTarget.style.borderColor = '#2563eb'
            e.currentTarget.style.transform = 'scale(1.05) translateY(-1px)'
            e.currentTarget.style.boxShadow = '0 4px 16px rgba(37,99,235,0.25)'
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = '#eff6ff'
          e.currentTarget.style.borderColor = '#bfdbfe'
          e.currentTarget.style.transform = 'scale(1) translateY(0)'
          e.currentTarget.style.boxShadow = loading
            ? 'none'
            : '0 2px 8px rgba(37,99,235,0.15)'
        }}
      >
        {loading ? '⏳' : '➤'}
      </button>
    </form>
  )
}
