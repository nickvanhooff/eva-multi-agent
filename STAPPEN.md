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
