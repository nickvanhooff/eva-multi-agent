import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listCampaigns } from '../api'
import AgentPipeline from '../components/AgentPipeline'

export default function Dashboard() {
  const [campaigns, setCampaigns] = useState([])
  const navigate = useNavigate()

  useEffect(() => {
    listCampaigns().then(setCampaigns).catch(() => {})
  }, [])

  const approved = campaigns.filter(c => c.approved_by_cm).length
  const approvalRate = campaigns.length ? Math.round((approved / campaigns.length) * 100) : 0
  const avgIterations = campaigns.length
    ? (campaigns.reduce((s, c) => s + (c.iterations || 0), 0) / campaigns.length).toFixed(1)
    : '—'

  return (
    <div style={{ padding: 32 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text)' }}>Dashboard</h1>
        <p style={{ color: 'var(--text-muted)', marginTop: 4 }}>Eva Multi-Agent System</p>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 32 }}>
        {[
          { label: 'Total Campaigns', value: campaigns.length },
          { label: 'Approval Rate', value: `${approvalRate}%` },
          { label: 'Avg Iterations', value: avgIterations },
        ].map(({ label, value }) => (
          <div key={label} style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 20 }}>
            <div style={{ color: 'var(--text-muted)', fontSize: 12, marginBottom: 8 }}>{label}</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--text)' }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Pipeline */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 24, marginBottom: 32 }}>
        <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 20, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>Agent Pipeline</div>
        <AgentPipeline activeNode={null} doneNodes={[]} />
        <div style={{ marginTop: 12, fontSize: 12, color: 'var(--text-muted)' }}>● System idle</div>
      </div>

      {/* Recent Campaigns */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>Recent Campaigns</div>
          <button onClick={() => navigate('/history')} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: 13 }}>View all →</button>
        </div>
        {campaigns.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '24px 0' }}>No campaigns yet</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                {['Product', 'Type', 'Status', 'Iterations', 'Date'].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '8px 12px', fontSize: 12, color: 'var(--text-muted)', fontWeight: 500 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {campaigns.slice(0, 5).map((c, i) => (
                <tr key={i} style={{ borderBottom: '1px solid var(--border)', cursor: 'pointer' }}
                  onClick={() => navigate(`/campaigns/${encodeURIComponent(c.filename?.replace('.json', ''))}`)}
                >
                  <td style={{ padding: '10px 12px', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.product_description}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{ background: 'rgba(99,102,241,0.15)', color: 'var(--primary)', borderRadius: 6, padding: '2px 8px', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>
                      {c.campaign_type || 'product'}
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{ color: c.approved_by_cm ? 'var(--green)' : 'var(--text-muted)' }}>
                      {c.approved_by_cm ? '● Approved' : '○ Pending'}
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px', color: 'var(--text-muted)' }}>{c.iterations ?? '—'}</td>
                  <td style={{ padding: '10px 12px', color: 'var(--text-muted)' }}>{c.timestamp ? new Date(c.timestamp).toLocaleDateString('nl') : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <button
        onClick={() => navigate('/campaigns/new')}
        style={{ marginTop: 24, background: 'var(--primary)', color: '#fff', border: 'none', borderRadius: 10, padding: '12px 28px', fontWeight: 600, fontSize: 14, cursor: 'pointer' }}
      >
        + New Campaign
      </button>
    </div>
  )
}
