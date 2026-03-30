import { NavLink } from 'react-router-dom'

const nav = [
  { to: '/', label: 'Dashboard', icon: '⬛' },
  { to: '/campaigns/new', label: 'New Campaign', icon: '✦' },
  { to: '/history', label: 'History', icon: '◷' },
]

export default function Sidebar() {
  return (
    <aside style={{
      width: 220,
      minHeight: '100vh',
      background: 'var(--surface)',
      borderRight: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
      padding: '24px 0',
      flexShrink: 0,
    }}>
      <div style={{ padding: '0 20px 24px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ fontWeight: 700, fontSize: 16, color: 'var(--primary)', letterSpacing: '-0.3px' }}>Eva AI</div>
        <div style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 2 }}>Multi-Agent System</div>
      </div>

      <nav style={{ marginTop: 16, flex: 1 }}>
        {nav.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 20px',
              color: isActive ? 'var(--primary)' : 'var(--text-muted)',
              background: isActive ? 'rgba(99,102,241,0.1)' : 'transparent',
              borderRight: isActive ? '2px solid var(--primary)' : '2px solid transparent',
              textDecoration: 'none',
              fontSize: 14,
              fontWeight: isActive ? 600 : 400,
              transition: 'all 0.15s',
            })}
          >
            <span>{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
