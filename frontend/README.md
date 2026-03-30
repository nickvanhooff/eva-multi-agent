# Eva Frontend

React+Vite dashboard for the Eva multi-agent marketing campaign system.

## Setup

```bash
npm install
npm run dev       # http://localhost:5173
```

Requires the Eva API running at `http://localhost:8000` (see root README for API setup). The Vite dev server proxies `/api` → `http://localhost:8000` automatically.

## Pages

| Route | Description |
|-------|-------------|
| `/` | Dashboard — stats, pipeline overview, recent campaigns |
| `/campaigns/new` | New Campaign — type toggle, description, PDF upload/select |
| `/campaigns/:id/live` | Live view — real-time pipeline + expandable agent log |
| `/campaigns/:id` | Results — Strategy / Copy / Social / Image / Logs tabs |
| `/history` | Campaign History — filter by type and status |

## Structure

```
src/
├── api.js                  Fetch wrapper + streamCampaignEvents() (EventSource) + imageUrl()
├── App.jsx                 React Router setup
├── index.css               CSS variables (dark theme, indigo primary)
├── components/
│   ├── Sidebar.jsx         Navigation sidebar
│   └── AgentPipeline.jsx   7-node pipeline visualization (idle/active/done)
└── pages/
    ├── Dashboard.jsx
    ├── NewCampaign.jsx
    ├── CampaignLive.jsx    SSE stream — live events with expandable prompts/responses
    ├── CampaignResults.jsx Tabs including Logs for reviewing agent thought process
    └── CampaignHistory.jsx
```

## Real-time agent tracking

`CampaignLive` connects to `GET /api/campaigns/:id/stream` via `EventSource`. Each event is one of:

- `→ llm_call` — prompt sent to the model (click to expand: system prompt + user prompt)
- `← llm_response` — response received (click to expand: full response preview)
- `✓ node_done` — agent node completed

After completion, the Logs tab in `CampaignResults` shows the full event history loaded from the saved `_events.json` file.

## Design system

Based on Google Stitch-generated designs (project `9283653711690935700`):
- Dark mode, `#6366f1` indigo primary
- Inter font, rounded-lg corners
- No external UI library — pure CSS variables
