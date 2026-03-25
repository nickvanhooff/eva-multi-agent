# Model Selectie per Agent — Eva Multi-Agent

Dit document beschrijft welk LLM model voor welke agent wordt gebruikt, waarom, en de bronnen.

---

## Overzicht

| Agent | Provider | Model | Tokens/dag |
|-------|----------|-------|-----------|
| Researcher | Groq | `llama-3.1-8b-instant` | 500.000 |
| Strateeg | Groq | `llama-3.1-8b-instant` | 500.000 |
| Copywriter | OpenRouter | `meta-llama/llama-3.3-70b-instruct:free` | Variabel |
| Social Specialist | OpenRouter | `meta-llama/llama-3.3-70b-instruct:free` | Variabel |
| Campaign Manager | Groq | `llama-3.3-70b-versatile` | 100.000 |

---

## Per agent — keuze en motivatie

### Researcher → `llama-3.1-8b-instant` (Groq)

**Waarom dit model:**
De Researcher doet feitelijk marktonderzoek op basis van de productbeschrijving. Dit vereist geen extreme creativiteit — het gaat om gestructureerde analyse en het ophalen van informatie uit de trainingsdata van het model. Een 8B model is hiervoor voldoende.

**Waarom Groq:**
Groq biedt de laagste latency voor LLM inference (SpeculativeDecoding hardware). Voor de Researcher, die als eerste in de pipeline staat, is snelheid belangrijk.

**Waarom niet 70B:**
De 70B models hebben een limiet van 100k tokens/dag op Groq. Door de Researcher op 8B te draaien, besparen we de 70B tokens voor de Campaign Manager waar kwaliteit kritischer is.

**Bron:**
- Groq model limieten: https://console.groq.com/settings/limits
- Llama 3.1 8B benchmark: https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct

---

### Strateeg → `llama-3.1-8b-instant` (Groq)

**Waarom dit model:**
De Strateeg bouwt voort op de output van de Researcher en maakt een marketingstrategie. De input is gestructureerd en het verwachte output-formaat ook (strategie, positionering, tone of voice). Een 8B model volgt dit patroon goed.

**Waarom Groq:**
Zelfde redenering als Researcher — snelheid en geen 70B tokens verspillen.

**Waarom niet OpenRouter:**
De Strateeg levert input aan de Copywriter. Kwaliteit van de strategie heeft directe invloed op de rest van de pipeline — Groq heeft stabielere inference dan de gratis OpenRouter tier.

**Bron:**
- Groq snelheid benchmark: https://artificialanalysis.ai/models/llama-3-1-instruct-8b/providers

---

### Copywriter → `meta-llama/llama-3.3-70b-instruct:free` (OpenRouter)

**Waarom dit model:**
De Copywriter schrijft creatieve marketingteksten — headline, bodytekst, call-to-action. Dit vereist het meeste taalgevoel en creativiteit. Een 70B model geeft merkbaar betere creatieve output dan een 8B model.

**Waarom OpenRouter:**
De Copywriter gebruikt de meeste tokens per run (lange output, hoge temperature=0.9). Door dit op OpenRouter te draaien i.p.v. Groq, wordt de Groq 100k/dag limiet gespaard voor de Campaign Manager.

**Waarom free model:**
`llama-3.3-70b-instruct:free` op OpenRouter is hetzelfde model als op Groq, maar via OpenRouter's gratis tier. Voor creatief schrijven is de iets hogere latency acceptabel.

**Bron:**
- OpenRouter free models: https://openrouter.ai/models?q=free
- Llama 3.3 70B release: https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct

---

### Social Specialist → `meta-llama/llama-3.3-70b-instruct:free` (OpenRouter)

**Waarom dit model:**
De Social Specialist maakt platform-specifieke content (Instagram, LinkedIn, X/Twitter). Elk platform heeft een eigen tone en format. Een 70B model begrijpt deze nuances beter dan een 8B model — met name voor LinkedIn (professioneel) vs Instagram (casual).

**Waarom OpenRouter:**
Zelfde redenering als Copywriter — hoge token output, gratis 70B model beschikbaar, Groq tokens sparen.

**Bron:**
- OpenRouter free models: https://openrouter.ai/models?q=free

---

### Campaign Manager → `llama-3.3-70b-versatile` (Groq)

**Waarom dit model:**
De Campaign Manager is het kritiekste punt in de pipeline. Hij beoordeelt alle output van alle andere agents, geeft gestructureerde feedback (BESLISSING/FASE/FEEDBACK), en bepaalt of de campagne goedgekeurd wordt of terug moet. Fouten hier kosten extra iteraties en dus extra tokens.

**Waarom 70B en niet 8B:**
De Campaign Manager leest de volledige state — alle output van alle agents. Dat is veel context. Een 70B model begrijpt deze context beter en geeft betrouwbaardere beoordelingen. In testen met 8B modellen werd de feedback minder specifiek en de BESLISSING minder consistent geparsed.

**Waarom Groq en niet OpenRouter:**
De Campaign Manager heeft de laagste temperature (0.3) — determinisme is belangrijk. Groq's inference is stabieler en sneller dan de gratis OpenRouter tier, wat de kans op parsing-fouten verkleint.

**Bron:**
- Groq model limieten: https://console.groq.com/settings/limits
- Llama 3.3 70B versatile: https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct

---

## Token gebruik schatting per run

| Agent | Gemiddeld tokens | Model |
|-------|-----------------|-------|
| Researcher | ~600 | 8B (Groq) |
| Strateeg | ~800 | 8B (Groq) |
| Copywriter | ~1200 | 70B (OpenRouter) |
| Social Specialist | ~1100 | 70B (OpenRouter) |
| Campaign Manager | ~2100 | 70B (Groq) |
| **Groq 70B verbruik** | **~2100/run** | — |
| **Groq 8B verbruik** | **~1400/run** | — |

Met 100k tokens/dag op Groq 70B: ~47 runs per dag.
Met 500k tokens/dag op Groq 8B: geen limiet probleem.
