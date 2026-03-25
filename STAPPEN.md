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
