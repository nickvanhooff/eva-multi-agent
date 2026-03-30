import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { streamCampaignEvents } from '../api'
import AgentPipeline from '../components/AgentPipeline'

const NODE_LABEL = {
  pdf_ingestion: 'PDF Ingestion',
  researcher: 'Researcher',
  strateeg: 'Strateeg',
  copywriter: 'Copywriter',
  social_specialist: 'Social Specialist',
  campaign_manager: 'Campaign Manager',
  image_generator: 'Image Generator',
}

const NODE_COLOR = {
  pdf_ingestion: '#6366f1',
  researcher: '#06b6d4',
  strateeg: '#8b5cf6',
  copywriter: '#f59e0b',
  social_specialist: '#ec4899',
  campaign_manager: '#22c55e',
  image_generator: '#f97316',
}

export default function CampaignLive() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [activeNode, setActiveNode] = useState(null)
  const [doneNodes, setDoneNodes] = useState([])
  const [logs, setLogs] = useState([])
  const [status, setStatus] = useState('queued')
  const [iterations, setIterations] = useState(0)
  const logRef = useRef(null)

  useEffect(() => {
    const es = streamCampaignEvents(
      id,
      (event) => {
        const { node, status: s, data } = event
        if (node === '__done__' || node === '__error__') return

        setActiveNode(node)
        setDoneNodes(prev => prev.includes(node) ? prev : [...prev, node])
        setStatus('running')

        if (data?.iteration_count) setIterations(data.iteration_count)

        const label = NODE_LABEL[node] || node
        const summary = Object.entries(data || {})
          .filter(([, v]) => v && typeof v === 'string' && v.length < 80)
          .map(([k]) => k)
          .join(', ')

        setLogs(prev => [...prev, {
          time: new Date().toLocaleTimeString('nl'),
          node,
          label,
          text: summary ? `${label} completed (${summary})` : `${label} completed`,
        }])
      },
      (event) => {
        setActiveNode(null)
        setStatus(event.status === 'failed' ? 'failed' : 'done')
        if (event.status !== 'failed') {
          setTimeout(() => navigate(`/campaigns/${id}`), 1500)
        }
      }
    )
    return () => es.close()
  }, [id])

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [logs])

  return (
    <div style={{ padding: 32 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}>
        <button onClick={() => navigate('/')} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>← Back</button>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>
            Campaign Running
            <span style={{ marginLeft: 10, fontSize: 13, fontWeight: 500, color: status === 'done' ? 'var(--green)' : status === 'failed' ? 'var(--red)' : 'var(--primary)', background: 'rgba(99,102,241,0.1)', borderRadius: 6, padding: '3px 10px' }}>
              ● {status}
            </span>
          </h1>
          <p style={{ color: 'var(--text-muted)', marginTop: 4, fontFamily: 'monospace', fontSize: 12 }}>{id}</p>
        </div>
      </div>

      {/* Pipeline */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 28, marginBottom: 24 }}>
        <AgentPipeline activeNode={activeNode} doneNodes={doneNodes} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Active agent */}
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 24 }}>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 16 }}>Active Agent</div>
          {activeNode ? (
            <>
              <div style={{ fontSize: 24, fontWeight: 700, color: NODE_COLOR[activeNode] || 'var(--primary)', marginBottom: 6 }}>
                {NODE_LABEL[activeNode]}
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>Processing...</div>
              {iterations > 0 && (
                <div style={{ marginTop: 12, fontSize: 12, color: 'var(--yellow)' }}>↻ Iteration {iterations}</div>
              )}
            </>
          ) : (
            <div style={{ color: 'var(--text-muted)' }}>{status === 'done' ? '✓ Completed' : status === 'failed' ? '✗ Failed' : 'Waiting...'}</div>
          )}
        </div>

        {/* Activity log */}
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 24 }}>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>Activity Log</div>
          <div ref={logRef} style={{ height: 160, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}>
            {logs.length === 0 && <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>Waiting for agents...</p>}
            {logs.map((log, i) => (
              <div key={i} style={{ fontSize: 12, display: 'flex', gap: 8 }}>
                <span style={{ color: 'var(--text-muted)', flexShrink: 0 }}>{log.time}</span>
                <span style={{ color: NODE_COLOR[log.node] || 'var(--text)', fontWeight: 500 }}>[{log.label}]</span>
                <span style={{ color: 'var(--text-muted)' }}>{log.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {status === 'done' && (
        <div style={{ marginTop: 20, textAlign: 'center', color: 'var(--green)', fontSize: 14 }}>
          ✓ Campaign completed — redirecting to results...
        </div>
      )}
      {status === 'failed' && (
        <div style={{ marginTop: 20, textAlign: 'center', color: 'var(--red)', fontSize: 14 }}>
          ✗ Campaign failed — check logs above
        </div>
      )}
    </div>
  )
}
