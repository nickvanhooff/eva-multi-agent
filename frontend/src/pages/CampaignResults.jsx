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
  const { jobId } = useParams()
  const navigate = useNavigate()
  const [campaign, setCampaign] = useState(null)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    async function load() {
      const data = await getCampaign(jobId)
      setCampaign(data)
    }
    load()
  }, [jobId])

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      const result = await generateWebsite(jobId)
      // after generation, navigate to the static website view
      navigate(`/campaigns/${jobId}/website`)
    } catch (e) {
      console.error(e)
    } finally {
      setGenerating(false)
    }
  }

  if (!campaign) return <div className="flex justify-center items-center h-screen">Loading…</div>

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8 bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-100">
      {/* Header */}
      <header className="flex flex-col md:flex-row items-center md:items-start gap-6">
        {campaign.image_path && (
          <img
            src={imageUrl(campaign.image_path)}
            alt={campaign.title}
            className="w-full md:w-64 h-auto rounded-lg shadow-md"
          />
        )}
        <div className="flex-1">
          <h1 className="text-3xl md:text-4xl font-bold mb-4">{campaign.title}</h1>
          <p className="text-lg mb-4">{campaign.summary}</p>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className={
              `mt-2 inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm 
               bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 
               text-white transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed`
            }
          >
            {generating ? 'Generating…' : 'Generate Website'}
          </button>
        </div>
      </header>

      {/* Campaign copy – rendered as markdown */}
      <section className="prose prose-lg dark:prose-invert max-w-none">
        <ReactMarkdown
          children={campaign.copy_draft}
          components={{
            p: ({node, ...props}) => <p className="mb-4" {...props} />,
            h1: ({node, ...props}) => <h1 className="text-2xl font-semibold mt-8 mb-4" {...props} />, 
            h2: ({node, ...props}) => <h2 className="text-xl font-semibold mt-6 mb-3" {...props} />, 
          }}
        />
      </section>
    </div>
  )
}
