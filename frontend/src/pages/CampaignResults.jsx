import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { getCampaign, getCampaignEvents, imageUrl, generateWebsite, websiteUrl } from '../api'

const mdStyle = {
  color: 'var(--text)',
  lineHeight: 1.8,
  fontSize: 14,
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
    <div style={{ padding: 32 }}>\n      <p style={{ color: 'var(--red)' }}>Campaign not found</p>\n      <button onClick={() => navigate('/')} style={{ marginTop: 12, background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer' }}>← Back</button>\n    </div>\n  )

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

  const tabLabels = {
    strategy: 'Strategy',
    copy: 'Marketing Copy',
    social: 'Social Content',
    image: 'Visual',
    sources: 'Sources',
    logs: 'Agent Logs',
    website: 'Website',
  }

  return (
    <div style={{ padding: '32px 24px', maxWidth: '1200px', margin: '0 auto' }}>\n      {/* Back button */}\n      <button
        onClick={() => navigate(-1)}
        style={{\n          background: 'none',\n          border: 'none',\n          color: 'var(--text-muted)',\n          cursor: 'pointer',\n          marginBottom: '24px',\n          fontSize: '14px',\n          fontWeight: 500,\n          display: 'inline-flex',\n          alignItems: 'center',\n          gap: '6px',\n          padding: '8px 12px',\n          borderRadius: '8px',\n          transition: 'background 0.15s, color 0.15s',\n        }}
        onMouseEnter={e => { e.target.style.background = 'var(--surface2)'; e.target.style.color = 'var(--text)' }}
        onMouseLeave={e => { e.target.style.background = 'none'; e.target.style.color = 'var(--text-muted)' }}
      >\n        ← Back\n      </button>\n\n      {/* Header */}\n      <div style={{ marginBottom: '32px' }}>\n        <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '16px', lineHeight: 1.2, color: 'var(--text)' }}>
          {(data.product_description || '').slice(0, 80)}{(data.product_description || '').length > 80 ? '…' : ''}
        </h1>\n        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '20px' }}>\n          <span style={{ background: 'rgba(99,102,241,0.15)', color: 'var(--primary)', borderRadius: '999px', padding: '6px 14px', fontSize: '12px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            {data.campaign_type || 'product'}
          </span>\n          <span style={{ color: data.approved_by_cm ? 'var(--green)' : 'var(--text-muted)', fontSize: '14px', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '6px' }}>
            {data.approved_by_cm ? '●' : '○'} {data.approved_by_cm ? 'Approved' : 'Pending'} CM\n          </span>\n          <span style={{ color: 'var(--text-muted)', fontSize: '14px', fontWeight: 500 }}>
            {data.iterations ?? '—'} iteration{data.iterations !== 1 ? 's' : ''}\n          </span>\n        </div>\n\n        {/* Prominent Generate Website Button */}\n        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>\n          <button\n            onClick={handleGenerateWebsite}\n            disabled={generatingWebsite}\n            style={{\n              background: generatingWebsite ? 'var(--surface2)' : 'var(--primary)',\n              color: generatingWebsite ? 'var(--text-muted)' : '#fff',\n              border: 'none',\n              borderRadius: '12px',\n              padding: '14px 28px',\n              fontSize: '15px',\n              fontWeight: '600',\n              cursor: generatingWebsite ? 'not-allowed' : 'pointer',\n              display: 'inline-flex',\n              alignItems: 'center',\n              gap: '10px',\n              boxShadow: generatingWebsite ? 'none' : '0 4px 14px rgba(99, 102, 241, 0.35), 0 2px 4px rgba(99, 102, 241, 0.2)',\n              transition: 'transform 0.1s, box-shadow 0.15s, background 0.15s',\n              minWidth: '200px',\n              justifyContent: 'center',\n            }}\n            onMouseEnter={e => {\n              if (!generatingWebsite) {\n                e.target.style.transform = 'translateY(-1px)';\n                e.target.style.boxShadow = '0 6px 20px rgba(99, 102, 241, 0.4), 0 3px 6px rgba(99, 102, 241, 0.25)';\n              }\n            }}\n            onMouseLeave={e => {\n              if (!generatingWebsite) {\n                e.target.style.transform = 'translateY(0)';\n                e.target.style.boxShadow = '0 4px 14px rgba(99, 102, 241, 0.35), 0 2px 4px rgba(99, 102, 241, 0.2)';\n              }\n            }}\n            onMouseDown={e => {\n              if (!generatingWebsite) e.target.style.transform = 'translateY(0)';\n            }}\n          >\n            <span style={{ display: 'inline-flex', alignItems: 'center' }}>
              {generatingWebsite ? (
                <svg width="18" height="18" viewBox="0 0 24 24" style={{ animation: 'spin 1s linear infinite' }}>
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" strokeDasharray="31.4 31.4" strokeLinecap="round" />
                  <style jsx>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><path d="M9 9h6v6"/><path d="M15 15l3 3"/></svg>
              )}
            </span>\n            {generatingWebsite ? 'Generating…' : 'Generate Website'}\n          </button>\n          {websiteError && (\n            <span style={{ color: 'var(--red)', fontSize: '13px', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '6px' }}>\n              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>\n              {websiteError}\n            </span>\n          )}\n        </div>\n      </div>\n\n      {/* Tabs - modern pill style */}\n      <div style={{ display: 'flex', gap: '6px', borderBottom: '1px solid var(--border)', marginBottom: '28px', paddingBottom: '4px' }}>\n        {tabs.map(t => (\n          <button\n            key={t}\n            onClick={() => setTab(t)}\n            style={{\n              background: tab === t ? 'rgba(99,102,241,0.12)' : 'transparent',\n              border: 'none',\n              borderBottom: 'none',\n              color: tab === t ? 'var(--primary)' : 'var(--text-muted)',\n              padding: '12px 20px',\n              cursor: 'pointer',\n              fontWeight: tab === t ? 600 : 500,\n              fontSize: '14px',\n              borderRadius: '10px 10px 0 0',\n              transition: 'all 0.15s',\n              position: 'relative',\n              marginBottom: '-1px',\n            }}\n            onMouseEnter={e => {\n              if (tab !== t) e.target.style.background = 'var(--surface2)';\n            }}\n            onMouseLeave={e => {\n              if (tab !== t) e.target.style.background = 'transparent';\n            }}\n          >\n            {tabLabels[t] || t}\n          </button>\n        ))}\n      </div>\n\n      {/* Content panels with elevated cards */}\n      {tab === 'strategy' && (\n        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>\n          {[
            { label: 'Target Audience', value: data.target_audience, cited: true },
            { label: 'Positioning', value: data.positioning },
            { label: 'Tone of Voice', value: data.tone_of_voice },
          ].map(({ label, value, cited }) => (\n            <div key={label} style={cardStyle}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '12px', fontWeight: 600 }}>{label}</div>\n              {cited && data.pdf_sources?.length > 0
                ? <CitedText text={value} sources={data.pdf_sources} />
                : <div style={mdStyle}>{value}</div>}
            </div>\n          ))}\n        </div>\n      )}\n\n      {tab === 'copy' && (\n        <div style={cardStyle}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '16px', fontWeight: 600 }}>Marketing Copy</div>\n          <div style={mdStyle}>{data.copy_draft}</div>\n        </div>\n      )}\n\n      {tab === 'social' && (\n        <div style={cardStyle}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '16px', fontWeight: 600 }}>Social Content</div>\n          <div style={mdStyle}>{data.social_content}</div>\n        </div>\n      )}\n\n      {tab === 'sources' && data.pdf_sources && (\n        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>\n          <div style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 500 }}>
            {data.pdf_sources.length} passage{data.pdf_sources.length !== 1 ? 's' : ''} retrieved from PDF via RAG\n          </div>\n          {data.pdf_sources.map((src, i) => (\n            <div key={i} style={cardStyle}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', paddingBottom: '12px', borderBottom: '1px solid var(--border)' }}>\n                <span style={{ fontSize: '11px', color: 'var(--primary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px' }}>\n                  Passage {i + 1}\n                </span>\n                {src.page != null && (\n                  <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 500 }}>\n                    Page {src.page + 1}\n                  </span>\n                )}\n              </div>\n              <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic', marginBottom: '12px' }}>\n                Query: {src.query}\n              </div>\n              <pre style={{ color: 'var(--text)', whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0, lineHeight: 1.7, fontSize: '13px', fontFamily: 'inherit' }}>\n                {src.text}\n              </pre>\n            </div>\n          ))}\n        </div>\n      )}\n\n      {tab === 'image' && data.image_path && (\n        <div style={{ textAlign: 'center' }}>\n          <img\n            src={imageUrl(data.image_path)}\n            alt="Campaign visual"\n            style={{ maxWidth: '100%', width: '100%', maxWidth: 720, borderRadius: '16px', border: '1px solid var(--border)', boxShadow: '0 8px 30px rgba(0,0,0,0.12)' }}\
            onError={e => { e.target.style.display = 'none' }}
          />\n          <p style={{ color: 'var(--text-muted)', fontSize: '12px', marginTop: '12px' }}>{data.image_path}</p>\n        </div>\n      )}\n\n      {tab === 'logs' && (\n        <div style={cardStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', paddingBottom: '16px', borderBottom: '1px solid var(--border)' }}>\n            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 600 }}>Agent Logs</div>\n            <span style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 500 }}>{events.length} events</span>\n          </div>\n          <div style={{ maxHeight: 600, overflowY: 'auto' }}>\n            {events.map((e, i) => (\n              <LogLine\n                key={i}\n                entry={e}\n                expanded={expandedIdx === i}\n                onToggle={() => setExpandedIdx(expandedIdx === i ? null : i)}\n              />\n            ))}\n          </div>\n        </div>\n      )}\n\n      {tab === 'website' && generatedWebsiteUrl && (\n        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>\n          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>\n            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 600 }}>Generated Landing Page</div>\n            <a\n              href={generatedWebsiteUrl}\n              target="_blank"\n              rel="noopener noreferrer"\n              style={{\n                fontSize: '13px',\n                color: 'var(--primary)',\n                textDecoration: 'none',\n                fontWeight: 600,\n                display: 'inline-flex',\n                alignItems: 'center',\n                gap: '6px',\n                padding: '8px 16px',\n                background: 'rgba(99,102,241,0.1)',\n                borderRadius: '8px',\n                transition: 'background 0.15s',\n              }}\n              onMouseEnter={e => e.target.style.background = 'rgba(99,102,241,0.2)'}\n              onMouseLeave={e => e.target.style.background = 'rgba(99,102,241,0.1)'}\n            >\n              Open in new tab\n              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>\n            </a>\n          </div>\n          <iframe\n            src={generatedWebsiteUrl}\n            sandbox="allow-scripts allow-same-origin"\n            style={{\n              width: '100%', height: 720,\n              border: '1px solid var(--border)',\n              borderRadius: '16px',\n              background: '#fff',\n              boxShadow: '0 4px 24px rgba(0,0,0,0.08)',\n            }}\n            title="Generated website preview"\n          />\n        </div>\n      )}\n    </div>\n  )\n}\n\nconst cardStyle = {\n  background: 'var(--surface)',\n  border: '1px solid var(--border)',\n  borderRadius: '16px',\n  padding: '24px',\n  boxShadow: '0 2px 8px rgba(0,0,0,0.04), 0 1px 3px rgba(0,0,0,0.06)',\n  transition: 'box-shadow 0.2s, border-color 0.2s',\n}
