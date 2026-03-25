# LangSmith Setup — Eva Multi-Agent System

Dit document beschrijft hoe je LangSmith instelt voor debugging, monitoring en evaluatie van het Eva multi-agent systeem.

**LangSmith** is het debugging- en monitoring-platform van LangChain. Het geeft real-time zichtbaarheid in alle LLM calls, agent stappen, en state transitions.

---

## Wat doet LangSmith?

| Functie | Voordeel |
|---------|----------|
| **Real-time tracing** | Zie elke agent-stap, LLM call en state transition live |
| **Performance monitoring** | Latency, token usage, kosten per agent |
| **Debugging** | Inspecteer output van elke agent en identificeer bottlenecks |
| **Evaluatie** | Vergelijk runs, track iteraties, meet kwaliteit |
| **Cost tracking** | Hoeveel tokens/geld per run |

---

## Stap 1: LangSmith Account aanmaken

1. Ga naar **https://smith.langchain.com**
2. Klik "Sign up" (gratis account beschikbaar)
3. Volg de registratie-stappen
4. Bevestig je email

---

## Stap 2: API Key ophalen

1. Log in op https://smith.langchain.com
2. Klik rechtsboven op je profiel → **"Settings"**
3. Scroll naar **"API Keys"**
4. Klik **"Create API Key"**
5. Kopieer de gegenereerde key (volledige key, niet alleen het begin)
6. Bewaar deze ergens veilig (of in je `.env` bestand, zie stap 3)

---

## Stap 3: Configuratie in `.env`

Voeg deze variabelen toe aan je `.env` bestand:

```env
# LangSmith Configuration
LANGSMITH_ENABLED=true
LANGSMITH_API_KEY=ls_your_actual_api_key_here
LANGSMITH_PROJECT=eva-multi-agent
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

### Wat betekent elke variabele?

| Variabele | Betekenis | Voorbeeld |
|-----------|-----------|-----------|
| `LANGSMITH_ENABLED` | Tracing aan/uit | `true` of `false` |
| `LANGSMITH_API_KEY` | Je API key van Smith | `ls_xxx...` |
| `LANGSMITH_PROJECT` | Naam van je project in Smith | `eva-multi-agent`, `test-run`, etc. |
| `LANGSMITH_ENDPOINT` | Smith API URL (meestal default) | `https://api.smith.langchain.com` |

---

## Stap 4: Dependencies installeren

```bash
pip install -r requirements.txt
```

Dit installeert `langsmith>=0.1.0` (toegevoegd in requirements.txt).

---

## Stap 5: Campaign uitvoeren met tracing

Voer de campaign uit als normaal:

```bash
# Lokaal:
python src/main.py

# Of in Docker:
docker compose up
```

Bij startup zie je:

```
[TRACING] LangSmith enabled for project: eva-multi-agent
[TRACING] Dashboard: https://smith.langchain.com/
[TRACING] All agent steps, LLM calls, and state transitions will be traced.
```

---

## Stap 6: Resultaten bekijken in LangSmith

1. Open **https://smith.langchain.com**
2. Ga naar je project (bijv. "eva-multi-agent")
3. Je ziet een lijst met runs
4. Klik op een run om de volledige trace te zien

### Wat zie je in een run trace?

**Top level:** de hele campaign van START tot END

```
Campaign Generation
├── Researcher
├── Strateeg
├── Copywriter
├── Social Specialist
└── Campaign Manager
```

**Per agent:**
- Inputs (wat de agent leest uit state)
- Outputs (wat de agent teruggeeft)
- LLM call details (model, tokens, latency, kosten)
- System prompt en user prompt

---

## Voorbeeld: Analyzing a Trace

Stel je hebt een run gedaan en wilt weten waarom de Campaign Manager feedback gaf. In Smith kun je:

1. Klik op de Campaign Manager node in de trace tree
2. Zie de exacte input (alle state velden)
3. Zie de exacte output (BESLISSING, FASE, FEEDBACK)
4. Zie de LLM response in volle lengte
5. Identificeer waar het mis ging

---

## Debugging Use Cases

### 1. Agent produceert slecht output

**In Smith:**
- Bekijk de exakte input die de agent ontving
- Controleer of alle vorige agents correct hebben uitgevoerd
- Lees de volledige LLM response (niet alleen de samenvatting)
- Check tokens/latency (was het model overbelast?)

### 2. Feedback loop werkt niet goed

**In Smith:**
- Vergelijk twee runs: één zonder feedback, één met feedback
- Zie exact wat de Campaign Manager feedback gaf
- Zie hoe de Copywriter die feedback verwerkte

