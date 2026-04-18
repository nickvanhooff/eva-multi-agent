import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { startCampaign, listPdfs, uploadPdf } from '../api'

const TEMPLATES = {
  product: [
    { label: '📦 Hardware', text: 'Product: [naam]\nDoelgroep: [leeftijd, interesse]\nKernfunctie: [wat doet het]\nUSP: [waarom beter dan alternatief]\nPrijs: [€ en segment]' },
    { label: '💻 Software / App', text: 'App: [naam]\nPlatform: [web / iOS / Android]\nProbleem dat het oplost: [omschrijving]\nBelangrijkste feature: [feature]\nDoelgroep: [type gebruiker]' },
    { label: '🍔 Food & Beverage', text: 'Product: [naam]\nSmaak / samenstelling: [omschrijving]\nDoelgroep: [lifestyle, dieet, leeftijd]\nVerkoop via: [supermarkt / horeca / online]\nUSP: [gezond / duurzaam / gemak]' },
    { label: '👕 Fashion', text: 'Merk: [naam]\nProductlijn: [omschrijving]\nStijl / doelgroep: [type klant]\nPrijs: [segment]\nKernboodschap: [duurzaam / exclusief / casual]' },
    { label: '🔧 B2B / Dienst', text: 'Bedrijf: [naam]\nDienst: [omschrijving]\nDoelklant: [sector, bedrijfsgrootte]\nProbleem dat het oplost: [pijnpunt]\nResultaat voor klant: [meetbaar voordeel]' },
  ],
  book: [
    { label: '📖 Roman / Fictie', text: 'Titel: [naam]\nAuteur: [naam]\nGenre: [thriller / literair / fantasy]\nCentrale belofte: [wat ervaart de lezer]\nDoelgroep: [lezersprofiel]' },
    { label: '📚 Non-fictie', text: 'Titel: [naam]\nAuteur: [naam]\nOnderwerp: [thema]\nWat leert de lezer: [resultaat]\nDoelgroep: [professioneel / breed publiek]' },
    { label: '💼 Business / Zelfhulp', text: 'Titel: [naam]\nAuteur: [naam]\nCentrale these: [kernboodschap]\nVoor wie: [doelgroep]\nBelofte: [concreet resultaat na het lezen]' },
    { label: '🎓 Educatief', text: 'Titel: [naam]\nVak / domein: [omschrijving]\nDoelgroep: [student / professional / niveau]\nLeerdoel: [wat beheers je na het lezen]\nFormaat: [leerboek / werkboek / cursus]' },
  ],
}

