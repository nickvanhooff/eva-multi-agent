import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getCampaign } from '../api'

export default function CampaignResults() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [tab, setTab] = useState('strategy')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getCampaign(decodeURIComponent(id))
      .then(job => {
        // result can be the campaign object directly (from file) or nested under .result
        setData(job.result || job)
        setLoading(false)
      })
      .catch(err => {
        setError(String(err))
        setLoading(false)
      })
  }, [id])

  if (loading) return <div style={{ padding: 32, color: 'var(--text-muted)' }}>Loading...</div>
  if (error || !data) return (
    <div style={{ padding: 32 }}>
      <p style={{ color: 'var(--red)' }}>Campaign not found</p>
      <button onClick={() => navigate('/')} style={{ marginTop: 12, background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer' }}>← Back to dashboard</button>
    </div>
  )

  const tabs = ['strategy', 'copy', 'social']
  if (data.image_path) tabs.push('image')

  return (
    <div style={{ padding: 32 }}>
      <button onClick={() => navigate(-1)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', marginBottom: 16 }}>← Back</button>

      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>
          {(data.product_description || '').slice(0, 60)}{(data.product_description || '').length > 60 ? '...' : ''}
        </h1>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{ background: 'rgba(99,102,241,0.15)', color: 'var(--primary)', borderRadius: 6, padding: '2px 10px', fontSize: 12, fontWeight: 600, textTransform: 'uppercase' }}>
            {data.campaign_type || 'product'}
          </span>
          <span style={{ color: data.approved_by_cm ? 'var(--green)' : 'var(--text-muted)', fontSize: 13 }}>
            CM: {data.approved_by_cm ? '✓ Approved' : 'Pending'}
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>
            {data.iterations ?? '—'} iteration{data.iterations !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid var(--border)', marginBottom: 24 }}>
        {tabs.map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            background: 'none', border: 'none',
            borderBottom: tab === t ? '2px solid var(--primary)' : '2px solid transparent',
            color: tab === t ? 'var(--primary)' : 'var(--text-muted)',
            padding: '10px 18px', cursor: 'pointer',
            fontWeight: tab === t ? 600 : 400, fontSize: 14, textTransform: 'capitalize',
          }}>{t}</button>
        ))}
      </div>

      {tab === 'strategy' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          {[
            { label: 'Target Audience', value: data.target_audience },
            { label: 'Positioning', value: data.positioning },
            { label: 'Tone of Voice', value: data.tone_of_voice },
          ].map(({ label, value }) => (
            <div key={label} style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 20 }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>{label}</div>
              <p style={{ color: 'var(--text)', lineHeight: 1.6, fontSize: 13 }}>{value || '—'}</p>
            </div>
          ))}
          <div style={{ gridColumn: '1/-1', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 20 }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Strategy</div>
            <p style={{ color: 'var(--text)', lineHeight: 1.7, fontSize: 13, whiteSpace: 'pre-wrap' }}>{data.strategy || '—'}</p>
          </div>
        </div>
      )}

      {tab === 'copy' && (
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 24 }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>Marketing Copy</div>
          <p style={{ color: 'var(--text)', lineHeight: 1.8, fontSize: 14, whiteSpace: 'pre-wrap' }}>{data.copy_draft || '—'}</p>
        </div>
      )}

      {tab === 'social' && (
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 24 }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>Social Content</div>
          <p style={{ color: 'var(--text)', lineHeight: 1.8, fontSize: 14, whiteSpace: 'pre-wrap' }}>{data.social_content || '—'}</p>
        </div>
      )}

      {tab === 'image' && data.image_path && (
        <div style={{ textAlign: 'center' }}>
          <img src={`/api/static/${data.image_path}`} alt="Campaign" style={{ maxWidth: '100%', borderRadius: 12 }} />
        </div>
      )}
    </div>
  )
}
