# Stappenlog — Eva Multi-Agent System

Dit document beschrijft alle stappen die zijn genomen bij het opzetten van het multi-agent systeem.

---

## Stap 1: Project skeleton initialisatie
**Datum:** 2026-03-25
**Commit:** [`1f59280`](https://github.com/nickvanhooff/eva-multi-agent/commit/1f59280)

**Wat is er gedaan:**
- Nieuw project aangemaakt in `C:\fontys\semester_4\eva-multi-agent\`
- Git repository geinitialiseerd
- Mappenstructuur opgezet: `src/`, `src/agents/`, `docs/`, `tests/`
- Basisbestanden aangemaakt: `.gitignore`, `requirements.txt`, `.env.example`, `README.md`
- `STAPPEN.md` (dit bestand) aangemaakt voor het bijhouden van voortgang

**Waarom een nieuw project?**
Het bestaande `reclamebureau_eva` was een prototype/testfase met LangGraph + LangChain. Dit nieuwe project start bewust met **pure LangGraph** (zonder LangChain), gebaseerd op de aanpak uit de freeCodeCamp tutorial (bron: https://www.youtube.com/watch?v=jGg_1h0qzaM) — eerst LangGraph begrijpen, daarna LangChain toevoegen.

**Dependencies (zelf gekozen):**
- `langgraph>=0.2.28` — graph orchestratie framework
- `openai>=1.30.0` — LLM calls via OpenAI-compatibele API (werkt met Ollama, OpenRouter, Groq)
- `python-dotenv>=1.0.1` — omgevingsvariabelen laden

**Bronnen:**
- freeCodeCamp LangGraph tutorial: https://www.youtube.com/watch?v=jGg_1h0qzaM
- OpenAI SDK documentatie: https://github.com/openai/openai-python
- LangGraph documentatie: https://langchain-ai.github.io/langgraph/

**Zelf bedacht:**
- De keuze om de openai SDK te gebruiken als provider-agnostische LLM wrapper (i.p.v. langchain) is zelf bedacht, gebaseerd op het feit dat Ollama, OpenRouter en Groq allemaal OpenAI-compatibele endpoints bieden.

---

## Stap 2: Architectuur diagrammen
**Datum:** 2026-03-25
**Commit:** [`2467667`](https://github.com/nickvanhooff/eva-multi-agent/commit/2467667)

**Wat is er gedaan:**
- `docs/architecture.md` aangemaakt met 3 Mermaid diagrammen:
  1. **Graph Flow** — toont alle 5 agent nodes, edges, en conditionele feedback loops
  2. **State Schema** — toont de CampaignState TypedDict met alle velden en welke agent wat leest/schrijft
  3. **LangGraph Concepts Map** — overzicht van welke LangGraph primitives worden gebruikt
- Uitleg toegevoegd over conditional routing logica (cm_router)
- Tabel met wat elke agent leest uit de state

**Ontwerpkeuzes (zelf bedacht):**
- De Campaign Manager als centraal beslispunt met `phase` veld om feedback naar de juiste agent te routeren
- Twee feedback loops: copy loop en social loop (i.p.v. alles tegelijk terugsturen)
- `copy_versions` en `social_versions` met `operator.add` reducer om iteratiegeschiedenis te bewaren (patroon overgenomen uit prototype)
- Maximum 3 iteraties om oneindige loops te voorkomen

**Bronnen:**
- LangGraph StateGraph documentatie: https://langchain-ai.github.io/langgraph/concepts/low_level/#stategraph
- LangGraph conditional edges: https://langchain-ai.github.io/langgraph/concepts/low_level/#conditional-edges
- Agent rollen gebaseerd op DL2 onderzoek (marketingskills plugin analyse)

---

## Stap 3: CampaignState TypedDict
**Datum:** 2026-03-25
**Commit:** [`5ed9fdb`](https://github.com/nickvanhooff/eva-multi-agent/commit/5ed9fdb)

**Wat is er gedaan:**
- `src/state.py` aangemaakt met de `CampaignState` TypedDict
- Alle state velden gedefinieerd voor de 5 agents
- `operator.add` reducer toegevoegd op `copy_versions` en `social_versions` om iteratiegeschiedenis te bewaren

**Waarom TypedDict?**
LangGraph gebruikt TypedDict als state schema voor de StateGraph. Dit geeft type safety en maakt duidelijk welke velden beschikbaar zijn. Het is het standaard patroon uit de LangGraph documentatie.

**Waarom Annotated met operator.add?**
Standaard overschrijft LangGraph velden (last-write-wins). Met `Annotated[list[str], operator.add]` worden nieuwe items aan de lijst toegevoegd i.p.v. overschreven. Zo blijft de volledige versiegeschiedenis bewaard — handig voor debugging en evaluatie.

**Bronnen:**
- LangGraph state reducers: https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers
- Python TypedDict: https://docs.python.org/3/library/typing.html#typing.TypedDict

---

## Stap 4: LLM wrapper met openai SDK
**Datum:** 2026-03-25
**Commit:** [`1874adc`](https://github.com/nickvanhooff/eva-multi-agent/commit/1874adc)

**Wat is er gedaan:**
- `src/llm.py` aangemaakt met een `call_llm()` functie
- Provider-agnostisch: werkt met Ollama, OpenRouter en Groq via `base_url` switching
- Configuratie via `.env` bestand (LLM_PROVIDER, LLM_MODEL, LLM_BASE_URL, LLM_API_KEY)
- Standaard provider defaults per provider opgenomen

**Waarom openai SDK i.p.v. LangChain?**
Het doel is om eerst puur met LangGraph te werken zonder LangChain. De openai Python SDK werkt met alle drie de providers omdat ze allemaal OpenAI-compatibele endpoints bieden. Dit vervangt de `langchain_core.messages` en `BaseChatModel` uit het prototype.

**Zelf bedacht:**
- Het `PROVIDER_DEFAULTS` dictionary patroon met fallback naar .env variabelen
- De `_get_client()` helper die een tuple (client, model) teruggeeft

**Bronnen:**
- OpenAI Python SDK: https://github.com/openai/openai-python
- Ollama OpenAI compatibility: https://ollama.com/blog/openai-compatibility
- Groq OpenAI compatibility: https://console.groq.com/docs/openai

---

## Stap 5: Researcher agent node
**Datum:** 2026-03-25
**Commit:** [`4d5ef26`](https://github.com/nickvanhooff/eva-multi-agent/commit/4d5ef26)

**Wat is er gedaan:**
- `src/agents/researcher.py` aangemaakt
- Node functie `researcher_node(state) -> dict` die `product_description` leest en `market_research` + `target_audience` teruggeeft
- Nederlandse system prompt voor consistente taaloutput
- Section parsing met fallback als LLM het formaat niet volgt

**Zelf bedacht:**
- Section parsing logica met `## MARKTONDERZOEK` / `## DOELGROEP` markers
- Fallback: als parsing faalt, wordt de volledige response gebruikt voor beide velden

---

## Stap 6: Strateeg agent node
**Datum:** 2026-03-25
**Commit:** [`7eabaa8`](https://github.com/nickvanhooff/eva-multi-agent/commit/7eabaa8)

**Wat is er gedaan:**
- `src/agents/strategist.py` aangemaakt
- Node functie `strateeg_node(state) -> dict` die research + doelgroep leest en strategie, positionering, en tone of voice teruggeeft
- Robuustere section parsing met line-by-line approach (case-insensitive)

**Waarom Nederlandse system prompts?**
Uit het prototype (DL-002 bugfix) bleek dat kleine LLMs (llama3.2) Engels en Nederlands door elkaar halen als de prompt in het Engels is. Nederlandse system prompts voorkomen dit probleem.

**Bronnen:**
- DL-002 bugfix uit reclamebureau_eva prototype (les geleerd)
- LangGraph node pattern: https://langchain-ai.github.io/langgraph/concepts/low_level/#nodes

---

## Stap 7: Minimale graph met researcher en strateeg
**Datum:** 2026-03-25
**Commit:** [`959fd33`](https://github.com/nickvanhooff/eva-multi-agent/commit/959fd33)

**Wat is er gedaan:**
- `src/graph.py` aangemaakt met een minimale 2-node StateGraph
- Flow: START -> Researcher -> Strateeg -> END
- MemorySaver checkpointer toegevoegd voor state persistence
- `build_graph()` functie die de gecompileerde graph teruggeeft

**Waarom eerst een minimale graph?**
Door klein te beginnen (2 nodes) kunnen we verifiereren dat de LangGraph setup correct werkt voordat we de complexere agents en conditional routing toevoegen. Dit volgt de incrementele aanpak uit de freeCodeCamp tutorial.

**Bronnen:**
- LangGraph StateGraph: https://langchain-ai.github.io/langgraph/concepts/low_level/#stategraph
- LangGraph MemorySaver: https://langchain-ai.github.io/langgraph/concepts/persistence/

---

## Stap 8: Copywriter agent node
**Datum:** 2026-03-25
**Commit:** [`e8458b1`](https://github.com/nickvanhooff/eva-multi-agent/commit/e8458b1)

**Wat is er gedaan:**
- `src/agents/copywriter.py` aangemaakt
- Schrijft headline, subheadline, bodytekst en call-to-action
- Verwerkt feedback van Campaign Manager bij revisies
- Gebruikt `copy_versions: [response]` zodat de reducer elke iteratie toevoegt
- Hoogste temperature (0.9) voor maximale creativiteit

**Zelf bedacht:**
- De feedback_section wordt alleen getoond als er daadwerkelijk feedback is EN iteratie > 0

---

## Stap 9: Social Specialist agent node
**Datum:** 2026-03-25
**Commit:** [`48569de`](https://github.com/nickvanhooff/eva-multi-agent/commit/48569de)

**Wat is er gedaan:**
- `src/agents/social_specialist.py` aangemaakt
- Maakt content voor Instagram (caption + hashtags), LinkedIn, en X/Twitter
- Gebruikt `copy_draft` als basis voor social content
- Verwerkt feedback alleen als `phase == "social_review"`

---

## Stap 10: Campaign Manager met conditionele routing
**Datum:** 2026-03-25
**Commit:** [`3428ab7`](https://github.com/nickvanhooff/eva-multi-agent/commit/3428ab7)

**Wat is er gedaan:**
- `src/agents/campaign_manager.py` aangemaakt
- Beoordeelt de campagne op strategie-aansluiting, consistentie, creativiteit en volledigheid
- Parsed BESLISSING, FASE en FEEDBACK uit LLM response met regex
- `cm_router()` functie voor conditionele routing in de graph
- Bij goedkeuring of max iteraties: `final_campaign` dict wordt aangemaakt met alle resultaten

**Waarom regex parsing?**
Uit het prototype (DL-002) bleek dat eenvoudige string matching niet betrouwbaar is bij kleine LLMs. Regex op specifieke patronen (bijv. `BESLISSING: GOEDGEKEURD`) is robuuster.

**Bronnen:**
- LangGraph conditional edges: https://langchain-ai.github.io/langgraph/concepts/low_level/#conditional-edges
- Regex parsing patroon overgenomen uit prototype `reclamebureau_eva/src/agents/reviewer.py`

---

## Stap 11: Volledige graph met feedback loops
**Datum:** 2026-03-25
**Commit:** [`4d44aed`](https://github.com/nickvanhooff/eva-multi-agent/commit/4d44aed)

**Wat is er gedaan:**
- `src/graph.py` uitgebreid van 2-node naar volledige 5-node graph
- Alle 5 agents geregistreerd als nodes
- Lineaire edges: START -> Researcher -> Strateeg -> Copywriter -> Social Specialist -> Campaign Manager
- Conditionele edges vanuit Campaign Manager:
  - `"copywriter"` — feedback loop voor copy revisie
  - `"social_specialist"` — feedback loop voor social revisie
  - `"finalize"` -> END — goedkeuring of max iteraties bereikt

**Bronnen:**
- LangGraph add_conditional_edges: https://langchain-ai.github.io/langgraph/concepts/low_level/#conditional-edges

---

## Stap 12: Main entry point en Docker setup
**Datum:** 2026-03-25
**Commit:** [`2a8ae7f`](https://github.com/nickvanhooff/eva-multi-agent/commit/2a8ae7f)

**Wat is er gedaan:**
- `src/main.py` aangemaakt als entry point
- `run_campaign()` functie die de graph bouwt, een uniek thread_id genereert, en de pipeline runt
- Demo product (Eco-Cup Go) als test input — hetzelfde product als in DL1 benchmarking
- UTF-8 fix voor Windows console output
- `Dockerfile` aangemaakt (Python 3.11-slim, pip install, run main)
- `docker-compose.yml` met twee services:
  - `ollama` — lokale LLM server met volume voor model data
  - `eva` — het multi-agent systeem, verbonden met ollama via Docker netwerk

**Waarom Docker?**
Docker maakt het project reproduceerbaar en makkelijk te deployen. De docker-compose setup zorgt ervoor dat Ollama en Eva in dezelfde Docker network draaien, zodat Eva via `http://ollama:11434/v1` de LLM kan aanroepen.

**Zelf bedacht:**
- De `run_campaign()` wrapper die een uniek `thread_id` genereert per run (nodig voor de MemorySaver checkpointer)
- Docker networking: Eva verwijst naar `ollama` hostname i.p.v. `localhost`

**Bronnen:**
- Docker Compose services: https://docs.docker.com/compose/
- Ollama Docker image: https://hub.docker.com/r/ollama/ollama

---

## Stap 13: Logging enhancement — zichtbaarheid van agent activiteit
**Datum:** 2026-03-25
**Commit:** [`a0ae122`](https://github.com/nickvanhooff/eva-multi-agent/commit/a0ae122)

**Wat is er gedaan:**
- Alle 5 agent nodes (`researcher`, `strategist`, `copywriter`, `social_specialist`, `campaign_manager`) voorzien van print statements
- Elke agent print:
  - Startsignaal met duidelijke headers (`===` scheidingslijn)
  - Response snippet (eerste 500 tekens) zodat voortgang zichtbaar is
  - Campaign Manager print ook: BESLISSING (GOEDGEKEURD/AFGEWEZEN), FASE, FEEDBACK preview
- `Dockerfile` aangepast: `ENV PYTHONUNBUFFERED=1` toegevoegd zodat logs direct in Docker container zichtbaar zijn (niet gebufferd)

**Waarom nodig?**
Vorige test met lokale Ollama (qwen3.5:4b) duurde 20+ minuten met zero zichtbare voortgang. Gebruikers kunnen niet zien wat er gebeurt. Met logging kunnen ze monitor wanneer welke agent actief is.

**Zelf bedacht:**
- De `PYTHONUNBUFFERED=1` env var in Dockerfile voor real-time Docker logging
- Logging format met duidelijke headers (`[RESEARCHER]`, `[CAMPAIGN MANAGER]`, etc.) voor scannability

---

## Stap 14: Cloud LLM provider integratie — Groq
**Datum:** 2026-03-25
**Commit:** [`cad09de`](https://github.com/nickvanhooff/eva-multi-agent/commit/cad09de) (GPU support), [`9439006`](https://github.com/nickvanhooff/eva-multi-agent/commit/9439006) (report saving)

**Wat is er gedaan:**
- `.env` aangepast: `LLM_PROVIDER=groq`, model `llama-3.3-70b-versatile`, API key ingevuld
- `docker-compose.yml` geoptimaliseerd:
  - GPU support enabled: `driver: nvidia`, `count: all`, `capabilities: [gpu]`
  - Hardcoded environment overrides verwijderd (lijn 24-28 geco}mmentarieerd) zodat `.env` bestand wordt gebruikt
- Lokale Ollama service blijft in docker-compose (voor toekomstig gebruik), maar is nu optioneel

**Waarom Groq cloud i.p.v. lokale Ollama?**
Lokale Ollama met qwen3.5:4b (4B parameters) was traag: 20+ minuten per pipeline. Groq biedt:
- Snellere inference (llama-3.3-70b-versatile): ~2 minuten totaal
- Veel groter model (70B parameters) → betere kwaliteit
- Gratis API tier (8000 requests/dag, ruim voldoende voor testen)

**Kosten analyse:**
- Ollama (lokaal): Gratis, maar langzaam + GPU nodig
- Groq: Gratis tier, snel, geen GPU nodig
- OpenRouter/andere clouds: Betaald

**Performance verschil:**
- qwen3.5:4b (Ollama, RTX 4050): 4-5 minuten per agent = 20+ minuten totaal
- llama-3.3-70b (Groq API): ~3-4 seconden per agent = ~20 seconden totaal
→ **60x sneller** (van 20+ minuten naar 20 seconden)

**Zelf bedacht:**
- De keuze om docker-compose beiden services te behouden maar via `.env` flexibel switchen (i.p.v. permanent te verwijderen)
- GPU support in docker-compose als future-proofing

**Bronnen:**
- Groq console: https://console.groq.com
- Groq OpenAI compatibility: https://console.groq.com/docs/openai
- Docker GPU support: https://docs.docker.com/compose/gpu-support/

---

## Stap 15: Campaign report persistentie — JSON reports
**Datum:** 2026-03-25
**Commit:** [`9439006`](https://github.com/nickvanhooff/eva-multi-agent/commit/9439006), volume mount gefixt in `docker-compose.yml`, later [`835ff09`](https://github.com/nickvanhooff/eva-multi-agent/commit/835ff09)

**Wat is er gedaan:**
- `src/main.py` uitgebreid met `save_campaign_report()` functie
- Elke campaign wordt opgeslagen als JSON file in `campaigns/` directory
- Bestandsnaam bevat timestamp: `campaign_YYYYMMDD_HHMMSS.json`
- Report bevat: product, doelgroep, strategie, positioning, tone of voice, copy, social content, versie-aantallen, iteratie-count, goedkeuring-status
- `.gitignore` aangepast: `campaigns/` directory genegeerd (niet in git)
- `docker-compose.yml` aangepast: volume mount `./campaigns:/app/campaigns` zodat reports persistent zijn op host machine
- `main.py` print het pad naar het rapport na completion: `📄 Campaign report saved to: campaigns/campaign_20260325_142530.json`

**Waarom nodig?**
Vorige aanvraag: "Waar kan ik het final report lezen?" → Campaign output stond alleen in console logs, niet persistent opgeslagen. Nu kan je alle gegenereerde campagnes teruslezen en vergelijken.

**Waarom volume mount?**
Docker containers hebben hun eigen geïsoleerd filesystem. Zonder volume mount, de `campaigns/` directory (en alle reports erin) verdwijnt wanneer de container stopt. Met `volumes: ./campaigns:/app/campaigns` worden reports direct naar de host machine geschreven.

**Access:**
- Host machine: `campaigns/campaign_*.json`
- Docker: `/app/campaigns/campaign_*.json`

**Use case:**
- Evaluatie: vergelijken van verschillende campagnes
- Portfolio: bewijs van werking voor learning outcomes
- Debugging: nagaan wat een agent heeft gegenereerd

**Zelf bedacht:**
- JSON format i.p.v. markdown/TXT voor machine-readability
- Timestamp in bestandsnaam zodat elke run uniek is
- Kompakte report (geen volledige versiegeschiedenis, wel counts) om file size klein te houden
- Volume mount pattern voor persistent Docker output

---

## Stap 16: LangSmith integratie — debugging en monitoring
**Datum:** 2026-03-25
**Commit:** [`31dcbe7`](https://github.com/nickvanhooff/eva-multi-agent/commit/31dcbe7)

**Wat is er gedaan:**
- `src/tracing.py` aangemaakt met `setup_tracing()` functie
- `langsmith>=0.1.0` toegevoegd aan requirements.txt
- `.env.example` aangemaakt met LangSmith configuratietemplate
- `src/main.py` uitgebreid: `setup_tracing()` aangeroepen bij startup
- `LANGSMITH_SETUP.md` aangemaakt: volledige Dutch gids voor setup en gebruik

**LangSmith features:**
- Real-time tracing: zie elke agent-stap, LLM call, en state transition
- Performance monitoring: latency per agent, token usage, kosten
- Debugging interface: inspecteer state velden en LLM responses
- Run comparison: vergelijk iteraties en feedback-loops

**Configuratie:**
```env
LANGSMITH_ENABLED=true          # Aan/uit
LANGSMITH_API_KEY=ls_...        # API key van smith.langchain.com
LANGSMITH_PROJECT=eva-multi-agent
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

**Setup stappen:**
1. Account aanmaken: https://smith.langchain.com
2. API Key ophalen uit Settings
3. In `.env` instellen: `LANGSMITH_ENABLED=true` + API key
4. Campaign runnen: tracing automatisch actief
5. Dashboard bezoeken: zie real-time traces en metrics

**Waarom LangSmith?**
Debugging multi-agent systemen is complex: je wilt zien:
- Wat zei Researcher precies? Waarom gaf Campaign Manager feedback?
- Hoe lang duurt elke agent? Waar is de bottleneck?
- Hoeveel tokens gebruiken we? (kostenbewustzijn)
- Werkt de feedback-loop echt?

LangSmith geeft antwoorden op al deze vragen zonder extra code te schrijven.

**Portfolio waarde:**
- Screenshots van traces kunnen als bewijs in decision logs gelinkt
- Verdeelt eigen werk (keuzes, config) en AI-werk (LLM responses, agent logica)
- Toont iteratieproces: feedback loop in actie

**Zelf bedacht:**
- Environment-variable based configuration (LANGSMITH_ENABLED) zodat je kan switchen zonder code
- Automatic initialization in main.py (setup_tracing() called at startup)
- Nederlandse documentatie LANGSMITH_SETUP.md met stap-voor-stap + troubleshooting

**Bronnen:**
- LangSmith officieel: https://smith.langchain.com
- LangSmith docs: https://docs.smith.langchain.com/
- LangGraph + LangSmith integratie: https://langchain-ai.github.io/langgraph/how-tos/debugging/

---

## Stap 17: LangSmith debuggen — traces werkend krijgen
**Datum:** 2026-03-25
**Commit:** [`6b83624`](https://github.com/nickvanhooff/eva-multi-agent/commit/6b83624)

**Wat is er gedaan:**
- Bug gevonden en opgelost: traces verschenen niet in LangSmith dashboard ondanks correcte API key
- Drie oorzaken gevonden en gefixed:

**Bug 1 — Verkeerde environment variabele naam:**
`.env` had `LANGSMITH_TRACING=true`, maar `src/tracing.py` checkte op `LANGSMITH_ENABLED=true`.
→ `.env` aangepast: `LANGSMITH_TRACING=true` → `LANGSMITH_ENABLED=true`

**Bug 2 — LangSmith SDK werd nooit geactiveerd:**
`setup_tracing()` zette wel `LANGSMITH_API_KEY` maar nooit `LANGSMITH_TRACING=true` — de variabele die de LangSmith SDK zelf checkt om tracing in te schakelen.
→ `src/tracing.py` aangepast: `os.environ["LANGSMITH_TRACING"] = "true"` toegevoegd in `setup_tracing()`

**Bug 3 — Raw OpenAI SDK wordt niet getraceerd door LangSmith:**
`src/llm.py` gebruikte de raw `openai.OpenAI` client. LangSmith trapt alleen automatisch LangChain calls af, niet de raw OpenAI SDK.
→ `src/llm.py` omgebouwd: van `openai.OpenAI` naar `langchain_openai.ChatOpenAI`
→ `requirements.txt` uitgebreid: `langchain>=0.1.0` en `langchain_openai>=0.1.0` toegevoegd

**Resultaat:**
Na rebuild (`docker compose build && docker compose up`) verschijnen traces in LangSmith:
- Volledige graph run zichtbaar (11.77s, ~8.500 tokens)
- Alle 5 agent stappen traceerbaar
- Token gebruik en latency per agent inzichtelijk

**Waarom is dit belangrijk voor portfolio?**
- LangSmith traces zijn nu bruikbaar als bewijs in decision logs (screenshot + link)
- Token usage zichtbaar: ~8.500 tokens per campaign run = gratis binnen Groq free tier
- Feedback loop werking aantoonbaar via trace tree

**Zelf bedacht:**
- Diagnose van alle drie de oorzaken systematisch doorlopen (env var naam → SDK activatie → SDK compatibiliteit)
- Keuze om llm.py te migreren naar LangChain i.p.v. raw SDK (meer integratiemogelijkheden voor tracing)

**Bronnen:**
- LangSmith quickstart: https://docs.smith.langchain.com/
- LangChain ChatOpenAI: https://python.langchain.com/docs/integrations/chat/openai/

---

## Stap 18: SDXL image generatie — lokaal via Docker met CUDA
**Datum:** 2026-03-25
**Commit:** [`b855e75`](https://github.com/nickvanhooff/eva-multi-agent/commit/b855e75)

**Aanleiding — eigen prompts in deze sessie:**
> "which agent has web search"
> "can groq generate images?"
> "is RTX 4050 capable of running a HuggingFace model and how long?"
> "SDXL can also work, add torch + packages for Docker"

Doordat ik vroeg welke agent web search heeft, ontdekte ik dat dit niet geïmplementeerd was. Daarna vroeg ik of Groq images kon genereren (antwoord: nee). Op basis van mijn vraag over de RTX 4050 is besloten om lokaal te draaien i.p.v. de HuggingFace cloud API. Tot slot heb ik zelf de richting gegeven: SDXL lokaal via Docker met GPU support.

**Wat is er gedaan:**
- `Dockerfile` base image gewijzigd: `python:3.11-slim` → `pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime`
- `requirements.txt` uitgebreid: `diffusers>=0.24.0`, `transformers>=4.36.0`, `accelerate>=0.25.0`, `safetensors>=0.4.0`
- `docker-compose.yml` aangepast: GPU support toegevoegd aan `eva` service (was alleen bij `ollama`)
- `sdxl_cache` Docker volume toegevoegd: HuggingFace model cache persistent opgeslagen (voorkomt re-download bij elke rebuild)

**Beslissing: lokaal draaien i.p.v. HuggingFace Inference API**

Overwogen opties:
1. HuggingFace Inference API (cloud) — gratis tier, geen GPU nodig, maar rate limits en afhankelijk van internet
2. Lokaal met `diffusers` op RTX 4050 — volledig gratis, consistent, geen externe afhankelijkheid

Gekozen voor **lokaal** omdat:
- RTX 4050 (6GB VRAM) past SDXL met fp16 optimalisaties (~30–60s per image)
- Geen API key of rate limits
- Sneller dan HF gratis tier (geen wachtrij)
- GPU support was al geconfigureerd in docker-compose voor `ollama` service

**Overwegingen hardwarelimiet:**
- 6GB VRAM is krap voor SDXL (normaal 8GB+)
- Oplossing: `torch.float16` + `enable_attention_slicing()` + `enable_vae_slicing()`
- Alternatief als OOM: SDXL-turbo (4-stap model, sneller, iets minder kwaliteit)

**Waarom pytorch base image?**
`pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime` bevat al PyTorch + CUDA + cuDNN. Dit voorkomt handmatige CUDA installatie in de Dockerfile en geeft een stabiele, geteste combinatie.

**Zelf bedacht:**
- `sdxl_cache` volume voor model persistentie (SDXL is ~6GB download — niet elke keer opnieuw downloaden)
- GPU support op `eva` container naast `ollama` container

**Bronnen:**
- HuggingFace diffusers SDXL: https://huggingface.co/docs/diffusers/using-diffusers/sdxl
- PyTorch Docker images: https://hub.docker.com/r/pytorch/pytorch
- Docker GPU support: https://docs.docker.com/compose/gpu-support/

---

## Stap 19: Bugfix — PyTorch versie te oud voor transformers
**Datum:** 2026-03-25

**Aanleiding — eigen prompt in deze sessie:**
> "can i set the inference steps to 1 for testing?"
> [na het zien van de Docker error] "add this error to STAPPEN.md"

Ik vroeg om inference steps op 1 te zetten om snel te testen of de pipeline werkte zonder lang te wachten. Daarna zag ik de foutmelding in de Docker output en gaf ik de instructie om dit te documenteren en op te lossen.

**Fout:**
```
Disabling PyTorch because PyTorch >= 2.4 is required but found 2.1.0
PyTorch was not found. Models won't be available...
[IMAGE GENERATOR] ERROR: module 'torch' has no attribute 'xpu'
```

**Oorzaak:**
`Dockerfile` gebruikte `pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime` (PyTorch 2.1.0). De `transformers` library vereist PyTorch >= 2.4. Door de versie mismatch kon `torch` niet worden geïnitialiseerd en ontbrak het `xpu` attribuut.

**Fix:**
`Dockerfile` base image bijgewerkt:
```dockerfile
# Was:
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime
# Nu:
FROM pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime
```

**Zelf bedacht:**
- Foutmelding herkend als versie mismatch (niet een code bug)
- Gekozen voor minimale versie die voldoet (2.4.0) i.p.v. de nieuwste (2.5+) voor stabiliteit

---

## Stap 20: Bugfix — diffusers/transformers versie incompatibiliteit met PyTorch 2.4
**Datum:** 2026-03-25

**Aanleiding — eigen prompts in deze sessie:**
> "weet je dit zeker?" [over het vastpinnen van versies]
> "the 4-step result was just noise/texture, not a real image"
> [na het zien van SDXL-Turbo output] "this looks good now"

Ik twijfelde aan de aanpak van versie pinning en stelde een kritische vraag. Daarnaast observeerde ik dat 4 stappen met standaard SDXL alleen noise gaf — zelf gezien en gerapporteerd — wat leidde tot de overstap naar SDXL-Turbo.

**Fout:**
```
Failed to import diffusers.models.autoencoders.autoencoder_kl
infer_schema(func): Parameter q has unsupported type torch.Tensor
```

**Oorzaak:**
`pip install` haalde de nieuwste versies op: `diffusers 0.37.1` + `transformers 5.3.0`. Deze versies gebruiken attention mechanismen die `torch.compile`/`infer_schema` vereisen met features die niet beschikbaar zijn in PyTorch 2.4.0. De `>=` versieconstraints in `requirements.txt` lieten pip vrij om te recente versies te installeren.

**Fix:**
Versies vastgepind op bewezen stabiele combinatie met PyTorch 2.4:
```
# Was:
diffusers>=0.24.0
transformers>=4.36.0

# Nu:
diffusers==0.30.0
transformers==4.44.0
```

**Zelf bedacht:**
- Root cause herkend: `>=` constraints zijn gevaarlijk bij snel evoluerende ML libraries
- Stabiele combinatie bepaald: diffusers 0.30.0 + transformers 4.44.0 zijn getest met PyTorch 2.4

---

## Stap 21: Groq rate limit bereikt — multi-LLM oplossing
**Datum:** 2026-03-25
**Commit:** [`f7a61a9`](https://github.com/nickvanhooff/eva-multi-agent/commit/f7a61a9)

**Aanleiding — eigen prompts in deze sessie:**
> "groq has now limit at me, can i use multiple LLMs per agent?"
> "voer het niet uit maar stel op in 1 md" [over de model-verdeling]
> "gebruik nu OPENROUTER_API_KEY als env waarde"
> "look which models are there for use"
> "pak een middel maat model"

Ik zag de 429 rate limit fout en stelde zelf voor om meerdere LLMs per agent te gebruiken. Ik gaf bewust de instructie om eerst te documenteren (in één MD-bestand) voordat er code geschreven werd. Daarna heb ik zelf de OpenRouter API key aangewezen en de modelkeuze gestuurd door te vragen om een "middel maat model" uit de beschikbare gratis modellen.

**Fout:**
```
openai.RateLimitError: Error code: 429
Rate limit reached for model `llama-3.3-70b-versatile`
Limit 100000, Used 100000, Requested 1533.
Please try again in 22m4.512s.
```

**Oorzaak:**
Groq gratis tier heeft een limiet van **100.000 tokens per dag**. Na meerdere test-runs (debugging van LangSmith, SDXL, en campaign runs) was de dagelijkse limiet bereikt.

**Oplossing: multi-LLM per agent**
- `src/llm.py` uitgebreid: `call_llm()` accepteert nu een optionele `provider` parameter
- `OPENROUTER_API_KEY` toegevoegd als tweede provider in `.env`
- `docs/multi_llm_config.md` aangemaakt met configuratie-overzicht

**Aanbevolen verdeling:** zie @[docs/model_selection.md](docs/model_selection.md)

**Besparing:** ~60% minder Groq 70B tokens (copywriter + social draaien op OpenRouter)

**Zelf bedacht:**
- Keuze om per agent een provider te configureren i.p.v. één globale provider
- Groq 70B bewaren voor Campaign Manager (kritiekste agent)
- Groq 8B voor Researcher + Strateeg (500k tokens/dag limiet)
- OpenRouter voor creatieve agents (copywriter, social)

**Bronnen:**
- Volledige model motivatie per agent: @[docs/model_selection.md](docs/model_selection.md)
- OpenRouter free models: https://openrouter.ai/models?q=free
- Groq rate limits: https://console.groq.com/settings/limits

---

## Stap 26: Tools geïmplementeerd — DuckDuckGo + Wikipedia in Researcher
**Datum:** 2026-03-29
**Commit:** [`16864a6`](https://github.com/nickvanhooff/eva-multi-agent/commit/16864a6)

**Aanleiding — eigen prompt:**
> "ja" (na stap 25 oriëntatie: wil je dat ik DuckDuckGo en Wikipedia implementeer?)

**Wat is er gedaan:**
- `src/tools.py` aangemaakt met twee functies:
  - `duckduckgo_search(query, max_results=5)` — zoekt via ddgs package
  - `wikipedia_summary(query, sentences=4)` — haalt Wikipedia-samenvatting op (NL, fallback EN)
- Researcher aangepast: roept tools aan vóór de LLM-call, injecteert resultaten in de user_prompt
- `requirements.txt` bijgewerkt: `ddgs` en `wikipedia` toegevoegd
- Note: package heette eerst `duckduckgo-search`, hernoemd naar `ddgs` — aangepast

**Hoe het werkt:**
```
Researcher node:
  1. duckduckgo_search("{product} markt concurrenten doelgroep")
  2. wikipedia_summary("{product}")
  3. resultaten → user_prompt als extra context
  4. LLM analyseert op basis van echte data
```

Graph-structuur ongewijzigd. Tools zijn synchrone pre-processing, geen LangGraph tool-calling.

**Zelf bedacht:**
- tools als pre-processing vóór llm-call, niet als langgraph tool nodes
- wikipedia eerst nl, daarna en als fallback
- ddgs package naam fix zelf ontdekt tijdens testen

**Bronnen:**
- ddgs: https://github.com/deedy5/ddgs
- wikipedia package: https://pypi.org/project/wikipedia/

---

## Stap 25: Tool oriëntatie — welke tools passen bij welke agent?
**Datum:** 2026-03-28

**Aanleiding — eigen prompt:**
> "look which tools can be used in the first version, it can be small. also document this in stappen that the skills are added and that i am now searching for easy tools to use. look for which agent can use which tool"

**Wat is er gedaan:**
LangChain tool integrations pagina doorgelopen (https://docs.langchain.com/oss/python/integrations/tools/index). Gefilterd op: gratis, geen API key, zinvol voor een marketingpipeline.

**Versie 1 — geen API key:**

| Tool | Package | Agent | Waarvoor |
|---|---|---|---|
| DuckDuckGo Search | `ddgs` | Researcher | actuele markt- en concurrentieinfo |
| Wikipedia | `wikipedia` | Researcher | achtergrondkennis product/markt |
| Google Trends | `pytrends` | Researcher + Strateeg | trending zoektermen |

**Optioneel (gratis API key):**

| Tool | Gratis tier | Agent | Waarvoor |
|---|---|---|---|
| Tavily Search | 1.000 req/maand | Researcher | rijkere zoekresultaten |
| Reddit Search | ja | Strateeg | wat zegt de doelgroep |

Copywriter, Social Specialist en Campaign Manager krijgen geen tools — die werken op output van vorige agents.

**Verwacht effect op tokens:** tool output vergroot de Researcher user_prompt. Te meten in LangSmith als V5.

**Zelf bedacht:**
- alleen Researcher en Strateeg krijgen tools, de rest niet
- eerst zonder API key beginnen om het simpel te houden

---

## Stap 24: Skills map — domeinkennis per agent via systeemprompt
**Datum:** 2026-03-28
**Commit:** [`ca8d757`](https://github.com/nickvanhooff/eva-multi-agent/commit/ca8d757)

**Aanleiding — eigen prompt in deze sessie:**
> "look at DL2, here i did talk about skills, now i will add a sample of skills, to test what happens with the tokens, do i need first tools if i add skills in my project [...] i will clean up each agent now and add skills folder and use the system prompt that it reads the skills folder and the specific skill for each agent."

Vervolgvraag: "gaat dit een verschil maken met de huidige setup, zo ja wat?" → antwoord: ja, skills verhogen input tokens per agent en geven de LLM concrete frameworks i.p.v. generieke taakomschrijving. Geen tools nodig — skills zijn puur tekst.

**Wat is er gedaan:**
- `src/skills/` map aangemaakt met 7 skill-bestanden (markdown):
  - `product-marketing-context.md` — gedeelde kennisbasis (Researcher)
  - `marketing-ideas.md` — jobs-to-be-done, pijnpunten (Researcher)
  - `content-strategy.md` — positionering, 60/30/10 mix (Strateeg)
  - `marketing-psychology.md` — AIDA, social proof, anchoring (Strateeg)
  - `copywriting.md` — PAS, FAB, headline-formules (Copywriter)
  - `copy-editing.md` — redactie-checklist (Copywriter)
  - `social-content.md` — platform-specifieke formats (Social Specialist)
  - `launch-strategy.md` — beoordelingscriteria (Campaign Manager)
- `src/skills/__init__.py`: `load_skill()` utility die skills inlaadt
- Alle 5 agents aangepast: skill als prefix van systeemprompt

**Systeemprompt grootte voor en na:**
- Voor: ~50 tokens per agent (generieke taakomschrijving)
- Na: ~260–417 tokens per agent (skill + taakomschrijving)

**Test — zelfde product (Philips dubbele airfryer), MAX_ITERATIONS=1 (kosten besparen):**

| | Zonder skills (`campaign_20260326`) | Met skills (`campaign_20260328`) |
|---|---|---|
| Iteraties | 3 | 1 (direct goedgekeurd) |
| Goedgekeurd | ja | ja |
| Persona | generiek (Sanne) | concreet met koopredenering in 3 stappen |
| Pijnpunten | globaal | specifiek (smaakgeurtransfer, temperatuurbeheer) |
| Kernboodschap | niet aanwezig | 1 scherpe UVP-zin |
| Contentmix | niet benoemd | 60/30/10 expliciet uitgewerkt |
| Headline | features ("2 bakken, 15 min") | benefit ("Twee gerechten, moeiteloos") |

**Conclusie:**
Skills geven aantoonbaar betere output. De Campaign Manager keurde de campagne met skills direct goed in 1 iteratie, tegen 3 iteraties zonder. De LLM past concrete frameworks toe (PAS, AIDA, jobs-to-be-done) die zonder skill impliciet of afwezig waren. Hogere input tokens per agent, maar minder iteraties = netto vergelijkbaar of lager totaal tokenverbruik. Te meten in LangSmith als V4.

**Zelf bedacht:**
- skills als pure markdown, geen graph wijzigingen nodig
- load_skill() met meerdere namen per agent, gescheiden door ---
- max_iterations op 1 gezet voor kosten tijdens testen

**Bronnen:**
- DL2: marketingskills plugin analyse (aanleiding en skill-indeling per agent)
- marketingskills plugin: https://github.com/coreyhaines31/marketingskills

---

## Stap 23: Graph visualisatie vanuit code — Jupyter notebook
**Datum:** 2026-03-28
**Commit:** [`60682d8`](https://github.com/nickvanhooff/eva-multi-agent/commit/60682d8)

**Aanleiding:**
In de freeCodeCamp LangGraph tutorial zag ik dat je de graph automatisch kunt visualiseren vanuit de code via `graph.get_graph().draw_mermaid_png()`. Dit triggerde de wens om hetzelfde te doen voor Eva, zodat het diagram altijd up-to-date is met de werkelijke code.

**Wat is er gedaan:**
- `graph_visualize.ipynb` aangemaakt in `eva-multi-agent/`
- Notebook laadt de graph via `build_graph()` en toont het diagram als PNG via `IPython.display`
- Fallback naar Mermaid-tekst als PNG rendering mislukt
- Pip install cel toegevoegd bovenaan notebook zodat de juiste dependencies in het Jupyter kernel geladen worden

**Relatie met architecture.md:**
De gegenereerde visualisatie is hetzelfde diagram als het handmatig getekende Graph Flow diagram in `docs/architecture.md` (Stap 2). Het verschil: `architecture.md` is handmatig geschreven Mermaid, dit notebook genereert het diagram automatisch vanuit de werkelijke graph-code. Dit bevestigt dat het handmatige diagram correct was.

**Waarom een notebook i.p.v. een los script?**
Een notebook geeft direct visuele output naast de code — handig voor portfolio en presentaties. Het diagram wordt gegenereerd vanuit de werkelijke graph, niet handmatig getekend, dus het klopt altijd met de code.

**Bronnen:**
- freeCodeCamp LangGraph tutorial: https://www.youtube.com/watch?v=jGg_1h0qzaM
- LangGraph draw_mermaid_png: https://langchain-ai.github.io/langgraph/how-tos/visualization/

---

## Stap 22: Eerste volledige testrun — "Burning Barrel" campagne
**Datum:** 2026-03-25
**Commit:** [`6d3afa9`](https://github.com/nickvanhooff/eva-multi-agent/commit/6d3afa9)
**Output bestand:** `campaigns/campaign_20260325_144508.json`

**Wat is er gedaan:**
Het systeem is voor het eerst volledig end-to-end getest met een eigen product-input. De volgende prompt is handmatig ingevoerd als `product_description`:

```
Burning Barrel
```

Het systeem heeft op basis van die enkele input automatisch een volledige marketingcampagne gegenereerd via alle 5 agents.

**Gegenereerde output (samenvatting):**
- **Doelgroep** (Researcher): 25–45 jaar, €45.000+ inkomen, Noord-Europa, urban/suburban, duurzaamheid & design-gericht
- **Strategie** (Strateeg): eco-design + experience niche, 3 product-edities (Core €199, Premium €279, Accessory kits), UGC + micro-influencer campagne, "Plant a Tree" partnership
- **Positionering**: "De premium, eco-designed fire pit die stijl, veiligheid en Instagram-waardige ervaringen combineert"
- **Tone of Voice**: Vriendelijk, story-driven, visueel & sensorisch, inclusief & community-gericht
- **Copy** (Copywriter): Headline "Ontsteek de avond met Burning Barrel", 3 bodytekst-alinea's, CTA met 15% early-bird korting
- **Social content** (Social Specialist): Instagram caption + hashtags, LinkedIn B2B post, X/Twitter tweet (280 tekens)
- **Campaign Manager**: na 1 iteratie beoordeeld (niet goedgekeurd wegens Groq rate limit — max iteraties bereikt)
- **Afbeelding** (Image Generator): SDXL-Turbo afbeelding gegenereerd op basis van de campagne-content

**Bewijs van eigen werk:**
De input `"Burning Barrel"` is zelfgekozen als testproduct — een vuurkorf, concreet genoeg om realistische output te genereren, maar ook een product waarbij je duidelijk kunt beoordelen of de strategie klopt. Het systeem heeft alle content zelf gegenereerd op basis van die input.

**Wat dit aantoont:**
- De volledige agent pipeline werkt (Researcher → Strateeg → Copywriter → Social Specialist → Campaign Manager → Image Generator)
- State wordt correct doorgegeven tussen agents
- JSON report wordt persistent opgeslagen buiten de Docker container
- SDXL-Turbo genereert een bijpassende productafbeelding

**Zelf bedacht:**
- "Burning Barrel" als testproduct gekozen omdat het een niche, premium outdoor-product is met duidelijke doelgroep en positionering-mogelijkheden — goede indicator voor de kwaliteit van de agents
- Beslissing om de output te bewaren als bewijs voor portfolio (learning outcome: werking aantonen)

---

## Stap 23: Analyse campagne-kwaliteit — ontbrekende creatieve laag
**Datum:** 2026-03-28

**Wat is er gedaan:**
Twee gegenereerde campagnes vergeleken om te beoordelen wat het systeem mist voor een écht overtuigende output:
- `campaign_20260328_223632.json` — zonder tool use (persona-gedreven, aspirationeel)
- `campaign_20260328_230629.json` — met tool use/marktonderzoek (data-gedreven, cijfermatig)

**Observatie:**
De data-gedreven versie is concreter en beter onderbouwd (marktcijfers, concurrentieanalyse, reviewdata). De persona-gedreven versie is emotioneel toegankelijker. Beide missen echter een tussenstap: de vertaling van data-inzichten naar een **centrale creatieve gedachte** die mensen raakt. De copy in beide versies somt features op in plaats van een spanning of verhaal te activeren.

Een overtuigende campagne heeft beide lagen nodig:
1. **Data** — wat wil de doelgroep, waar zit de frustratie, wat doet de concurrent?
2. **Creatief concept** — welke menselijke spanning of emotie maakt dit product relevant?

Het systeem springt nu direct van data/persona naar copy, zonder die tweede laag.

**Zelf bedacht:**
- een creative concept agent toevoegen tussen strateeg en copywriter, data alleen is niet genoeg voor een overtuigende campagne
- campaign manager ook laten beoordelen of het overtuigend is, niet alleen of de strategie klopt

**Wat toegevoegd wordt:**
- `creative_concept_agent` — genereert één campagneconcept met centrale menselijke spanning + 2–3 creatieve richtingen, ná de Strateeg en vóór de Copywriter
- Campaign Manager prompt uitbreiden met kwalitatieve beoordeling op emotionele overtuigingskracht naast strategische correctheid

**Aangepaste flow:**
```
Researcher → Strateeg → [Creative Concept] → Copywriter → Social Specialist → Campaign Manager → Image Generator
```

---

## Stap 24: README bijgewerkt — skills en tools per agent gedocumenteerd
**Datum:** 2026-03-28
**Commit:** [`d652248`](https://github.com/nickvanhooff/eva-multi-agent/commit/d652248)

**Wat is er gedaan:**
- agententabel in `README.md` uitgebreid met twee kolommen: skills en tools
- per agent zichtbaar welke skills geladen worden via `load_skill()` en welke tools gebruikt worden

**Zelf bedacht:**
- skills en tools in de readme zetten zodat het in één oogopslag duidelijk is wat elke agent kan

---

## Stap 25: RAG — onderzoek en stack keuze
**Datum:** 2026-03-29
**Branch:** `feature/rag-pdf-ingestion`

**Wat is er gedaan:**
Onderzocht hoe een grote PDF (bijv. productbeschrijving, boek, merkbriefing) als input gebruikt kan worden voor de Researcher agent. Het doel is dat het systeem campagnes kan genereren op basis van een extern document, niet alleen op basis van een korte productstring.

Conclusie: RAG (Retrieval-Augmented Generation) is de juiste aanpak. Een 200-pagina PDF past niet in één prompt, en zelfs als het paste verliest een LLM focus bij zeer lange context ("Lost in the Middle", Liu et al. 2023).

**Gekozen stack:**

| Laag | Keuze | Reden |
|---|---|---|
| PDF parser | PyMuPDF | Gratis, lokaal, geen extra deps, werkt in Docker |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Lokaal op CPU, ~80MB, gratis, snel genoeg voor 200p |
| Vector store | ChromaDB | In-process, persistent by default, clean API, swapbaar naar cloud |
| Glue | LangChain | Zit al in de stack |

PostgreSQL (+ pgvector) is overwogen maar afgevallen: voegt alleen infrastructuurcomplexiteit toe zonder meerwaarde zolang Eva geen relationele data heeft. Zie `docs/rag.md` voor volledige onderbouwing.

**Bronnen:**
- Lewis et al. (2020) RAG paper: `arxiv.org/abs/2005.11401`
- "Lost in the Middle": `arxiv.org/abs/2307.03172`
- ChromaDB docs: `docs.trychroma.com`
- Sentence Transformers: `sbert.net`

**Zelf bedacht:**
- postgresql afgevallen omdat er geen relationele data is in eva — rag-only use case
- vaste queries per run in plaats van dynamische tool calls, eenvoudiger en voorspelbaarder
- alleen de researcher krijgt toegang tot de pdf, de rest werkt via state

---

## Stap 26: RAG implementatie — pdf_ingestion node toegevoegd aan graph
**Datum:** 2026-03-29
**Branch:** `feature/rag-pdf-ingestion`
**Commits:** `d794265` → `da39408` (7 commits)

**Wat is er gedaan:**
RAG geïmplementeerd als nieuwe node (`pdf_ingestion`) in de bestaande LangGraph pipeline. De node draait vóór de Researcher en is volledig optioneel — zonder PDF slaat hij stilletjes over.

**Bestanden gewijzigd:**

| Bestand | Wijziging |
|---|---|
| `requirements.txt` | pymupdf, sentence-transformers, chromadb, langchain-community toegevoegd |
| `src/rag.py` | nieuw — volledige RAG module (laden, chunken, embedden, retrieven) |
| `src/state.py` | `pdf_path: Optional[str]` en `pdf_context: str` toegevoegd |
| `src/agents/researcher.py` | `pdf_context` injecteren als extra sectie in de prompt |
| `src/graph.py` | `pdf_ingestion_node` toegevoegd als eerste node, `START → pdf_ingestion → researcher` |
| `src/main.py` | `run_campaign()` accepteert nu optionele `pdf_path` parameter |

**Hoe het werkt:**

```
PDF → PyMuPDF laden → RecursiveCharacterTextSplitter (500/50) → HuggingFaceEmbeddings → ChromaDB
                                                                                              ↑
5 vaste campaign queries → vector similarity search → TOP_K=3 chunks per query → deduplicatie → pdf_context string
```

De `pdf_context` string wordt als extra sectie in de Researcher-prompt geïnjecteerd:
```
Productdocumentatie (uit PDF via RAG):
[retrieved passages]

Actuele zoekresultaten (DuckDuckGo):
...
```

**Gebruik:**
```python
# Zonder PDF — werkt exact zoals voor (backwards-compatible)
run_campaign("dubbele airfryer van Philips")

# Met PDF — RAG draait automatisch vóór de Researcher
run_campaign("dubbele airfryer van Philips", pdf_path="data/philips.pdf")
```

**Zelf bedacht:**
- pdf_ingestion als aparte node zodat het los te testen is van de researcher
- backwards-compatible — geen pdf_path betekent gewoon overslaan, bestaande flows breken niet
- deduplicatie op chunk-content zodat dezelfde passage niet meerdere keren in de prompt eindigt
- 5 vaste queries gericht op campagne-relevante info (doelgroep, usps, tone of voice, markt, positionering)

---

## Stap 27: Fix — RecursiveCharacterTextSplitter import fout
**Datum:** 2026-03-29
**Branch:** `feature/rag-pdf-ingestion`
**Commit:** `9db9eef`

**Wat is er gedaan:**
Bij het draaien van Docker crashte de container direct met:

```
ModuleNotFoundError: No module named 'langchain.text_splitter'
```

**Oorzaak:**
LangChain >= 0.2 heeft de text splitters verplaatst uit `langchain` naar een apart pakket `langchain-text-splitters`. De import in `src/rag.py` was nog de oude locatie.

**Fix:**

| Bestand | Oud | Nieuw |
|---|---|---|
| `src/rag.py` | `from langchain.text_splitter import ...` | `from langchain_text_splitters import ...` |
| `requirements.txt` | — | `langchain-text-splitters>=0.2.0` toegevoegd |

**Zelf bedacht:**
- foutmelding direct herkend als langchain versie-issue, niet als code-fout

---

## Stap 28: data/ map aangemaakt — PDF input voor RAG
**Datum:** 2026-03-29
**Branch:** `feature/rag-pdf-ingestion`
**Commit:** `b3cd3d4`

**Wat is er gedaan:**
Een `data/` map aangemaakt als vaste locatie voor PDF-bestanden die als input meegegeven worden aan het systeem. Docker kon de map niet zien zonder een volume mount.

**Wijzigingen:**

| Bestand | Wijziging |
|---|---|
| `data/.gitkeep` | Map aanwezig houden in git zonder inhoud |
| `data/.gitignore` | `*.pdf` uitgesloten van git — PDFs worden niet gecommit |
| `docker-compose.yml` | `./data:/app/data` volume mount toegevoegd aan eva service |

**Gebruik:**
1. PDF neerzetten in `eva-multi-agent/data/`
2. In `src/main.py` instellen: `pdf = "data/naam.pdf"`
3. `docker compose build && docker compose up`

**Zelf bedacht:**
- `.gitignore` in de data map zodat pdfs niet per ongeluk gecommit worden — kunnen grote bestanden zijn
- `.gitkeep` zodat de lege map wel in git staat en iedereen direct weet waar de pdf naartoe moet

---

## Stap 29: Campagne-vergelijking — zonder RAG vs. met RAG
**Datum:** 2026-03-29
**Branch:** `feature/rag-pdf-ingestion`
**Bestanden:** `campaigns/campaign_20260328_230629.json` (oud) vs. `campaigns/campaign_20260329_174603.json` (nieuw)

**Wat is er gedaan:**
Twee gegenereerde campagnes vergeleken voor hetzelfde product ("dubbele airfryer met 2 bakken van Philips") — één zonder RAG (alleen DuckDuckGo + Wikipedia) en één met RAG (Philips handleiding PDF).

---

### Vergelijking

| | Zonder RAG | Met RAG |
|---|---|---|
| **Input** | product string + DDGS + Wikipedia | product string + PDF handleiding |
| **Iteraties** | 1 — direct goedgekeurd | 3 — meer verfijning nodig |
| **Productfeatures** | Verzonnen: "Twin-Cook Pro", "Cerami-Tech + Quick-Wipe" | Echt: HomeID-app, stoom+air frying, 3,5L + 1,5L bakken, descaling-cyclus, 5 jaar garantie |
| **Prijs** | €329 (van marktonderzoek) | €299 / €250–€350 (uit handleiding) |
| **Kernpositionering** | Synchronisatie (Twin-Cook Pro) | Stoom + dual-cooking combinatie |
| **Concurrenten** | Ninja, Tefal, Cosori, huismerk | Ninja (géén stoom), Cosori (lagere capaciteit), Cuisinart 2-in-1 |
| **Marktcijfers** | Sterk: 12% CAGR, 1,8M units, 31% sync-frustratie | Geen marktcijfers — productdocumentatie heeft dit niet |
| **Duurzaamheid** | Niet vermeld | 100% recyclebaar — letterlijk uit de handleiding |
| **Doelgroep** | Persona "Sanne, 38" — model-gegenereerd | 28–55 jaar, €3.500+ netto, HomeID-app gebruikers — uit PDF |

---

### Conclusie

**RAG levert:** feitelijke productinfo die het model zelf niet kon verzinnen — echte features, juiste prijsrange, correcte USPs, relevante concurrentievergelijking op basis van wat het product werkelijk kan.

**DDGS levert:** marktintelligentie die de PDF niet heeft — CAGR, marktgrootte, consumentenfrustaties, concurrentieprijzen.

**Probleem:** zonder RAG verzon het model features die klinken als Philips maar het niet zijn ("Twin-Cook Pro"). Met RAG verdwijnen de marktcijfers.

**Ideale situatie:** beide combineren. De Researcher gebruikt RAG voor productfeitenen en DDGS/Wikipedia voor marktcontext. Dit is al het geval in de huidige implementatie — beide inputs zitten in de Researcher-prompt. De campagne met RAG bewijst dat productfeatures nu correct zijn; de marktcijfers kwamen in dit geval minder sterk terug omdat de PDF-context dominant was.

**Zelf bedacht:**
- verzonnen features zijn een groter risico dan ontbrekende marktcijfers — een klant kan een campagne met foute productinfo niet gebruiken
- rag lost het belangrijkste probleem op: hallucinatie over het product zelf
- volgende stap: testen of de researcher de twee bronnen beter in balans brengt bij een minder uitgebreide pdf

---

## Stap 30: Skills analyse — van product naar boek
**Datum:** 2026-03-29
**Branch:** `feature/rag-pdf-ingestion`

**Gebruikte prompt:**
> "kijk wat er nu in mijn skills zit wat niet relevant is voor boek campagnes, of kijk wat er mist bij skills of wat anders wat voor boeken een goede skill zou zijn, hiervoor is het vooral om een product gegaan, nu wil ik de focus verleggen naar een boek. geef me advies wat ik het beste kan aanpassen hiervoor."

**Wat is er gedaan:**
Twee boek-campagnes geanalyseerd (`campaign_20260329_204823.json` en `campaign_20260329_205551.json`) voor het boek *Een-jaar-in-de-Molukken*. Alle 8 huidige skills vergeleken met wat een boek-campagne werkelijk nodig heeft.

**Bevindingen per skill:**

| Skill | Status | Probleem |
|---|---|---|
| `content-strategy.md` | ✅ Werkt | 60/30/10 is universeel toepasbaar |
| `copy-editing.md` | ✅ Werkt | Platform-agnostisch |
| `marketing-psychology.md` | ✅ Werkt | Social proof, autoriteit, schaarste werken ook voor boeken |
| `launch-strategy.md` | ✅ Werkt | Criteria zijn breed genoeg |
| `social-content.md` | ⚠️ Aanpassen | Mist Bookstagram/BookTok formats en literaire community-content |
| `product-marketing-context.md` | ⚠️ Aanpassen | Volledig product-gericht — boek heeft andere dimensies: thema, auteur, genre, leeservaring |
| `copywriting.md` | ⚠️ Aanpassen | PAS/FAB zijn product-frameworks — boekcopy vereist blurb-format, premise-hook, thematische belofte |
| `marketing-ideas.md` | ⚠️ Aanpassen | "Jobs-to-be-done" mist het boek-specifieke motief: identiteit, escapisme, verbinding, kennis |

**Wat volledig ontbreekt:**
- Boek-discovery funnel: Goodreads, NetGalley, bibliotheken, literaire boekhandels
- Literaire community formats: Bookstagram, BookTok, leesclubs, literaire nieuwsbrieven
- Auteur-platform: geloofwaardigheid via auteur, bronvermelding, academische endorsement
- Boekomschrijvings-formats: achterflapstekst, Bol.com/Amazon-beschrijving, reading group guide

**Concreet actieplan:**

| Actie | Bestand | Wat verandert |
|---|---|---|
| Aanpassen | `product-marketing-context.md` | Boek-modus toevoegen: genre, auteur, thema, leeservaring als analysedimensies |
| Aanpassen | `copywriting.md` | Blurb-format toevoegen: premise → belofte → haak |
| Aanpassen | `social-content.md` | Bookstagram/BookTok, quote-kaart format, leesclub-content |
| Nieuw | `book-marketing.md` | Boek-discovery funnel, literaire kanalen, auteur-platform, leescommunity |

**Waarom dit relevant is:**
De huidige campagnes voor het boek gebruiken product-taal ("USPs", "prijs-kwaliteit", "early-bird korting") die geforceerd aanvoelen voor een historisch-literair werk. De agents missen de context om het verschil te maken tussen een fysiek product en een cultureel werk.

**Zelf bedacht:**
- book-marketing.md als nieuwe skill in plaats van product-marketing aanpassen — dan blijft het systeem bruikbaar voor beide
- auteur-platform als apart concept toevoegen, dat bestaat niet bij producten
- discovery funnel voor boeken is fundamenteel anders dan een product-funnel: goodreads/reviews/leesclubs zijn de motor, niet google shopping

---

## Stap 31: Dynamische skill selectie per campaign_type
**Datum:** 2026-03-29
**Branch:** `feature/rag-pdf-ingestion`

**Gebruikte prompt:**
> "houd rekening dat de uiteindelijke klant vanalles wil promoten met een campagne, dus zorg ervoor dat het de juiste skill pakt en niet onnodig skills mee stuurt. voor nu ligt de focus op een campagne voor een boek"

**Wat is er gedaan:**
Nieuw skill-systeem gebouwd waarbij elke agent de juiste skills laadt op basis van `campaign_type`. Vóór deze stap had elke agent een vaste module-level `SYSTEM_PROMPT` die altijd dezelfde skills inlaadde, ongeacht of het een product- of boekcampagne was.

**Nieuwe bestanden:**
- `src/skills/book-context.md` — boek-researcher context: genre, auteur, lezermotieven (identiteit, kennis, escapisme, verbinding, educatie)
- `src/skills/book-copywriting.md` — blurb-format (hook → premise → thematische belofte → CTA), geen FAB, geen productkenmerken
- `src/skills/book-social.md` — Bookstagram, BookTok/Reels, LinkedIn voor non-fiction, Goodreads, literaire community's
- `src/skills/book-launch-strategy.md` — CM-beoordelingscriteria voor boeken: auteurgeloofwaardigheid, emotionele haakjes, community-integratie, literaire toon; expliciet géén product-criteria
- `src/skills/skills_config.py` — centrale SKILL_MAP: campaign_type → agent → skill-namen; `get_skills(campaign_type, agent)` als publieke interface

**SKILL_MAP:**

| Agent | product | book |
|---|---|---|
| researcher | `research-brief` | `book-context` |
| copywriter | `copywriting` | `book-copywriting` |
| social_media | `social-media` | `book-social` |
| email_marketer | `email-marketing` | `email-marketing` |
| campaign_manager | `launch-strategy` | `book-launch-strategy` |

**Gewijzigde bestanden:**
- `src/state.py` — `campaign_type: str` toegevoegd als verplicht input-veld
- `src/agents/researcher.py` — statische `SYSTEM_PROMPT` vervangen door dynamische opbouw in node-functie
- `src/agents/copywriter.py` — idem
- `src/agents/social_specialist.py` — idem
- `src/agents/campaign_manager.py` — idem; nu laadt de CM `book-launch-strategy` voor boek-campagnes in plaats van productgerichte `launch-strategy`
- `src/main.py` — `campaign_type` parameter toegevoegd aan `run_campaign()`, default `"product"`; demo ingesteld op `"book"`

**Patroon per agent (na wijziging):**
```python
campaign_type = state.get("campaign_type", "product")
skill_content = get_skills(campaign_type, "researcher")
system_prompt = (skill_content + "\n\n---\n\n" if skill_content else "") + _BASE_PROMPT
```

**Waarom dit relevant is:**
De Campaign Manager beoordeelde boekcampagnes eerder met productcriteria (`launch-strategy.md`): hij keek naar prijsvermelding, USP's, features. Een boek heeft dat niet — de CM moet kijken naar auteurgeloofwaardigheid, emotionele haakjes en literaire toon.

**Backwards-compatibiliteit:**
`get_skills()` valt terug op `"product"` als een onbekend campaign_type wordt meegegeven. Bestaande aanroepen zonder `campaign_type` werken via de default `"product"`.

**Zelf bedacht:**
- book-launch-strategy als apart bestand (niet combineren met product-versie) — schoner, geen if/else in de skill-tekst zelf
- get_skills als centrale functie zodat agents niet zelf de SKILL_MAP hoeven te importeren
- strategist buiten de SKILL_MAP gelaten — strategie-aanpak is voor boek en product vergelijkbaar genoeg

---

## Stap 32: Campagne beoordeling + no-fabrication regels toegevoegd
**Datum:** 2026-03-29
**Branch:** `feature/rag-pdf-ingestion`

**Gebruikte prompt:**
> "kijk naar nieuwe output, beoordeel deze en vergelijk — is het campagne waardig?"

**Wat is er gedaan:**
Campaign output (`campaign_20260329_212825.json`) beoordeeld na de skill-update. De campagne liet duidelijk zien dat de book-skills werkten (literaire toon, juiste kanalen, emotionele copy), maar ook dat het model ging hallucineren zodra het iets niet in de PDF kon vinden.

**Gevonden problemen:**
- `Auteur [Naam]` placeholder aanwezig, maar model verzond er wél een verzonnen backstory bij ("historicus en zoon van Molukse immigranten")
- `Dr. Marielle Sari, cultuurhistoricus bij het Rijksmuseum van Ethnologie` — volledig gefabriceerd persoon en quote
- Digitale producten verzonden: "Interactieve online kaarten (Leaflet/ArcGIS)", "Audio-fragmenten" — staan niet in het boek

**Fix:**
- `book-context.md` — bronregel toegevoegd: geen verzonnen aantallen, media of auteursinformatie zonder bewijs in de PDF
- `book-copywriting.md` — no-fabrication regel toegevoegd: geen verzonnen quotes, endorsements, auteursverhaal of digitale producten; element weglaten als het ontbreekt

**Zelf bedacht:**
- fix in zowel context (researcher) als copywriting skill — het probleem begint bij de researcher die specs verzint, de copywriter gebruikt die dan
- niet alleen copywriter fixen, dan lost het probleem zich niet op

---

## Stap 33: RAG queries aangepast per campaign_type
**Datum:** 2026-03-29
**Branch:** `feature/rag-pdf-ingestion`

**Gebruikte prompt:**
> (voortkomend uit de campagne-analyse) — product-queries draaiden tegen een boek-PDF, wat hallucinaties veroorzaakte

**Wat is er gedaan:**
De vaste `CAMPAIGN_QUERIES` list in `rag.py` was volledig product-gericht. Bij een boek-campagne vroeg de RAG dus naar "USPs" en "markt en concurrenten" — begrippen die een boek-PDF niet bevat. Het model vulde dat gat dan zelf in.

Oplossing: queries gesplitst per campaign_type in een `_QUERIES` dict.

**Boek-queries (nieuw):**
1. Wie is de auteur en wat is zijn/haar achtergrond?
2. Wat is het centrale thema, genre en de belofte van het boek?
3. Welke historische/culturele context wordt beschreven?
4. Wat maakt dit boek uniek?
5. Voor welke lezer en welke leeservaring?

`retrieve_pdf_context()` accepteert nu `campaign_type` als parameter. `graph.py` geeft dit door vanuit de state. `build_vector_store` hernoemd naar `_build_vector_store` (intern gebruik).

**Zelf bedacht:**
- queries zijn de input van het RAG-systeem — verkeerde vragen = verkeerde passages = hallucinaties stroomafwaarts
- product-queries behouden zodat bestaande campagnes ongewijzigd blijven

---

## Stap 34: Chunk size en overlap aangepast
**Datum:** 2026-03-29
**Branch:** `feature/rag-pdf-ingestion`

**Gebruikte prompt:**
> "wat voor invloed heeft de chunk size en overlap? is 500 en 50 te groot?"

**Wat is er gedaan:**
Instellingen in `rag.py` aangepast na analyse van wat chunk_size en overlap doen voor dit gebruik.

**Bevinding:** de comment zei "500 words" maar `RecursiveCharacterTextSplitter` telt karakters. 500 karakters ≈ 80-100 woorden ≈ 3-4 zinnen — te klein voor narratieve boektekst.

**Probleem met de oude instelling:**
- 500 chars fragmenteert zinnen halverwege — een passage zonder omringende context zegt weinig
- TOP_K=3 × 5 queries = tot 7.500 karakters in de researcher-prompt — te veel ruis voor een klein model

**Nieuwe instelling:**

| Parameter | Oud | Nieuw | Reden |
|---|---|---|---|
| `CHUNK_SIZE` | 500 chars | 800 chars | Meer context per passage voor narratieve tekst |
| `CHUNK_OVERLAP` | 50 chars | 80 chars | ~10% verhouding behouden |
| `TOP_K` | 3 | 2 | Minder ruis in de researcher-prompt |

**Zelf bedacht:**
- TOP_K verlagen is effectiever dan chunk_size verkleinen bij een klein model
- comment gecorrigeerd van "words" naar "characters"

---

## Stap 35: Agent config registry — LLM-instellingen op één plek
**Datum:** 2026-03-30
**Branch:** `feature/rag-pdf-ingestion`

**Gebruikte prompt:**
> "wat is een professionele aanpak om per agent de llm te kunnen regelen op 1 plek?"

**Probleem:**
Elke agent hardcodede provider, model en temperature direct in de `call_llm()` aanroep. Om één model te wisselen moest je 5 bestanden aanpassen.

```python
# Oud — in elke agent apart
call_llm(system_prompt, user_prompt, temperature=0.4, provider="openrouter", model="nvidia/nemotron-3-nano-30b-a3b:free")
```

**Wat is er gedaan:**
`AGENT_LLM_CONFIG` dict toegevoegd in `src/llm.py` — één plek met alle LLM-instellingen per agent. `get_agent_config(agent_name)` geeft de juiste config terug. Alle 5 agents (+ strateeg) bijgewerkt om dit te gebruiken.

```python
# Nieuw — agents lezen config op uit llm.py
call_llm(system_prompt, user_prompt, **get_agent_config("researcher"))
```

**AGENT_LLM_CONFIG:**

| Agent | Provider | Model | Temperature |
|---|---|---|---|
| researcher | openrouter | nvidia/nemotron-3-nano-30b-a3b:free | 0.4 |
| strateeg | openrouter | nvidia/nemotron-3-nano-30b-a3b:free | 0.5 |
| copywriter | openrouter | nvidia/nemotron-3-nano-30b-a3b:free | 0.9 |
| social_specialist | openrouter | nvidia/nemotron-3-nano-30b-a3b:free | 0.8 |
| campaign_manager | openrouter | nvidia/nemotron-3-nano-30b-a3b:free | 0.3 |

**Zelf bedacht:**
- zelfde patroon als SKILL_MAP — centrale config, agents lezen zichzelf op
- fallback in get_agent_config zodat onbekende agents niet crashen

---

## Stap 36: Frontend prototype — Google Stitch via MCP
**Datum:** 2026-03-30
**Branch:** `feature/rag-pdf-ingestion`

**Gebruikte prompt:**
> Doel: Ik wil experimenteren met Google Stitch via MCP in Claude Code om een UX-gedreven frontend prototype te maken voor mijn multi-agent systeem.
>
> Werkwijze:
> 1. Gebruik Google Stitch (via MCP) om een eerste UI-prototype te genereren. https://stitch.withgoogle.com/docs/mcp/setup
> 2. Focus op UX-principes: duidelijke informatie-hiërarchie, minimale cognitieve belasting, consistente componentstructuur, schaalbaarheid voor toekomstige features
> 3. Het ontwerp moet geschikt zijn voor een multi-agent systeem dashboard.
>
> Rolverdeling:
> - Google Stitch fungeert als **Design Agent**
> - Claude Code fungeert als **Implementation Agent**
>
> Het prototype moet minimaal bevatten:
> - dashboardoverzicht van agents
> - agent status indicators
> - interactiepaneel met agents
> - logs / activiteitsoverzicht
> - duidelijke navigatiestructuur
>
> Output: gegenereerd UI-ontwerp vanuit Stitch, voorstel voor componentstructuur, aanbevelingen voor frontend architectuur, suggesties voor verdere iteraties.

**Context:**
Prompt aangescherpt met ChatGPT om duidelijkere doelen, UX-focus en een betere AI-workflow te definiëren.

**Wat is er gedaan:**
Oriëntatiestap: experiment met Google Stitch als design tool via MCP-integratie in Claude Code. Doel is een UI-prototype voor het Eva multi-agent dashboard — niet alleen functioneel maar ook UX-gedreven.

**Motivatie:**
Het systeem heeft tot nu toe alleen een CLI-interface. Een dashboard maakt de agent-status, logs en campagne-output inzichtelijk zonder door JSON-bestanden te bladeren. Google Stitch kan snel een visueel prototype genereren dat als basis dient voor de implementatie.

**Rolverdeling AI-agents in dit experiment:**
- Google Stitch → Design Agent (UI-ontwerp, componentstructuur)
- Claude Code → Implementation Agent (code-uitwerking op basis van ontwerp)

**Zelf bedacht:**
- twee AI-tools als agents in een design-workflow inzetten — niet één tool alles laten doen
- UX-principes als harde requirements meegeven, niet alleen "maak een dashboard"
- prompt eerst verfijnen via ChatGPT voor betere output van Stitch

---

## Stap 37: Google Stitch — 5 schermen gegenereerd en gedocumenteerd
**Datum:** 2026-03-30
**Branch:** `feature/frontend-stitch`

**Wat is er gedaan:**
Op basis van het plan uit stap 36 zijn 5 desktop-schermen gegenereerd via `generate_screen_from_text` (Stitch MCP). Schermen opgehaald via `list_screens`, screenshots opgeslagen in `docs/screenshots/stitch/`.

**Gegenereerde schermen:**

| Scherm | Bestand |
|---|---|
| Eva Dashboard | [`01_dashboard.png`](docs/screenshots/stitch/01_dashboard.png) |
| New Campaign | [`02_new_campaign.png`](docs/screenshots/stitch/02_new_campaign.png) |
| Campaign Running Progress | [`03_campaign_running.png`](docs/screenshots/stitch/03_campaign_running.png) |
| Campaign Results | [`04_campaign_results.png`](docs/screenshots/stitch/04_campaign_results.png) |
| Campaign History | [`05_campaign_history.png`](docs/screenshots/stitch/05_campaign_history.png) |

**Stitch project:** `9283653711690935700`
**Design system:** dark, `#6366f1` indigo, Geist/Inter, ROUND_EIGHT, TONAL_SPOT

**Beoordeling:**
Alle schermen matchen de data die Eva al produceert: campaign_type badges (product/book), iteratie-tellers, CM approval status, PDF upload, agent pipeline visualisatie. De designs sluiten direct aan op de bestaande `CampaignState` velden.

**Zelf bedacht:**
- screenshot-urls ophalen via `list_screens` en opslaan als png via playwright
- beoordeling of stitch-output aansluit op bestaande state-structuur

---

## Stap 38: Frameworkkeuze frontend + backend — voorbereiding decision log
**Datum:** 2026-03-30
**Branch:** `feature/frontend-stitch`

**Gebruikte prompt:**
> dit is een belangrijk moment voor stappen. hier maak ik een keuze voor de frameworks. zet hierbij in stappen.md om een decision log hierbij van te gaan maken. mijn opties zijn nuxt react+vite of pure html voor frontend, keuze word react+vite omdat het snel opgezet is en makkelijk dynamisch werkt. ookal ben ik al bekend met nuxt, alleen dit is net te zwaar voor zo'n project. react+vite is in no time opgezet en opgestart dus dit maakt het ook een sneller ontwikkelproces, nuxt is minder snel in het project opstarten ookal heb ik hier wel al meer kennis is. de keuze om ook voor react te gaan is dat ik dan ook wat meer ervaring opdoe met react+vite. ook moet hier de backend keuze gemaakt worden. hier was de keuze fastapi of django, django is een zwaardere api en veel te uitgebreid om een simpele api op te zetten die nu nodig is. django is een groter framework wat een beetje overkill is voor dit moment. zet ook erbij dat ik dit nog even moet onderzoeken en moet beargumenteren en dot research voor moet benoemen. een succescriteria is bijvoorbeeld snelheid, ontwikkeltijd, compatible in een docker container, op basis van eigen ervaring. en voor de frontend is de keuze niet zo groot omdat ik een ai engineer ben en geen designer die veel meer met frontend bezig is.

**Wat is er gedaan:**
Frameworkkeuze gemaakt voor de frontend en backend van het Eva dashboard. Deze keuze wordt uitgewerkt in een apart decision log (DL4).

**Frontend — keuze: React + Vite**

Opties afgewogen:

| Optie | Reden afgevallen |
|---|---|
| Pure HTML + JS | wordt snel rommelig bij dynamische state (pipeline, logs, polling) |
| Nuxt.js | te zwaar voor dit project; SSR niet nodig; langzamer om op te starten |
| **React + Vite** ✓ | snel opgezet, component-based, ideaal voor dynamische UI |

Keuze voor React + Vite omdat:
- in no time opgezet en gestart (`npm create vite`)
- `useState`/`useEffect` volstaat voor polling en live agent-status
- Stitch HTML makkelijk te vertalen naar JSX
- als AI engineer is de frontend keuze secundair — snelheid van ontwikkeling is leidend
- ook: nieuwe ervaring opdoen met React + Vite (kennis van Nuxt is al aanwezig)

**Backend — keuze: FastAPI** *(nog te onderbouwen via DOT research)*

Opties afgewogen:

| Optie | Reden afgevallen |
|---|---|
| Django | te zwaar framework; veel overhead voor een simpele API; overkill |
| **FastAPI** ✓ | lichtgewicht, snel, past bij bestaande Python-stack |

⚠️ **Nog te doen voor decision log:** DOT-onderzoeksmethode benoemen, keuze verder beargumenteren met bronnen en eigen ervaring.

**Succescriteria (voor DL4):**
- ontwikkeltijd: frontend in < 1 sprint werkend
- snelheid opstarten: project draait lokaal binnen 5 minuten
- compatibel in Docker container
- aansluitend op bestaande Eva Python-backend
- gebaseerd op eigen ervaring en kennis

**Zelf bedacht:**
- react+vite gekozen ondanks meer kennis van nuxt — bewust nieuwe kennis opdoen
- fastapi als logische keuze vanwege bestaande python-stack, maar nog onderbouwen
- dit moment vastleggen als vertrekpunt voor decision log DL4

---

## Stap 39: FastAPI backend opgezet in eva Docker container
**Datum:** 2026-03-30
**Branch:** `feature/frontend-stitch`

**Wat is er gedaan:**
FastAPI toegevoegd als API-laag aan de bestaande `eva` container. De CLI-entrypoint (`python -m src.main`) is vervangen door `uvicorn`. `run_campaign()` draait async via `asyncio.to_thread` zodat de API niet blokkeert.

**Architectuur:**
```
Docker container (eva) — port 8000
  POST /campaigns          → start campagne, geeft job_id terug
  GET  /campaigns/{id}     → poll status (queued / running / done / failed)
  GET  /campaigns          → lijst van opgeslagen JSON-rapporten
  GET  /pdfs               → beschikbare PDF's in data/
  POST /pdfs/upload        → PDF uploaden naar data/
```

**Aangepaste bestanden:**

| Bestand | Wijziging |
|---|---|
| `src/api.py` | nieuw — FastAPI app met alle endpoints |
| `requirements.txt` | `fastapi`, `uvicorn[standard]`, `python-multipart` toegevoegd |
| `Dockerfile` | CMD → `uvicorn src.api:app --host 0.0.0.0 --port 8000` |
| `docker-compose.yml` | `ports: 8000:8000` toegevoegd aan eva service |

**Keuzes:**
- 1 container (niet 2): FastAPI zit in dezelfde `eva` container — geen inter-container communicatie nodig, `campaigns/` en `data/` volumes al gemount
- async via `asyncio.to_thread`: `run_campaign()` is blocking (LangGraph), draait in thread pool
- job status in-memory dict: eenvoudig, voldoende voor eerste versie
- PDF upload + bestaande PDFs kiezen: beide ondersteund via aparte endpoints

**Verificatie:**
```bash
docker compose up --build
curl -X POST http://localhost:8000/campaigns \
  -H "Content-Type: application/json" \
  -d '{"product_description":"test","campaign_type":"product"}'
# → {"job_id": "..."}
curl http://localhost:8000/campaigns/{job_id}
# → {"status": "done", "result": {...}}
```

**Zelf bedacht:**
- 1 container i.p.v. 2 — simpeler voor eerste versie, volumes al beschikbaar
- asyncio.to_thread omdat langgraph sync is maar api async moet blijven
- job dict in memory, niet in db — bewuste keuze voor nu

---

## Stap 40: React+Vite frontend gebouwd + SSE streaming toegevoegd
**Datum:** 2026-03-30
**Branch:** `feature/frontend-stitch`

**Wat is er gedaan:**
React+Vite frontend opgezet op basis van de 5 Stitch-designs. API uitgebreid met SSE streaming via `graph.stream()` zodat agent-events real-time naar de frontend worden gestuurd.

**API-wijzigingen (`src/api.py`):**
- `graph.invoke()` vervangen door `graph.stream()` — yielded per node een state-update
- `jobs[job_id]["events"]` lijst bijgehouden per job
- `GET /campaigns/{job_id}/stream` — SSE endpoint (EventSource)
- `GET /campaigns/{job_id}/events` — alle events tot nu (reconnect)

**Frontend (`frontend/`):**

| Bestand | Beschrijving |
|---|---|
| `src/api.js` | fetch wrapper + `streamCampaignEvents()` via EventSource |
| `src/App.jsx` | React Router met 5 routes |
| `src/components/Sidebar.jsx` | navigatie sidebar |
| `src/components/AgentPipeline.jsx` | 7-node pipeline visualisatie (idle/active/done) |
| `src/pages/Dashboard.jsx` | stats, pipeline overzicht, recente campagnes |
| `src/pages/NewCampaign.jsx` | type toggle, beschrijving, PDF upload, launch |
| `src/pages/CampaignLive.jsx` | SSE stream, live pipeline, activity log |
| `src/pages/CampaignResults.jsx` | tabs Strategy/Copy/Social/Image |
| `src/pages/CampaignHistory.jsx` | filter + tabel van alle campagnes |

**Real-time flow:**
```
POST /campaigns → job_id
→ navigate /campaigns/{id}/live
→ EventSource /campaigns/{id}/stream
→ elk node-event → pipeline highlighted + log regel
→ bij __done__ → redirect naar /campaigns/{id} (results)
```

**Tech stack:**
- React + Vite (npm create vite --template react)
- react-router-dom (routing)
- @tailwindcss/vite (styling)
- Geen externe UI library — styling via CSS variables uit Stitch design system

**Zelf bedacht:**
- eventSource sluiten bij __done__ of __error__ node
- graph.stream() node-events filteren op relevante velden per node (_NODE_FIELDS)
- vite proxy /api → http://localhost:8000 voor dev zonder cors-issues

---

## Stap 41: Campaign lookup fix — opgeslagen campagnes niet gevonden
**Datum:** 2026-03-31
**Branch:** `feature/frontend-stitch`

**Gebruikte prompt:**
> i did test it by myself, it works to generate a campaign, i see the campaign is being generated and see the live view of it, but if i want to view older campaigns or click on the new campaign in the history or recent campaigns i do not see the campaign, i get "Campaign not found" and it is not the same url as the other what was showing with live

**Probleem:**
Klikken op een campagne vanuit History of Dashboard gaf "Campaign not found". De API zocht alleen in de in-memory `jobs` dict, maar opgeslagen campagnes staan als `campaign_*.json` op schijf.

**Oplossing:**
`GET /campaigns/{job_id}` zoekt nu eerst in-memory, daarna in `campaigns/{job_id}.json` op schijf. Navigatie gebruikt `encodeURIComponent(filename)` en CampaignResults decodeert dit weer.

**Zelf bedacht:**
- bestaande GET endpoint uitbreiden ipv nieuw endpoint — minder frontend-aanpassingen
- _events.json bestanden uitsluiten van glob-match

---

## Stap 42: Image serving fix + agent denkproces logging
**Datum:** 2026-03-31
**Branch:** `feature/frontend-stitch`

**Gebruikte prompt:**
> image is niet geladen, dit gaat fout: Failed to load resource: the server responded with a status of 404 (Not Found)
>
> tijdens live wil ik alles zien wat welke agent stuurt naar welke agent en wat er ontvangen word, dit word toch ook gelogd, dus het denkprocess van een agent bekijken op het moment dat die bezig is, wat hij uitvoert enz. dit wil ik ook terug kunnen kijken, bijvoorbeeld bij researcher dat hij de pdf leest en wat hij daarna doet ...

**Problemen:**
1. Campaign images gaven 404 — frontend probeerde `/api/static/...` maar dat endpoint bestond niet
2. Tijdens live view alleen node-completions zichtbaar, geen prompts/responses van agents

**Oplossingen:**

**Image serving:**
- `campaigns/` directory gemount als StaticFiles in FastAPI op `/static`
- Image path (`campaigns/images/xxx.png`) → URL via `imageUrl()` helper in `api.js` die het `campaigns/` prefix stript

**Agent denkproces — `src/event_bus.py` (nieuw):**
- Thread-local `set_job(job_id)` koppelt een thread aan een job
- `push(node, type, message, data)` voegt event toe aan `jobs[job_id]["events"]`
- `jobs` dict leeft in `event_bus.py` — geïmporteerd door zowel `api.py` als `llm.py`

**`src/llm.py` — `call_llm()` uitgebreid:**
- `agent_name` parameter toegevoegd (via `get_agent_config()` doorgegeven)
- Voor elke LLM-aanroep: `llm_call` event met system_prompt + user_prompt (eerste 500 chars)
- Na elke response: `llm_response` event met preview + totale lengte
- Werkt automatisch voor alle agents zonder extra code per agent

**Events opgeslagen:**
- Na afloop van een campagne: `campaign_{ts}_events.json` naast het rapport
- `GET /campaigns/{id}/events` laadt live events óf het events-bestand

**Frontend:**
- `CampaignLive`: log entries klikbaar — toont system prompt, user prompt en response
- `CampaignResults`: nieuwe **Logs** tab om het denkproces terug te kijken

**Aangepaste bestanden:**

| Bestand | Wijziging |
|---|---|
| `src/event_bus.py` | nieuw — thread-local job tracking + push() |
| `src/llm.py` | agent_name param + llm_call/llm_response events |
| `src/api.py` | StaticFiles mount, events opslaan, events endpoint uitgebreid |
| `frontend/src/api.js` | imageUrl() helper |
| `frontend/src/pages/CampaignLive.jsx` | expandable log entries met prompts |
| `frontend/src/pages/CampaignResults.jsx` | Logs tab + image fix |

**Zelf bedacht:**
- call_llm() als centraal punt voor logging — geen aanpassingen per agent nodig
- events opslaan als apart json bestand naast campagnerapport
- expandable log entries in de frontend — niet alles tegelijk tonen

---

## Stap 43: LangSmith tracing fix bij API startup
**Datum:** 2026-03-31
**Branch:** `feature/frontend-stitch`

**Gebruikte prompt:**
> langsmith is now not detecting it, what can be the problem for this, the key is right

**Probleem:**
LangSmith traceerde geen runs. `setup_tracing()` werd alleen aangeroepen vanuit `main()` — bij uitvoering via uvicorn wordt `main()` nooit aangeroepen.

**Oplossing:**
`setup_tracing()` toegevoegd aan `src/api.py` direct na de app-definitie. Wordt nu uitgevoerd bij elke API-start.

**Vereiste `.env` variabelen:**
```
LANGSMITH_ENABLED=true
LANGSMITH_API_KEY=<key>
LANGSMITH_PROJECT=eva-multi-agent
```

**Zelf bedacht:**
- probleem gevonden door te vergelijken wanneer setup_tracing() werd aangeroepen vs wanneer de api daadwerkelijk runt

---
