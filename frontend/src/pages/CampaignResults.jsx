import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { getCampaign, getCampaignEvents, imageUrl, generateWebsite, websiteUrl } from '../api'

const mdStyle = {
  color: 'var(--text)',
  lineHeight: 1.8,
  fontSize: 14,
}

function Md({ children }) {
  if (!children) return <span style={{ color: 'var(--text-muted)' }}>—</span>
  return (
    <div style={mdStyle} className="md-content">
      <ReactMarkdown>{children}</ReactMarkdown>
    </div>
  )
}

function CitedText({ text, sources }) {
  const [tooltip, setTooltip] = useState(null)
  const ref = useRef(null)

  useEffect(() => {
    const close = e => { if (ref.current && !ref.current.contains(e.target)) setTooltip(null) }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])

  if (!sources || sources.length === 0 || !text) return <Md>{text}</Md>

  // Split on [Bron: N] markers
  const parts = text.split(/(\[Bron:\s*\d+\])/g)
  const rendered = parts.map((part, i) => {
    const match = part.match(/\[Bron:\s*(\d+)\]/)
    if (!match) return <span key={i}>{part}</span>
    const idx = parseInt(match[1], 10) - 1
    const src = sources[idx]
    if (!src) return null
    return (
      <span key={i} style={{ position: 'relative', display: 'inline' }} ref={ref}>
        <button
          onClick={() => setTooltip(tooltip === i ? null : i)}
          title={`Passage ${idx + 1}`}
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0 2px', color: 'var(--primary)', fontSize: 13, lineHeight: 1 }}
        >ℹ</button>
        {tooltip === i && (
          <div style={{
            position: 'absolute', zIndex: 100, bottom: '120%', left: 0,
            background: 'var(--surface2)', border: '1px solid var(--border)',
            borderRadius: 8, padding: 12, width: 320, boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
          }}>
            <div style={{ fontSize: 11, color: 'var(--primary)', fontWeight: 600, marginBottom: 6 }}>
              Passage {idx + 1}{src.page != null ? ` · pagina ${src.page + 1}` : ''}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', fontStyle: 'italic', marginBottom: 8 }}>
              {src.query}
            </div>
            <pre style={{ fontSize: 12, color: 'var(--text)', whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0, lineHeight: 1.6 }}>
              {src.text}
            </pre>
          </div>
        )}
      </span>
    )
  })

  return <div style={{ ...mdStyle, whiteSpace: 'pre-wrap' }}>{rendered}</div>
}

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
  const [generatingWebsite, setGeneratingWebsite] = useState(false)
  const [generatedWebsiteUrl, setGeneratedWebsiteUrl] = useState(null)
  const [websiteError, setWebsiteError] = useState(null)

  useEffect(() => {
    getCampaign(decodeURIComponent(id))
      .then(job => {
        const result = job.result || job
        setData(result)
        setLoading(false)
        if (result?.html_path) {
          setGeneratedWebsiteUrl(websiteUrl(result.html_path))
        }
      })
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

  async function handleGenerateWebsite() {
    setGeneratingWebsite(true)
    setWebsiteError(null)
    try {
      const res = await generateWebsite(decodeURIComponent(id))
      setGeneratedWebsiteUrl(websiteUrl(res.html_path))
      setTab('website')
    } catch (e) {
      setWebsiteError(e.message)
    } finally {
      setGeneratingWebsite(false)
    }
  }

  const tabs = ['strategy', 'copy', 'social']
  if (data.image_path) tabs.push('image')
  if (data.pdf_sources && data.pdf_sources.length > 0) tabs.push('sources')
  if (events.length > 0) tabs.push('logs')
  if (generatedWebsiteUrl) tabs.push('website')

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
          <button
            onClick={handleGenerateWebsite}
            disabled={generatingWebsite}
            style={{
              marginLeft: 'auto',
              background: generatingWebsite ? 'var(--surface2)' : 'var(--primary)',
              color: generatingWebsite ? 'var(--text-muted)' : '#fff',
              border: 'none', borderRadius: 8,
              padding: '6px 16px', fontSize: 13, fontWeight: 600,
              cursor: generatingWebsite ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', gap: 6,
            }}
          >
            {generatingWebsite ? 'Generating...' : '⚡ Generate Website'}
          </button>
          {websiteError && (
            <span style={{ color: 'var(--red)', fontSize: 12 }}>{websiteError}</span>
          )}
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
            { label: 'Target Audience', value: data.target_audience, cited: true },
            { label: 'Positioning', value: data.positioning },
            { label: 'Tone of Voice', value: data.tone_of_voice },
          ].map(({ label, value, cited }) => (
            <div key={label} style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 20 }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>{label}</div>
              {cited && data.pdf_sources?.length > 0
                ? <CitedText text={value} sources={data.pdf_sources} />
                : <Md>{value}</Md>}
            </div>
          ))}
          <div style={{ gridColumn: '1/-1', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 20 }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Strategy</div>
            <Md>{data.strategy}</Md>
          </div>
        </div>
      )}

      {tab === 'copy' && (
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 24 }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>Marketing Copy</div>
          <Md>{data.copy_draft}</Md>
        </div>
      )}

      {tab === 'social' && (
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 24 }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>Social Content</div>
          <Md>{data.social_content}</Md>
        </div>
      )}

      {tab === 'sources' && data.pdf_sources && (
        <div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 16 }}>
            {data.pdf_sources.length} passages opgehaald uit PDF via RAG
          </div>
          {data.pdf_sources.map((src, i) => (
            <div key={i} style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 20, marginBottom: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span style={{ fontSize: 11, color: 'var(--primary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
                  Passage {i + 1}
                </span>
                {src.page != null && (
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    pagina {src.page + 1}
                  </span>
                )}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', fontStyle: 'italic', marginBottom: 10 }}>
                Vraag: {src.query}
              </div>
              <pre style={{ color: 'var(--text)', whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0, lineHeight: 1.7, fontSize: 13 }}>
                {src.text}
              </pre>
            </div>
          ))}
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

      {tab === 'website' && generatedWebsiteUrl && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>
              Generated Landing Page
            </div>
            <a
              href={generatedWebsiteUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: 12, color: 'var(--primary)', textDecoration: 'none' }}
            >
              Open in new tab ↗
            </a>
          </div>
          <iframe
            src={generatedWebsiteUrl}
            sandbox="allow-scripts allow-same-origin"
            style={{
              width: '100%', height: 680,
              border: '1px solid var(--border)',
              borderRadius: 12, background: '#fff',
            }}
            title="Generated website preview"
          />
        </div>
      )}
    </div>
  )
}
