import { useState } from 'react'
import { authApi } from '../services/api'

interface LoginPageProps {
  onSwitchToRegister: () => void
  onLoginSuccess: () => void
}

export default function LoginPage({ onSwitchToRegister, onLoginSuccess }: LoginPageProps) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await authApi.login(username, password)
      if (res.code === 200) {
        localStorage.setItem('access_token', res.data.token)
        onLoginSuccess()
      } else {
        setError(res.msg)
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        width: '420px',
        background: 'rgba(255,255,255,0.95)',
        borderRadius: '24px',
        padding: '48px 40px',
        boxShadow: '0 20px 60px rgba(0,0,0,0.08)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.6)',
        position: 'relative',
        zIndex: 1,
        animation: 'fadeInUp 0.6s ease forwards'
      }}
    >
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <div
          style={{
            width: '56px',
            height: '56px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, #2c5f2d, #3d7a3e)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '20px',
            fontSize: '24px',
            color: '#fff'
          }}
        >
          🍳
        </div>
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '28px',
            color: '#2c5f2d',
            marginBottom: '8px',
            fontWeight: 400
          }}
        >
          欢迎回来
        </h1>
        <p style={{ color: '#9e9e9e', fontSize: '14px' }}>登录后继续探索美味菜谱</p>
      </div>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '20px' }}>
          <label
            style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '14px',
              color: '#5c5c5c',
              fontWeight: 500
            }}
          >
            用户名
          </label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            style={{
              width: '100%',
              padding: '12px 16px',
              border: '1px solid #ece8e3',
              borderRadius: '12px',
              fontSize: '14px',
              fontFamily: 'inherit',
              background: '#f7f5f2',
              outline: 'none',
              transition: 'all 0.2s'
            }}
            onFocus={(e) => {
              e.currentTarget.style.background = '#fff'
              e.currentTarget.style.borderColor = '#2c5f2d'
              e.currentTarget.style.boxShadow = '0 0 0 3px rgba(44,95,45,0.1)'
            }}
            onBlur={(e) => {
              e.currentTarget.style.background = '#f7f5f2'
              e.currentTarget.style.borderColor = '#ece8e3'
              e.currentTarget.style.boxShadow = 'none'
            }}
          />
        </div>
        <div style={{ marginBottom: '24px' }}>
          <label
            style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '14px',
              color: '#5c5c5c',
              fontWeight: 500
            }}
          >
            密码
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{
              width: '100%',
              padding: '12px 16px',
              border: '1px solid #ece8e3',
              borderRadius: '12px',
              fontSize: '14px',
              fontFamily: 'inherit',
              background: '#f7f5f2',
              outline: 'none',
              transition: 'all 0.2s'
            }}
            onFocus={(e) => {
              e.currentTarget.style.background = '#fff'
              e.currentTarget.style.borderColor = '#2c5f2d'
              e.currentTarget.style.boxShadow = '0 0 0 3px rgba(44,95,45,0.1)'
            }}
            onBlur={(e) => {
              e.currentTarget.style.background = '#f7f5f2'
              e.currentTarget.style.borderColor = '#ece8e3'
              e.currentTarget.style.boxShadow = 'none'
            }}
          />
        </div>

        {error && (
          <div
            style={{
              color: '#c83c23',
              fontSize: '13px',
              marginBottom: '16px',
              padding: '10px 14px',
              background: 'rgba(200,60,35,0.06)',
              borderRadius: '8px'
            }}
          >
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            width: '100%',
            padding: '14px',
            background: 'linear-gradient(135deg, #2c5f2d, #3d7a3e)',
            color: '#fff',
            border: 'none',
            borderRadius: '12px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '15px',
            fontWeight: 600,
            opacity: loading ? 0.7 : 1,
            transition: 'all 0.2s',
            boxShadow: loading ? 'none' : '0 4px 12px rgba(44,95,45,0.3)'
          }}
          onMouseEnter={(e) => {
            if (!loading) {
              e.currentTarget.style.transform = 'translateY(-1px)'
              e.currentTarget.style.boxShadow = '0 6px 20px rgba(44,95,45,0.4)'
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)'
            e.currentTarget.style.boxShadow = '0 4px 12px rgba(44,95,45,0.3)'
          }}
        >
          {loading ? '登录中...' : '登录'}
        </button>
      </form>

      <div
        style={{
          textAlign: 'center',
          marginTop: '24px',
          fontSize: '14px',
          color: '#9e9e9e'
        }}
      >
        还没有账号？
        <a
          onClick={onSwitchToRegister}
          style={{
            color: '#2c5f2d',
            cursor: 'pointer',
            fontWeight: 600,
            marginLeft: '4px'
          }}
        >
          立即注册
        </a>
      </div>
    </div>
  )
}
