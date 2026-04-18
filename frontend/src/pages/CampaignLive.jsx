import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { resumeCampaign, streamCampaignEvents } from '../api'
import AgentPipeline from '../components/AgentPipeline'

const NODE_LABEL = {
  pdf_ingestion: 'PDF Ingestion',
  mismatch_check: 'Mismatch Check',
  researcher: 'Researcher',
  strateeg: 'Strateeg',
  copywriter: 'Copywriter',
  social_specialist: 'Social Specialist',
  campaign_manager: 'Campaign Manager',
  image_generator: 'Image Generator',
  __system__: 'System',
}

const NODE_COLOR = {
  pdf_ingestion: '#6366f1',
  mismatch_check: '#f59e0b',
  researcher: '#06b6d4',
  strateeg: '#8b5cf6',
  copywriter: '#f59e0b',
  social_specialist: '#ec4899',
  campaign_manager: '#22c55e',
  image_generator: '#f97316',
  __system__: '#64748b',
}

const TYPE_STYLE = {
  node_done:    { icon: '✓', color: 'var(--green)' },
  llm_call:     { icon: '→', color: '#6366f1' },
  llm_response: { icon: '←', color: '#06b6d4' },
  error:        { icon: '✗', color: 'var(--red)' },
}

function LogEntry({ entry, expanded, onToggle }) {
  const style = TYPE_STYLE[entry.type] || { icon: '·', color: 'var(--text-muted)' }
  const hasDetail = entry.data && (entry.data.system_prompt || entry.data.user_prompt || entry.data.preview)

  return (
    <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: 6, marginBottom: 6 }}>
      <div
        style={{ display: 'flex', gap: 8, alignItems: 'flex-start', cursor: hasDetail ? 'pointer' : 'default' }}
        onClick={() => hasDetail && onToggle()}
      >
        <span style={{ color: 'var(--text-muted)', fontSize: 11, flexShrink: 0, paddingTop: 1 }}>
          {new Date(entry.timestamp).toLocaleTimeString('nl')}
        </span>
        <span style={{ color: style.color, flexShrink: 0, fontWeight: 700 }}>{style.icon}</span>
        <span style={{ color: NODE_COLOR[entry.node] || 'var(--text-muted)', fontWeight: 500, fontSize: 12, flexShrink: 0 }}>
          [{NODE_LABEL[entry.node] || entry.node}]
        </span>
        <span style={{ color: 'var(--text)', fontSize: 12 }}>{entry.message}</span>
        {hasDetail && (
          <span style={{ color: 'var(--text-muted)', fontSize: 11, marginLeft: 'auto', flexShrink: 0 }}>
            {expanded ? '▲' : '▼'}
          </span>
        )}
      </div>

      {expanded && hasDetail && (
        <div style={{ marginTop: 8, marginLeft: 80, background: 'var(--surface2)', borderRadius: 6, padding: 10, fontSize: 11 }}>
          {entry.data.system_prompt && (
            <div style={{ marginBottom: 8 }}>
              <div style={{ color: 'var(--text-muted)', marginBottom: 4, fontWeight: 600 }}>SYSTEM PROMPT</div>
              <pre style={{ color: 'var(--text)', whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0, lineHeight: 1.5 }}>
                {entry.data.system_prompt}
              </pre>
            </div>
          )}
          {entry.data.user_prompt && (
            <div style={{ marginBottom: 8 }}>
              <div style={{ color: 'var(--text-muted)', marginBottom: 4, fontWeight: 600 }}>USER PROMPT</div>
              <pre style={{ color: 'var(--text)', whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0, lineHeight: 1.5 }}>
                {entry.data.user_prompt}
              </pre>
            </div>
          )}
          {entry.data.preview && (
            <div>
              <div style={{ color: 'var(--text-muted)', marginBottom: 4, fontWeight: 600 }}>
                RESPONSE {entry.data.length ? `(${entry.data.length} chars)` : ''}
              </div>
              <pre style={{ color: '#22c55e', whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0, lineHeight: 1.5 }}>
                {entry.data.preview}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function CampaignLive() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [activeNode, setActiveNode] = useState(null)
  const [doneNodes, setDoneNodes] = useState([])
  const [logs, setLogs] = useState([])
  const [expandedIdx, setExpandedIdx] = useState(null)
  const [status, setStatus] = useState('queued')
  const [iterations, setIterations] = useState(0)
  const [awaitingInput, setAwaitingInput] = useState(null) // { question, original, suggestion }
  const [selectedOption, setSelectedOption] = useState(null) // 'original' | 'suggestion' | 'custom'
  const [customValue, setCustomValue] = useState('')
  const [resuming, setResuming] = useState(false)
  const logRef = useRef(null)

  useEffect(() => {
    const es = streamCampaignEvents(
      id,
      (event) => {
        if (event.node === '__done__' || event.node === '__error__') return

        // Update pipeline state on node_done
        if (event.type === 'awaiting_input') {
          setStatus('awaiting_input')
          setAwaitingInput(event.data)
          setSelectedOption(null)
          setCustomValue('')
          setLogs(prev => [...prev, event])
          return
        }

        if (event.type === 'node_done' && !event.node.startsWith('__')) {
          setActiveNode(event.node)
          setDoneNodes(prev => prev.includes(event.node) ? prev : [...prev, event.node])
          if (event.data?.iteration_count) setIterations(event.data.iteration_count)
        }

        setStatus('running')
        setLogs(prev => [...prev, event])
      },
      (event) => {
        setActiveNode(null)
        const finalStatus = event.status === 'failed' ? 'failed' : 'done'
        setStatus(finalStatus)
        if (finalStatus === 'done') {
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
            <span style={{
              marginLeft: 10, fontSize: 13, fontWeight: 500,
              color: status === 'done' ? 'var(--green)' : status === 'failed' ? 'var(--red)' : status === 'awaiting_input' ? 'var(--yellow)' : 'var(--primary)',
              background: 'rgba(99,102,241,0.1)', borderRadius: 6, padding: '3px 10px'
            }}>
              ● {status}
            </span>
          </h1>
          <p style={{ color: 'var(--text-muted)', marginTop: 4, fontFamily: 'monospace', fontSize: 11 }}>{id}</p>
        </div>
      </div>

      {/* Pipeline */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 28, marginBottom: 24 }}>
        <AgentPipeline activeNode={activeNode} doneNodes={doneNodes} />
        {iterations > 0 && (
          <div style={{ marginTop: 10, fontSize: 12, color: 'var(--yellow)' }}>↻ Iteration {iterations} — Campaign Manager requested revision</div>
        )}
      </div>

      {/* Active agent card */}
      <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 24, marginBottom: 24 }}>
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>Active Agent</div>
          {activeNode ? (
            <>
              <div style={{ fontSize: 20, fontWeight: 700, color: NODE_COLOR[activeNode] || 'var(--primary)', marginBottom: 4 }}>
                {NODE_LABEL[activeNode]}
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>Processing...</div>
            </>
          ) : (
            <div style={{ color: status === 'done' ? 'var(--green)' : status === 'failed' ? 'var(--red)' : 'var(--text-muted)', fontSize: 13 }}>
              {status === 'done' ? '✓ Completed' : status === 'failed' ? '✗ Failed' : 'Waiting...'}
            </div>
          )}

          <div style={{ marginTop: 16, paddingTop: 12, borderTop: '1px solid var(--border)', fontSize: 11, color: 'var(--text-muted)' }}>
            <div style={{ marginBottom: 4 }}>
              <span style={{ color: '#6366f1' }}>→ llm_call</span> — prompt sent
            </div>
            <div style={{ marginBottom: 4 }}>
              <span style={{ color: '#06b6d4' }}>← llm_response</span> — reply received
            </div>
            <div>
              <span style={{ color: 'var(--green)' }}>✓ node_done</span> — agent completed
            </div>
          </div>
        </div>

        {/* Activity log */}
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>
              Activity Log — click → or ← to expand prompts & responses
            </div>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{logs.length} events</span>
          </div>
          <div ref={logRef} style={{ height: 320, overflowY: 'auto' }}>
            {logs.length === 0 && <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>Waiting for agents...</p>}
            {logs.map((log, i) => (
              <LogEntry
                key={i}
                entry={log}
                expanded={expandedIdx === i}
                onToggle={() => setExpandedIdx(expandedIdx === i ? null : i)}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Human-in-the-loop modal */}
      {awaitingInput && status === 'awaiting_input' && (() => {
        const resolvedValue =
          selectedOption === 'original'   ? awaitingInput.original :
          selectedOption === 'suggestion' ? awaitingInput.suggestion :
          selectedOption === 'custom'     ? customValue : ''
        const canConfirm = !resuming && selectedOption && (selectedOption !== 'custom' || customValue.trim())

        const optionStyle = (key) => ({
          border: `1.5px solid ${selectedOption === key ? 'var(--primary)' : 'var(--border)'}`,
          borderRadius: 10,
          padding: '12px 16px',
          marginBottom: 8,
          cursor: 'pointer',
          background: selectedOption === key ? 'rgba(99,102,241,0.08)' : 'var(--surface2)',
          transition: 'border-color 0.15s, background 0.15s',
        })

        return (
          <div style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200,
          }}>
            <div style={{
              background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 16, padding: 32, maxWidth: 520, width: '90%',
            }}>
              <div style={{ fontSize: 11, color: 'var(--yellow)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12, fontWeight: 600 }}>
                ⚠ Verificatie nodig
              </div>
              <p style={{ color: 'var(--text)', fontSize: 14, lineHeight: 1.6, marginBottom: 24 }}>
                {awaitingInput.question}
              </p>

              {/* Option 1 — original */}
              <div style={optionStyle('original')} onClick={() => setSelectedOption('original')}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                  Mijn originele omschrijving
                </div>
                <div style={{ fontSize: 13, color: 'var(--text)' }}>{awaitingInput.original}</div>
              </div>

              {/* Option 2 — PDF suggestion */}
              <div style={optionStyle('suggestion')} onClick={() => setSelectedOption('suggestion')}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                  PDF-suggestie
                </div>
                <div style={{ fontSize: 13, color: 'var(--text)' }}>{awaitingInput.suggestion}</div>
              </div>

              {/* Option 3 — custom */}
              <div style={optionStyle('custom')} onClick={() => setSelectedOption('custom')}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                  Eigen omschrijving
                </div>
                {selectedOption === 'custom' ? (
                  <input
                    autoFocus
                    type="text"
                    value={customValue}
                    onChange={e => setCustomValue(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === 'Enter' && canConfirm) {
                        setResuming(true)
                        resumeCampaign(id, customValue.trim())
                          .then(() => { setAwaitingInput(null); setSelectedOption(null); setStatus('running'); setResuming(false) })
                          .catch(() => setResuming(false))
                      }
                    }}
                    onClick={e => e.stopPropagation()}
                    placeholder="Typ je eigen omschrijving..."
                    style={{
                      width: '100%', boxSizing: 'border-box', marginTop: 4,
                      background: 'var(--surface)', border: '1px solid var(--border)',
                      borderRadius: 6, padding: '8px 12px', color: 'var(--text)',
                      fontSize: 13, outline: 'none',
                    }}
                  />
                ) : (
                  <div style={{ fontSize: 13, color: 'var(--text-muted)', fontStyle: 'italic' }}>Klik om zelf te typen...</div>
                )}
              </div>

              <button
                disabled={!canConfirm}
                onClick={() => {
                  setResuming(true)
                  resumeCampaign(id, resolvedValue)
                    .then(() => { setAwaitingInput(null); setSelectedOption(null); setStatus('running'); setResuming(false) })
                    .catch(() => setResuming(false))
                }}
                style={{
                  marginTop: 8,
                  width: '100%',
                  background: 'var(--primary)', color: '#fff', border: 'none',
                  borderRadius: 8, padding: '11px 24px', fontSize: 14, fontWeight: 600,
                  cursor: canConfirm ? 'pointer' : 'not-allowed',
                  opacity: canConfirm ? 1 : 0.4,
                  transition: 'opacity 0.15s',
                }}
              >
                {resuming ? 'Bezig...' : 'Bevestigen en doorgaan →'}
              </button>
            </div>
          </div>
        )
      })()}

      {status === 'done' && (
        <div style={{ textAlign: 'center', color: 'var(--green)', fontSize: 14 }}>
          ✓ Campaign completed — redirecting to results...
        </div>
      )}
      {status === 'failed' && (
        <div style={{ textAlign: 'center', color: 'var(--red)', fontSize: 14 }}>
          ✗ Campaign failed
        </div>
      )}
    </div>
  )
}
