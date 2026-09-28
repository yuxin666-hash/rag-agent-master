import Avatar from './Avatar'

export interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface MessageListProps {
  messages: Message[]
}

export default function MessageList({ messages }: MessageListProps) {
  return (
    <div
      style={{
        flex: 1,
        overflowY: 'auto',
        padding: '24px 28px',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px'
      }}
    >
      {messages.map((msg, index) => {
        const isUser = msg.role === 'user'
        return (
          <div
            key={index}
            style={{
              alignSelf: isUser ? 'flex-end' : 'flex-start',
              maxWidth: '78%',
              display: 'flex',
              flexDirection: isUser ? 'row-reverse' : 'row',
              alignItems: 'flex-end',
              gap: '10px',
              animation: `fadeInUp 0.4s ease ${Math.min(index * 0.05, 0.3)}s both`
            }}
          >
            {/* 头像：优先加载图片，不存在则回退到渐变底色 */}
            <Avatar
              basePath={isUser ? '/avatars/user' : '/avatars/bot'}
              fallbackGradient={
                isUser
                  ? 'linear-gradient(135deg, #93c5fd, #60a5fa)'
                  : 'linear-gradient(135deg, #2c5f2d, #3d7a3e)'
              }
              label={isUser ? '我' : '厨'}
            />

            {/* 气泡 */}
            <div
              style={{
                padding: '14px 18px',
                borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                background: isUser
                  ? 'linear-gradient(135deg, #93c5fd, #60a5fa)'
                  : '#fff',
                color: isUser ? '#fff' : '#2d2d2d',
                fontSize: '14px',
                lineHeight: 1.7,
                boxShadow: isUser
                  ? '0 4px 12px rgba(59,130,246,0.2)'
                  : '0 2px 12px rgba(0,0,0,0.06)',
                wordBreak: 'break-word',
                borderLeft: isUser ? 'none' : '3px solid #2c5f2d'
              }}
            >
              {msg.content || (
                <span
                  style={{
                    display: 'inline-block',
                    width: '24px',
                    height: '6px',
                    borderRadius: '3px',
                    background: isUser
                      ? 'rgba(255,255,255,0.4)'
                      : 'rgba(0,0,0,0.1)',
                    animation: 'pulse 1.4s infinite'
                  }}
                />
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
