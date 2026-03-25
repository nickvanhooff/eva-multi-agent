# Stappenlog — Eva Multi-Agent System

Dit document beschrijft alle stappen die zijn genomen bij het opzetten van het multi-agent systeem.

---

## Stap 1: Project skeleton initialisatie
**Datum:** 2026-03-25

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

**Wat is er gedaan:**
- `src/agents/social_specialist.py` aangemaakt
- Maakt content voor Instagram (caption + hashtags), LinkedIn, en X/Twitter
- Gebruikt `copy_draft` als basis voor social content
- Verwerkt feedback alleen als `phase == "social_review"`

---

## Stap 10: Campaign Manager met conditionele routing
**Datum:** 2026-03-25

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
**Commit:** `2a8ae7f`

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
**Commit:** `cad09de` (GPU support), `9439006` (report saving)

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
**Commit:** `9439006`, volume mount gefixt in `docker-compose.yml`, later `835ff09`

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
**Commit:** `31dcbe7`

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
