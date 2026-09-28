import { useState, useRef, useEffect, useCallback } from 'react'
import MessageList, { Message } from '../components/MessageList'
import ChatBox from '../components/ChatBox'
import { chatApi, SessionItem } from '../services/api'

interface StatusInfo {
  step: string
  message: string
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: '你好！我是老乡鸡菜谱智能问答助手，请问有什么可以帮你的？' }
  ])
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<StatusInfo | null>(null)
  const [sessionId, setSessionId] = useState<string | undefined>(undefined)
  const [sessions, setSessions] = useState<SessionItem[]>([])
  const [sidebarVisible, setSidebarVisible] = useState(true)
  const [hoveredSession, setHoveredSession] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<boolean>(false)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, status])

  const loadSessions = useCallback(async () => {
    try {
      const res = await chatApi.listSessions()
      if (res.code === 200) {
        setSessions(res.data.sessions)
      }
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  const handleNewChat = async () => {
    if (loading) return
    try {
      const res = await chatApi.createSession()
      if (res.code === 200) {
        setSessionId(res.data.session_id)
        setMessages([
          { role: 'assistant', content: '你好！我是老乡鸡菜谱智能问答助手，请问有什么可以帮你的？' }
        ])
        setStatus(null)
        abortRef.current = false
        loadSessions()
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `抱歉，开启新对话失败：${err.message}` }
      ])
    }
  }

  const handleSelectSession = async (sid: string) => {
    if (loading || sid === sessionId) return
    try {
      const res = await chatApi.getSessionHistory(sid)
      if (res.code === 200) {
        setSessionId(sid)
        const historyMessages: Message[] = res.data.messages.map((m: any) => ({
          role: m.role,
          content: m.content
        }))
        setMessages(
          historyMessages.length > 0
            ? historyMessages
            : [
                {
                  role: 'assistant',
                  content: '你好！我是老乡鸡菜谱智能问答助手，请问有什么可以帮你的？'
                }
              ]
        )
        setStatus(null)
        abortRef.current = false
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `抱歉，加载历史对话失败：${err.message}` }
      ])
    }
  }

  const handleDeleteSession = async (sid: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!window.confirm('确定要删除这条对话记录吗？')) return
    try {
      const res = await chatApi.deleteSession(sid)
      if (res.code === 200) {
        if (sid === sessionId) {
          setSessionId(undefined)
          setMessages([
            { role: 'assistant', content: '你好！我是老乡鸡菜谱智能问答助手，请问有什么可以帮你的？' }
          ])
          setStatus(null)
        }
        loadSessions()
      }
    } catch (err: any) {
      alert(`删除失败：${err.message}`)
    }
  }

  const handleSend = async (message: string) => {
    setMessages((prev) => [...prev, { role: 'user', content: message }])
    setMessages((prev) => [...prev, { role: 'assistant', content: '' }])
    setLoading(true)
    setStatus({ step: 'start', message: '正在处理...' })
    abortRef.current = false

    const token = localStorage.getItem('access_token')
    const apiBase = import.meta.env.VITE_API_BASE_URL || '/api'

    try {
      const res = await fetch(`${apiBase}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ message, session_id: sessionId })
      })

      if (!res.ok || !res.body) {
        throw new Error('请求失败，请稍后重试')
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let fullReply = ''
      let finalSessionId = sessionId

      while (true) {
        if (abortRef.current) {
          reader.cancel()
          break
        }
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6)
            try {
              const data = JSON.parse(dataStr)

              if (data.type === 'status') {
                setStatus({ step: data.step, message: data.message })
              }

              if (data.type === 'chunk' && data.content) {
                fullReply += data.content
                setMessages((prev) => {
                  const next = [...prev]
                  next[next.length - 1] = { role: 'assistant', content: fullReply }
                  return next
                })
              }

              if (data.type === 'done') {
                finalSessionId = data.session_id || finalSessionId
              }

              if (data.type === 'error') {
                setMessages((prev) => {
                  const next = [...prev]
                  next[next.length - 1] = { role: 'assistant', content: `抱歉，${data.message}` }
                  return next
                })
              }
            } catch {
              // 忽略不完整的 JSON
            }
          }
        }
      }

      setSessionId(finalSessionId)
      loadSessions()
    } catch (err: any) {
      setMessages((prev) => {
        const next = [...prev]
        next[next.length - 1] = { role: 'assistant', content: `抱歉，${err.message}` }
        return next
      })
    } finally {
      setLoading(false)
      setStatus(null)
    }
  }

  return (
    <div style={{ display: 'flex', height: '100%', gap: '12px' }}>
      {/* 左侧会话列表面板 */}
      <div
        style={{
          width: sidebarVisible ? '240px' : '0px',
          background: '#fff',
          borderRadius: '20px',
          boxShadow: '0 4px 24px rgba(0,0,0,0.06)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          flexShrink: 0
        }}
      >
        <div
          style={{
            padding: '20px',
            borderBottom: '1px solid #f0ebe4',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          <button
            onClick={() => setSidebarVisible(false)}
            title="收起侧边栏"
            style={{
              width: '32px',
              height: '32px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: '#f7f5f2',
              border: 'none',
              borderRadius: '10px',
              cursor: 'pointer',
              color: '#666',
              fontSize: '13px',
              flexShrink: 0,
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#ece8e3'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = '#f7f5f2'
            }}
          >
            ◀
          </button>
          <button
            onClick={handleNewChat}
            disabled={loading}
            style={{
              flex: 1,
              padding: '10px',
              background: '#f0f7f0',
              color: '#2c5f2d',
              border: '1.5px solid #cce0cc',
              borderRadius: '12px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: 600,
              opacity: loading ? 0.6 : 1,
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.currentTarget.style.background = '#e0efe0'
                e.currentTarget.style.borderColor = '#2c5f2d'
                e.currentTarget.style.transform = 'translateY(-1px)'
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = '#f0f7f0'
              e.currentTarget.style.borderColor = '#cce0cc'
              e.currentTarget.style.transform = 'translateY(0)'
            }}
          >
            + 新建对话
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '10px 0' }}>
          {sessions.length === 0 && (
            <div style={{ padding: '16px 20px', color: '#bbb', fontSize: '13px', textAlign: 'center' }}>
              暂无历史对话
            </div>
          )}
          {sessions.map((s) => {
            const isActive = s.session_id === sessionId
            const isHovered = hoveredSession === s.session_id
            return (
              <div
                key={s.session_id}
                onClick={() => handleSelectSession(s.session_id)}
                onMouseEnter={() => setHoveredSession(s.session_id)}
                onMouseLeave={() => setHoveredSession(null)}
                style={{
                  padding: '12px 16px 12px 20px',
                  margin: '3px 12px',
                  borderRadius: '12px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontSize: '13px',
                  color: isActive ? '#2c5f2d' : '#555',
                  background: isActive ? 'rgba(44,95,45,0.08)' : 'transparent',
                  fontWeight: isActive ? 600 : 400,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  opacity: loading ? 0.6 : 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '8px',
                  transition: 'all 0.15s',
                  borderLeft: isActive ? '3px solid #2c5f2d' : '3px solid transparent'
                }}
                title={s.title}
              >
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.title}</span>
                <span
                  onClick={(e) => handleDeleteSession(s.session_id, e)}
                  style={{
                    flexShrink: 0,
                    width: '20px',
                    height: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: '6px',
                    fontSize: '15px',
                    color: isHovered ? '#c83c23' : 'transparent',
                    cursor: 'pointer',
                    transition: 'all 0.15s'
                  }}
                  title="删除"
                >
                  ×
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* 右侧聊天区域 */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          flex: 1,
          background: '#fff',
          borderRadius: '20px',
          boxShadow: '0 4px 24px rgba(0,0,0,0.06)',
          overflow: 'hidden'
        }}
      >
        <div
          style={{
            padding: '18px 28px',
            background: '#fff',
            borderBottom: '1px solid #f0ebe4',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
            fontSize: '16px',
            color: '#2d2d2d'
          }}
        >
          {!sidebarVisible && (
            <button
              onClick={() => setSidebarVisible(true)}
              title="展开侧边栏"
              style={{
                width: '34px',
                height: '34px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: '#f7f5f2',
                border: 'none',
                borderRadius: '10px',
                cursor: 'pointer',
                color: '#666',
                fontSize: '13px',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#ece8e3'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#f7f5f2'
              }}
            >
              ▶
            </button>
          )}
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '18px', color: '#2c5f2d' }}>
            智能问答
          </span>
          {status && (
            <span
              style={{
                marginLeft: 'auto',
                fontSize: '12px',
                color: '#2563eb',
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'rgba(37,99,235,0.06)',
                padding: '6px 14px',
                borderRadius: '20px'
              }}
            >
              <span
                style={{
                  width: '14px',
                  height: '14px',
                  border: '2px solid #2563eb',
                  borderTopColor: 'transparent',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite',
                  display: 'inline-block'
                }}
              />
              {status.message}
            </span>
          )}
        </div>

        <MessageList messages={messages} />

        <div ref={messagesEndRef} />
        <ChatBox onSend={handleSend} loading={loading} />
      </div>
    </div>
  )
}
