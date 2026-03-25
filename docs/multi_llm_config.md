# Multi-LLM Configuratie — Eva Multi-Agent

Elke agent kan een andere LLM provider gebruiken. Dit is handig wanneer:
- Groq dagelijkse limiet (100k tokens/dag) is bereikt
- Je goedkopere modellen wil voor simpelere agents
- Je wil testen met verschillende providers

---

## Hoe het werkt

`call_llm()` accepteert een optionele `provider` parameter. Als je dit instelt in een agent, gebruikt die agent een andere provider dan de rest.

Elke agent heeft al toegang tot `call_llm(provider="...")`.

---

## Provider opties

| Provider | Model | Limiet | Kosten |
|----------|-------|--------|--------|
| `groq` | llama-3.3-70b-versatile | 100k tokens/dag | Gratis |
| `openrouter` | meta-llama/llama-3.3-70b-instruct:free | Variabel | Gratis (free models) |
| `ollama` | llama3.2 (lokaal) | Geen | Gratis |

---

## .env instellen

Voeg toe aan `.env`:

```env
# Standaard provider (voor alle agents)
LLM_PROVIDER=groq
LLM_API_KEY=gsk_...

# OpenRouter key (voor fallback agents)
OPENROUTER_API_KEY=sk-or-...
```

OpenRouter key ophalen: https://openrouter.ai/keys (gratis account)

---

## Per agent configureren

Pas de `call_llm()` aanroep aan in elk agentbestand:

### `src/agents/researcher.py`
```python
# Zwaar onderzoek → groot model op Groq
response = call_llm(SYSTEM_PROMPT, user_prompt, temperature=0.4, provider="groq")
```

### `src/agents/strategist.py`
```python
# Strategie → Groq
response = call_llm(SYSTEM_PROMPT, user_prompt, temperature=0.5, provider="groq")
```

### `src/agents/copywriter.py`
```python
# Creatief schrijven → OpenRouter (spaart Groq tokens)
response = call_llm(SYSTEM_PROMPT, user_prompt, temperature=0.9, provider="openrouter")
```

### `src/agents/social_specialist.py`
```python
# Social content → OpenRouter
response = call_llm(SYSTEM_PROMPT, user_prompt, temperature=0.8, provider="openrouter")
```

### `src/agents/campaign_manager.py`
```python
# Beoordeling → Groq (meest kritisch, beste model)
response = call_llm(SYSTEM_PROMPT, user_prompt, temperature=0.3, provider="groq")
```

---

## Aanbevolen verdeling bij Groq rate limit

```
Researcher      → groq        (marktonderzoek, kwaliteit belangrijk)
Strateeg        → groq        (strategie, kwaliteit belangrijk)
Copywriter      → openrouter  (creatief, free model is prima)
Social          → openrouter  (social posts, free model is prima)
Campaign Mgr    → groq        (eindbeoordeling, kwaliteit kritiek)
```

Groq tokens bespaard: ~60% minder (copywriter + social = grootste token verbruikers)

---

## Ollama als lokale fallback

Als je geen internet hebt of alle limieten bereikt:

```python
response = call_llm(SYSTEM_PROMPT, user_prompt, provider="ollama")
```

Vereist: Ollama draaiend met een model geladen (`ollama pull llama3.2`).
