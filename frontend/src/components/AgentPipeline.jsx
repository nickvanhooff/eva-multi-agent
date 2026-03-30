const NODES = [
  { id: 'pdf_ingestion', label: 'PDF', sub: 'Ingestion' },
  { id: 'researcher', label: 'Researcher', sub: '' },
  { id: 'strateeg', label: 'Strateeg', sub: '' },
  { id: 'copywriter', label: 'Copywriter', sub: '' },
  { id: 'social_specialist', label: 'Social', sub: 'Specialist' },
  { id: 'campaign_manager', label: 'Campaign', sub: 'Manager' },
  { id: 'image_generator', label: 'Image', sub: 'Generator' },
]

export default function AgentPipeline({ activeNode, doneNodes = [] }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 0, flexWrap: 'wrap' }}>
      {NODES.map((node, i) => {
        const isDone = doneNodes.includes(node.id)
        const isActive = activeNode === node.id
        return (
          <div key={node.id} style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
              <div style={{
                width: 44,
                height: 44,
                borderRadius: 12,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 18,
                background: isActive ? 'var(--primary)' : isDone ? 'rgba(34,197,94,0.15)' : 'var(--surface2)',
                border: `2px solid ${isActive ? 'var(--primary)' : isDone ? 'var(--green)' : 'var(--border)'}`,
                boxShadow: isActive ? '0 0 16px rgba(99,102,241,0.4)' : 'none',
                transition: 'all 0.3s',
              }}>
                {isDone ? '✓' : isActive ? '⟳' : '○'}
              </div>
              <div style={{ textAlign: 'center', lineHeight: 1.2 }}>
                <div style={{ fontSize: 11, color: isActive ? 'var(--text)' : 'var(--text-muted)', fontWeight: isActive ? 600 : 400 }}>
                  {node.label}
                </div>
                {node.sub && <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{node.sub}</div>}
              </div>
            </div>
            {i < NODES.length - 1 && (
              <div style={{
                width: 24,
                height: 2,
                background: doneNodes.includes(NODES[i + 1].id) || doneNodes.includes(node.id) ? 'var(--green)' : 'var(--border)',
                marginBottom: 20,
                transition: 'background 0.3s',
              }} />
            )}
          </div>
        )
      })}
    </div>
  )
}