export default function NewCampaign() {
  const navigate = useNavigate()
  const [type, setType] = useState('product')
  const [description, setDescription] = useState('')
  const [pdfs, setPdfs] = useState([])
  const [selectedPdf, setSelectedPdf] = useState('')
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    listPdfs().then(setPdfs).catch(() => {})
  }, [])

  async function handleUpload(e) {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    try {
      const res = await uploadPdf(file)
      setPdfs(prev => [...prev, res.filename])
      setSelectedPdf(`data/${res.filename}`)
    } catch {
      setError('Upload failed')
    } finally {
      setUploading(false)
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!description.trim()) { setError('Description is required'); return }
    setLoading(true)
    setError('')
    try {
      const { job_id } = await startCampaign({
        product_description: description,
        campaign_type: type,
        pdf_path: selectedPdf || null,
      })
      navigate(`/campaigns/${job_id}/live`)
    } catch (err) {
      setError(String(err))
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: 32, maxWidth: 720 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>New Campaign</h1>
        <p style={{ color: 'var(--text-muted)', marginTop: 4 }}>Configure and launch a campaign</p>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Type toggle */}
        <div style={{ marginBottom: 24 }}>
          <label style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, display: 'block', marginBottom: 10 }}>Campaign Type</label>
          <div style={{ display: 'flex', gap: 12 }}>
            {['product', 'book'].map(t => (
              <button
                key={t}
                type="button"
                onClick={() => setType(t)}
                style={{
                  flex: 1,
                  padding: '16px',
                  borderRadius: 12,
                  border: `2px solid ${type === t ? 'var(--primary)' : 'var(--border)'}`,
                  background: type === t ? 'rgba(99,102,241,0.1)' : 'var(--surface)',
                  color: type === t ? 'var(--primary)' : 'var(--text-muted)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s',
                }}
              >
                <div style={{ fontWeight: 600, fontSize: 14, textTransform: 'capitalize' }}>{t} Campaign</div>
                <div style={{ fontSize: 12, marginTop: 4 }}>
                  {t === 'product' ? 'Hardware, software, or digital products' : 'Novel, non-fiction, or ebook'}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Description */}
        <div style={{ marginBottom: 24 }}>
          <label style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, display: 'block', marginBottom: 8 }}>
            {type === 'book' ? 'Book' : 'Product'} Description
          </label>

          {/* Template buttons */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 10 }}>
            {TEMPLATES[type].map(t => (
              <button
                key={t.label}
                type="button"
                onClick={() => setDescription(t.text)}
                style={{
                  background: 'var(--surface2)',
                  border: '1px solid var(--border)',
                  borderRadius: 6,
                  padding: '4px 10px',
                  fontSize: 12,
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={e => { e.target.style.borderColor = 'var(--primary)'; e.target.style.color = 'var(--primary)' }}
                onMouseLeave={e => { e.target.style.borderColor = 'var(--border)'; e.target.style.color = 'var(--text-muted)' }}
              >
                {t.label}
              </button>
            ))}
          </div>

          <textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder={type === 'book' ? 'Book title, author, genre, themes...' : 'Product name, features, target audience...'}
            rows={5}
            style={{
              width: '100%',
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 10,
              padding: '12px 14px',
              color: 'var(--text)',
              fontSize: 14,
              resize: 'vertical',
              outline: 'none',
            }}
          />
        </div>

        {/* PDF */}
        <div style={{ marginBottom: 24 }}>
          <label style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, display: 'block', marginBottom: 8 }}>PDF Context (optional)</label>

          {pdfs.length > 0 && (
            <select
              value={selectedPdf}
              onChange={e => setSelectedPdf(e.target.value)}
              style={{ width: '100%', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 12px', color: 'var(--text)', fontSize: 14, marginBottom: 10 }}
            >
              <option value="">— No PDF —</option>
              {pdfs.map(f => <option key={f} value={`data/${f}`}>{f}</option>)}
            </select>
          )}

          <label style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            border: '2px dashed var(--border)',
            borderRadius: 10,
            padding: '24px',
            cursor: 'pointer',
            color: 'var(--text-muted)',
            fontSize: 13,
            gap: 6,
          }}>
            <span style={{ fontSize: 24 }}>📄</span>
            {uploading ? 'Uploading...' : 'Drop PDF here or click to browse'}
            <input type="file" accept=".pdf" onChange={handleUpload} style={{ display: 'none' }} />
          </label>
        </div>

        {/* Model info */}
        <div style={{ background: 'var(--surface2)', borderRadius: 8, padding: '10px 14px', marginBottom: 24, fontSize: 12, color: 'var(--text-muted)' }}>
          <span style={{ color: 'var(--text)' }}>CORE:</span> Researcher & Strateeg → Groq llama-3.1-8b &nbsp;
          <span style={{ color: 'var(--text)' }}>CREATIVE:</span> Copywriter & Social → Groq llama-3.3-70b &nbsp;
          <span style={{ color: 'var(--text)' }}>CM:</span> Groq llama-3.3-70b
        </div>

        {error && <p style={{ color: 'var(--red)', marginBottom: 16, fontSize: 13 }}>{error}</p>}

        <button
          type="submit"
          disabled={loading}
          style={{ width: '100%', background: loading ? 'var(--surface2)' : 'var(--primary)', color: '#fff', border: 'none', borderRadius: 10, padding: '14px', fontWeight: 600, fontSize: 15, cursor: loading ? 'not-allowed' : 'pointer' }}
        >
          {loading ? 'Starting...' : '🚀 Launch Campaign'}
        </button>
      </form>
    </div>
  )
}
