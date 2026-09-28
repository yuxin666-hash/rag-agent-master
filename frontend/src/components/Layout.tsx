import { useState } from 'react'
import Sidebar from './Sidebar'
import ChatPage from '../pages/ChatPage'

interface LayoutProps {
  onLogout: () => void
}

export default function Layout({ onLogout }: LayoutProps) {
  const [activeKey, setActiveKey] = useState('chat')

  const renderContent = () => {
    switch (activeKey) {
      case 'chat':
        return <ChatPage />
      case 'profile':
        return (
          <div style={{ padding: '40px', color: '#666' }}>
            <h2 style={{ fontFamily: 'var(--font-display)', color: '#2c5f2d' }}>个人中心</h2>
            <p style={{ marginTop: '12px' }}>功能开发中...</p>
          </div>
        )
      default:
        return <ChatPage />
    }
  }

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: '#faf8f5' }}>
      <Sidebar activeKey={activeKey} onNavigate={setActiveKey} onLogout={onLogout} />
      <main style={{ flex: 1, overflow: 'hidden', background: '#faf8f5', padding: '12px', paddingLeft: '0' }}>
        {renderContent()}
      </main>
    </div>
  )
}
