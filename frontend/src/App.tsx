import { useState, useEffect } from 'react'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import Layout from './components/Layout'

type Page = 'login' | 'register'

function App() {
  const [page, setPage] = useState<Page>('login')
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      setIsLoggedIn(true)
    }
  }, [])

  const handleLoginSuccess = () => {
    setIsLoggedIn(true)
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    setIsLoggedIn(false)
    setPage('login')
  }

  if (isLoggedIn) {
    return <Layout onLogout={handleLogout} />
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #faf8f5 0%, #f0ebe4 50%, #e8e0d5 100%)',
        position: 'relative',
        overflow: 'hidden',
        fontFamily: 'var(--font-body)'
      }}
    >
      {/* 装饰性背景圆 */}
      <div
        style={{
          position: 'absolute',
          top: '-10%',
          right: '-5%',
          width: '500px',
          height: '500px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(212,165,116,0.15) 0%, transparent 70%)',
          pointerEvents: 'none'
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: '-15%',
          left: '-10%',
          width: '600px',
          height: '600px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(44,95,45,0.08) 0%, transparent 70%)',
          pointerEvents: 'none'
        }}
      />
      {page === 'login' ? (
        <LoginPage
          onSwitchToRegister={() => setPage('register')}
          onLoginSuccess={handleLoginSuccess}
        />
      ) : (
        <RegisterPage onSwitchToLogin={() => setPage('login')} />
      )}
    </div>
  )
}

export default App
