import { useEffect, useState } from 'react'
import { getConfig, saveConfig } from '../api'

const AGENT_LABELS = {
  researcher: 'Researcher',
  strateeg: 'Strategist',
  copywriter: 'Copywriter',
  social_specialist: 'Social Specialist',
  campaign_manager: 'Campaign Manager',
  website_generator: 'Website Generator',
}

const ITERATION_OPTIONS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

const card = {
  background: 'var(--surface)',
  border: '1px solid var(--border)',
  borderRadius: 12,
  padding: 24,
}

const inputStyle = {
  width: '100%',
  background: 'var(--surface2)',
  border: '1px solid var(--border)',
  borderRadius: 8,
  padding: '8px 10px',
  color: 'var(--text)',
  fontSize: 13,
}

function cloneBaseline(cfg) {
  return {
    max_iterations: cfg.max_iterations ?? 3,
    agents: JSON.parse(JSON.stringify(cfg.agents || {})),
  }
}

function normalizeAgents(agents, options, recommendedByAgent) {
  const out = JSON.parse(JSON.stringify(agents))
  for (const key of Object.keys(out)) {
    const row = out[key]
    if (!row) continue
    const provider = row.provider || 'groq'
    const { all } = buildModelSelect(key, provider, options, recommendedByAgent, row.model)
    if (!row.model && all.length) {
      row.model = all[0]
    }
  }
  return out
}

/** All pickable models + recommended subset for optgroups. */
function buildModelSelect(agentKey, provider, modelOptions, recommendedByAgent, currentModel) {
  const allRaw = modelOptions[provider] || []
  const recommended = recommendedByAgent?.[agentKey]?.[provider] || []
  const seen = new Set()
  const all = []
  for (const m of [...recommended, ...(currentModel ? [currentModel] : []), ...allRaw]) {
    if (m && !seen.has(m)) {
      seen.add(m)
      all.push(m)
    }
  }
  const recSet = new Set(recommended)
  if (currentModel) recSet.add(currentModel)
  const recommendedList = all.filter((m) => recSet.has(m))
  const other = all.filter((m) => !recSet.has(m))
  return { all, recommended: recommendedList, other }
}

export default function ConfigPage() {
  const [agents, setAgents] = useState({})
  const [maxIterations, setMaxIterations] = useState(3)
  const [baseline, setBaseline] = useState(null)
  const [providers, setProviders] = useState(['groq', 'openrouter', 'ollama'])
  const [modelOptions, setModelOptions] = useState({})
  const [recommendedByAgent, setRecommendedByAgent] = useState({})
  const [agentKeys, setAgentKeys] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  function applyConfigToState(cfg) {
    const options = cfg.model_options || {}
    const saved = cfg.saved || { max_iterations: cfg.max_iterations, agents: cfg.agents }
    const snap = cloneBaseline(saved)
    const recommended = cfg.recommended_models || {}
    const active = normalizeAgents(cfg.agents || snap.agents, options, recommended)
    setAgents(active)
    setMaxIterations(cfg.max_iterations ?? snap.max_iterations)
    setBaseline(snap)
    setProviders(cfg.valid_providers || ['groq', 'openrouter', 'ollama'])
    setModelOptions(options)
    setRecommendedByAgent(recommended)
    setAgentKeys(cfg.agent_keys || Object.keys(active))
  }

  async function load() {
    setLoading(true)
    setError('')
    try {
      const cfg = await getConfig()
      applyConfigToState(cfg)
    } catch (e) {
      setError(e.message || 'Could not load config')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  function updateAgent(key, field, value) {
    setAgents((prev) => ({
      ...prev,
      [key]: { ...prev[key], [field]: value },
    }))
  }

  function updateProvider(key, provider) {
    const current = agents[key]?.model
    const { all, recommended } = buildModelSelect(key, provider, modelOptions, recommendedByAgent, current)
    const nextModel =
      (current && all.includes(current) ? current : null) ||
      recommended[0] ||
      all[0] ||
      current ||
      ''
    setAgents((prev) => ({
      ...prev,
      [key]: { ...prev[key], provider, model: nextModel },
    }))
  }

  function handleRevert() {
    if (!baseline) return
    setAgents(JSON.parse(JSON.stringify(baseline.agents)))
    setMaxIterations(baseline.max_iterations)
    setMessage('Reverted to last saved configuration.')
    setError('')
  }

  async function handleSave(e) {
    e.preventDefault()
    setSaving(true)
    setMessage('')
    setError('')
    try {
      const payload = {
        max_iterations: Number(maxIterations),
        agents: normalizeAgents(agents, modelOptions, recommendedByAgent),
      }
      const cfg = await saveConfig(payload)
      applyConfigToState(cfg)
      setMessage('Saved — new campaigns use these settings.')
    } catch (e) {
      setError(e.message || 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  const keys = agentKeys.length ? agentKeys : Object.keys(agents)
  const dirty =
    baseline &&
    (Number(maxIterations) !== baseline.max_iterations ||
      JSON.stringify(agents) !== JSON.stringify(baseline.agents))

  return (
    <div style={{ padding: 32, maxWidth: 960 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Configuration</h1>
        <p style={{ color: 'var(--text-muted)', marginTop: 4 }}>
          Pick provider and model per agent. <strong style={{ color: 'var(--text)', fontWeight: 500 }}>Save</strong> writes
          to the server; agents read that on each run. Revert undoes unsaved edits.
        </p>
      </div>

      {loading ? (
        <p style={{ color: 'var(--text-muted)' }}>Loading…</p>
      ) : (
        <form onSubmit={handleSave}>
          <div style={{ ...card, marginBottom: 20 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
              Campaign manager
            </div>
            <label htmlFor="max-iterations" style={{ display: 'block', fontSize: 13, color: 'var(--text-muted)', marginBottom: 6 }}>
              Max review iterations
            </label>
            <select
              id="max-iterations"
              value={String(maxIterations)}
              onChange={(e) => setMaxIterations(Number(e.target.value))}
              style={{ ...inputStyle, maxWidth: 120 }}
            >
              {ITERATION_OPTIONS.map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </div>

          <div style={card}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 16, textTransform: 'uppercase', letterSpacing: 1 }}>
              Agents
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ color: 'var(--text-muted)', textAlign: 'left' }}>
                    <th style={{ padding: '8px 12px 12px 0', fontWeight: 500 }}>Agent</th>
                    <th style={{ padding: '8px 12px 12px 0', fontWeight: 500 }}>Provider</th>
                    <th style={{ padding: '8px 12px 12px 0', fontWeight: 500 }}>Model</th>
                    <th style={{ padding: '8px 0 12px', fontWeight: 500, minWidth: 140 }}>Temperature</th>
                  </tr>
                </thead>
                <tbody>
                  {keys.map((key) => {
                    const row = agents[key] || {}
                    const provider = row.provider || 'groq'
                    const { all, recommended, other } = buildModelSelect(
                      key,
                      provider,
                      modelOptions,
                      recommendedByAgent,
                      row.model,
                    )
                    const modelValue = row.model && all.includes(row.model) ? row.model : recommended[0] || all[0] || ''

                    return (
                      <tr key={key} style={{ borderTop: '1px solid var(--border)' }}>
                        <td style={{ padding: '14px 12px 14px 0', fontWeight: 500, whiteSpace: 'nowrap