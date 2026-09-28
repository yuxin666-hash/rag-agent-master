interface SidebarProps {
  activeKey: string
  onNavigate: (key: string) => void
  onLogout: () => void
}

const navItems = [
  { key: 'chat', label: '智能问答', icon: '💬' },
  { key: 'profile', label: '个人中心', icon: '👤' }
]

export default function Sidebar({ activeKey, onNavigate, onLogout }: SidebarProps) {
  return (
    <aside
      style={{
        width: '220px',
        height: '100vh',
        background: '#f4f9f4',
        display: 'flex',
        flexDirection: 'column',
        padding: '24px 0',
        position: 'relative',
        overflow: 'hidden',
        borderRight: '1px solid #e0ece0'
      }}
    >
      <div
        style={{
          padding: '0 24px 28px',
          fontSize: '20px',
          fontWeight: 600,
          color: '#2c5f2d',
          fontFamily: 'var(--font-display)',
          letterSpacing: '1px',
          position: 'relative',
          zIndex: 1
        }}
      >
        老乡鸡智能问答
      </div>

      <nav style={{ flex: 1, position: 'relative', zIndex: 1 }}>
        {navItems.map((item) => (
          <div
            key={item.key}
            onClick={() => onNavigate(item.key)}
            style={{
              padding: '14px 24px',
              margin: '4px 16px',
              borderRadius: '10px',
              cursor: 'pointer',
              fontSize: '14px',
              color: activeKey === item.key ? '#2c5f2d' : '#5c8a5c',
              background:
                activeKey === item.key
                  ? 'rgba(44,95,45,0.08)'
                  : 'transparent',
              fontWeight: activeKey === item.key ? 600 : 400,
              transition: 'all 0.2s',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              borderLeft:
                activeKey === item.key ? '3px solid #2c5f2d' : '3px solid transparent'
            }}
            onMouseEnter={(e) => {
              if (activeKey !== item.key) {
                e.currentTarget.style.background = 'rgba(44,95,45,0.04)'
                e.currentTarget.style.color = '#2c5f2d'
              }
            }}
            onMouseLeave={(e) => {
              if (activeKey !== item.key) {
                e.currentTarget.style.background = 'transparent'
                e.currentTarget.style.color = '#5c8a5c'
              }
            }}
          >
            <span style={{ fontSize: '16px' }}>{item.icon}</span>
            {item.label}
          </div>
        ))}
      </nav>

      <div style={{ padding: '0 20px', position: 'relative', zIndex: 1 }}>
        <button
          onClick={onLogout}
          style={{
            width: '100%',
            padding: '12px',
            background: 'transparent',
            border: '1px solid #c8dcc8',
            borderRadius: '10px',
            cursor: 'pointer',
            color: '#5c8a5c',
            fontSize: '14px',
            transition: 'all 0.2s',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(44,95,45,0.06)'
            e.currentTarget.style.borderColor = '#2c5f2d'
            e.currentTarget.style.color = '#2c5f2d'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent'
            e.currentTarget.style.borderColor = '#c8dcc8'
            e.currentTarget.style.color = '#5c8a5c'
          }}
        >
          <span>🚪</span>
          退出登录
        </button>
      </div>
    </aside>
  )
}
