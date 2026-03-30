import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listCampaigns } from '../api'

export default function CampaignHistory() {
  const navigate = useNavigate()
  const [campaigns, setCampaigns] = useState([])
  const [filter, setFilter] = useState({ type: '', status: '' })

  useEffect(() => {
    listCampaigns().then(setCampaigns).catch(() => {})
  }, [])

  const filtered = campaigns.filter(c => {
    if (filter.type && (c.campaign_type || 'product') !== filter.type) return false
    if (filter.status === 'approved' && !c.approved_by_cm) return false
    if (filter.status === 'pending' && c.approved_by_cm) return false
    return true
  })

  const sel = { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 12px', color: 'var(--text)', fontSize: 13 }

  return (
    <div style={{ padding: 32 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Campaign History</h1>
        <p style={{ color: 'var(--text-muted)', marginTop: 4 }}>All past AI-generated campaigns</p>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <select value={filter.type} onChange={e => setFilter(f => ({ ...f, type: e.target.value }))} style={sel}>
          <option value="">All Types</option>
          <option value="product">Product</option>
          <option value="book">Book</option>
        </select>
        <select value={filter.status} onChange={e => setFilter(f => ({ ...f, status: e.target.value }))} style={sel}>
          <option value="">All Status</option>
          <option value="approved">Approved</option>
          <option value="pending">Pending</option>
        </select>
        <button
          onClick={() => navigate('/campaigns/new')}
          style={{ marginLeft: 'auto', background: 'var(--primary)', color: '#fff', border: 'none', borderRadius: 8, padding: '8px 20px', fontWeight: 600, fontSize: 13, cursor: 'pointer' }}
        >
          + New Campaign
        </button>
      </div>

      {/* Table */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)', background: 'var(--surface2)' }}>
              {['Date', 'Product', 'Type', 'Iterations', 'Status', 'Actions'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '12px 16px', fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr><td colSpan={6} style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>No campaigns found</td></tr>
            ) : filtered.map((c, i) => (
              <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontSize: 13, whiteSpace: 'nowrap' }}>
                  {c.timestamp ? new Date(c.timestamp).toLocaleDateString('nl') : '—'}
                </td>
                <td style={{ padding: '12px 16px', maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 13 }}>
                  {c.product_description}
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ background: 'rgba(99,102,241,0.15)', color: 'var(--primary)', borderRadius: 6, padding: '2px 8px', fontSize: 11, fontWeight: 600, textTransform: 'uppercase' }}>
                    {c.campaign_type || 'product'}
                  </span>
                </td>
                <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontSize: 13 }}>{c.iterations ?? '—'}</td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ color: c.approved_by_cm ? 'var(--green)' : 'var(--text-muted)', fontSize: 13 }}>
                    {c.approved_by_cm ? '● Approved' : '○ Pending'}
                  </span>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <button
                    onClick={() => navigate(`/campaigns/${encodeURIComponent(c.filename?.replace('.json', ''))}`)}
                    style={{ background: 'none', border: '1px solid var(--border)', borderRadius: 6, padding: '4px 12px', color: 'var(--text)', cursor: 'pointer', fontSize: 12 }}
                  >
                    View →
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: 12, color: 'var(--text-muted)', fontSize: 12 }}>
        Showing {filtered.length} of {campaigns.length} campaigns
      </div>
    </div>
  )
}
