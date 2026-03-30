import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getCampaign, getCampaignEvents, imageUrl } from '../api'

const NODE_COLOR = {
  pdf_ingestion: '#6366f1', researcher: '#06b6d4', strateeg: '#8b5cf6',
  copywriter: '#f59e0b', social_specialist: '#ec4899',
  campaign_manager: '#22c55e', image_generator: '#f97316', __system__: '#64748b',
}
const TYPE_STYLE = {
  node_done:    { icon: '✓', color: 'var(--green)' },
  llm_call:     { icon: '→', color: '#6366f1' },
  llm_response: { icon: '←', color: '#06b6d4' },
  error:        { icon: '✗', color: 'var(--red)' },
}

function LogLine({ entry, expanded, onToggle }) {
  const style = TYPE_STYLE[entry.type] || { icon: '·', color: 'var(--text-muted)' }
  const hasDetail = entry.data && (entry.data.system_prompt || entry.data.user_prompt || entry.data.preview)
  return (
    <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: 6, marginBottom: 6 }}>
      <div style={{ display: 'flex', gap: 8, cursor: hasDetail ? 'pointer' : 'default' }} onClick={() => hasDetail && onToggle()}>
        <span style={{ color: 'var(--text-muted)', fontSize: 11, flexShrink: 0 }}>
          {new Date(entry.timestamp).toLocaleTimeString('nl')}
        </span>
        <span style={{ color: style.color, fontWeight: 700, flexShrink: 0 }}>{style.icon}</span>
        <span style={{ color: NODE_COLOR[entry.node] || 'var(--text-muted)', fontWeight: 500, fontSize: 12, flexShrink: 0 }}>
          [{entry.node}]
        </span>
        <span style={{ color: 'var(--text)', fontSize: 12 }}>{entry.message}</span>
        {hasDetail && <span style={{ color: 'var(--text-muted)', fontSize: 11, marginLeft: 'auto' }}>{expanded ? '▲' : '▼'}</span>}
      </div>
      {expanded && hasDetail && (
        <div style={{ marginTop: 8, marginLeft: 60, background: 'var(--surface2)', borderRadius: 6, padding: 10, fontSize: 11 }}>
          {entry.data.system_prompt && (
            <div style={{ marginBottom: 8 }}>
              <div style={{ color: 'var(--text-muted)', fontWeight: 600, marginBottom: 4 }}>SYSTEM PROMPT</div>
              <pre style={{ color: 'var(--text)', whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0, lineHeight: 1.5 }}>{entry.data.system_prompt}</pre>
            </div>
          )}
          {entry.data.user_prompt && (
            <div style={{ marginBottom: 8 }}>
              <div style={{ color: 'var(--text-muted)', fontWeight: 600, marginBottom: 4 }}>USER PROMPT</div>
              <pre style={{ color: 'var(--text)', whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0, lineHeight: 1.5 }}>{entry.data.user_prompt}</pre>
            </div>
          )}
          {entry.data.preview && (
            <div>
              <div style={{ color: 'var(--text-muted)', fontWeight: 600, marginBottom: 4 }}>
                RESPONSE {entry.data.length ? `(${entry.data.length} chars)` : ''}
              </div>
              <pre style={{ color: '#22c55e', whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0, lineHeight: 1.5 }}>{entry.data.preview}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function CampaignResults() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [events, setEvents] = useState([])
  const [tab, setTab] = useState('strategy')
  const [loading, setLoading] = useState(true)
  const [expandedIdx, setExpandedIdx] = useState(null)

  useEffect(() => {
    getCampaign(decodeURIComponent(id))
      .then(job => { setData(job.result || job); setLoading(false) })
      .catch(() => setLoading(false))

    getCampaignEvents(decodeURIComponent(id))
      .then(res => setEvents(res.events || []))
      .catch(() => {})
  }, [id])

  if (loading) return <div style={{ padding: 32, color: 'var(--text-muted)' }}>Loading...</div>
  if (!data) return (
    <div style={{ padding: 32 }}>
      <p style={{ color: 'var(--red)' }}>Campaign not found</p>
      <button onClick={() => navigate('/')} style={{ marginTop: 12, background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer' }}>← Back</button>
    </div>
  )

  const tabs = ['strategy', 'copy', 'social']
  if (data.image_path) tabs.push('image')
  if (events.length > 0) tabs.push('logs')

  return (
    <div style={{ padding: 32 }}>
      <button onClick={() => navigate(-1)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', marginBottom: 16 }}>← Back</button>

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
          <img
            src={imageUrl(data.image_path)}
            alt="Campaign visual"
            style={{ maxWidth: 600, width: '100%', borderRadius: 12, border: '1px solid var(--border)' }}
            onError={e => { e.target.style.display = 'none' }}
          />
          <p style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 8 }}>{data.image_path}</p>
        </div>
      )}

      {tab === 'logs' && (
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>
              Agent Logs — click → or ← to expand
            </div>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{events.length} events</span>
          </div>
          <div style={{ maxHeight: 600, overflowY: 'auto' }}>
            {events.map((e, i) => (
              <LogLine
                key={i}
                entry={e}
                expanded={expandedIdx === i}
                onToggle={() => setExpandedIdx(expandedIdx === i ? null : i)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
