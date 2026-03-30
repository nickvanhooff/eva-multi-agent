const BASE = '/api'

// Convert stored image_path (e.g. "campaigns/images/xxx.png") to a URL
// API mounts campaigns/ at /static, so strip the "campaigns/" prefix
export function imageUrl(imagePath) {
  if (!imagePath) return null
  const relative = imagePath.replace(/^campaigns[\\/]/, '')
  return `${BASE}/static/${relative.replace(/\\/g, '/')}`
}

export async function startCampaign(body) {
  const res = await fetch(`${BASE}/campaigns`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getCampaign(jobId) {
  const res = await fetch(`${BASE}/campaigns/${jobId}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getCampaignEvents(jobId) {
  const res = await fetch(`${BASE}/campaigns/${jobId}/events`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export function streamCampaignEvents(jobId, onEvent, onDone) {
  const es = new EventSource(`${BASE}/campaigns/${jobId}/stream`)
  es.onmessage = (e) => {
    const event = JSON.parse(e.data)
    onEvent(event)
    if (event.node === '__done__' || event.node === '__error__') {
      es.close()
      onDone(event)
    }
  }
  es.onerror = () => { es.close(); onDone({ node: '__error__', status: 'failed' }) }
  return es
}

export async function listCampaigns() {
  const res = await fetch(`${BASE}/campaigns`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function listPdfs() {
  const res = await fetch(`${BASE}/pdfs`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function uploadPdf(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/pdfs/upload`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