### 3. State veld ontbreekt

**In Smith:**
- Trace door elke agent stap-voor-stap
- Zie welke fields geschreven werden door welke agent
- Identificeer welke agent het veld vergat te schrijven

---

## Performance Monitoring

LangSmith toont per run:

- **Total latency:** Totale tijd van START tot END
- **Per-agent latency:** Hoe lang elke agent draait
- **Token usage:** Hoeveel input/output tokens per LLM call
- **Costs:** Euro/dollar waarde van de tokens (afhankelijk van model)

### Voorbeeld metrics:

```
Researcher: 2.3s, 180 input tokens, 245 output tokens
Strateeg: 1.9s, 420 input tokens, 380 output tokens
Copywriter: 3.1s, 580 input tokens, 650 output tokens
Social Specialist: 2.7s, 620 input tokens, 720 output tokens
Campaign Manager: 1.8s, 2100 input tokens, 450 output tokens
────────────────────────────────────────────────────────
Total: 11.8s, 3900 input tokens, 2445 output tokens
```

---

## Privacy & Security

- **API Key:** Je API key geeft Smith alleen lees-/schrijftoegang op jouw account. Deleting API key is instant.
- **Data:** Prompts en responses worden versleuteld (TLS) naar Smith's servers gestuurd.
- **Offline:** Wil je tracing uitschakelen? Zet `LANGSMITH_ENABLED=false` in `.env`.

---

## Troubleshooting

### "LANGSMITH_ENABLED=true but LANGSMITH_API_KEY not set"

**Oorzaak:** Je hebt `LANGSMITH_ENABLED=true` gezet, maar geen `LANGSMITH_API_KEY` ingevuld.

**Oplossing:**
```env
LANGSMITH_ENABLED=true
LANGSMITH_API_KEY=ls_your_key_here  # Voeg dit toe!
```

### "401 Unauthorized" in de logs

**Oorzaak:** Je API key is ongeldig of verlopen.

**Oplossing:**
1. Ga naar https://smith.langchain.com → Settings → API Keys
2. Genereer een nieuwe key
3. Update `.env`

### "Nothing appears in Smith dashboard"

**Mogelijke oorzaken:**
- `LANGSMITH_ENABLED=false` in `.env` (check!)
- API key niet ingevuld
- Campaign draaide maar Smith tab was niet open (refresh de pagina)

**Oplossing:**
1. Check: `LANGSMITH_ENABLED=true`
2. Check: `LANGSMITH_API_KEY` ingevuld
3. Voer campaign opnieuw uit
4. Refresh Smith dashboard

---

## Integratie met portfolio

Wanneer je een **Decision Log** schrijft over agent-verbetering:

1. Voer de campaign uit met `LANGSMITH_ENABLED=true`
2. Screenshot de trace in Smith
3. Link naar de Smith run in je decision log: https://smith.langchain.com/o/{org}/projects/{project}/runs/{run_id}

Voorbeeld in DL4+:

> Voor evaluatie van dit experiment raadpleeg je deze LangSmith trace:
> 📊 [Trace: Eva Campaign Run #15](https://smith.langchain.com/...)
> Dit toont: agent latencies, token usage, en de feedback loop in werking.

---

## Optioneel: Project in Smith aanpassen

In de Smith dashboard kun je:

- Project naam wijzigen
- Beschrijving toevoegen
- Tags per run toevoegen (bijv. "test", "production", "feedback-loop")
- Runs evalueren (goed/slecht)
- Datasets aanmaken voor benchmarking

---

## Stap voor stap: Eerste keer

**Dit is hoe je voor het eerst LangSmith opzet:**

1. Ga naar https://smith.langchain.com → Sign up → Bevestig email
2. Klik Settings → API Keys → Create API Key
3. Kopieer de key
4. Voeg toe aan `.env`:
   ```env
   LANGSMITH_ENABLED=true
   LANGSMITH_API_KEY=ls_...
   LANGSMITH_PROJECT=eva-multi-agent
   ```
5. Run: `pip install -r requirements.txt` (voegt langsmith toe)
6. Run: `python src/main.py`
7. Kijk in Smith dashboard → zie je project "eva-multi-agent" → zie je de campaign trace!

---

## Hulp nodig?

- LangSmith docs: https://docs.smith.langchain.com/
- LangGraph + LangSmith integratie: https://langchain-ai.github.io/langgraph/how-tos/debugging/
- LangSmith support: support@langchain.com
