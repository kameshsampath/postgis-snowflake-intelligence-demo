# IDD Metrics — Streetlights Intelligence Demo

Pre-computed baseline values for the agent to use when answering user questions about
Intent-Driven Development metrics.  Values marked (~) are estimates; run `uv run idd-metrics`
for exact Cortex token counts.

---

## Formulas

| Metric | Formula | Directionality |
|--------|---------|----------------|
| **Infrastructure ICR** | `traditional_ops ÷ 1 invocation = traditional_ops` (one skill invocation per step) | Higher = more ops done per intent |
| **Query ICR score** | `int(trad_ops × 1000 ÷ NL_tokens)` | Higher = more ops per intent token (icr-lab formula) |
| **SQL/NL tok** | `SQL~est_tokens ÷ NL_tokens` | **Higher = better** — Cortex generated more SQL per intent token you typed |

### SQL/NL tok worked example

> Intent: "How many streetlights are faulty in Zone A?"
> NL tokens: 9 (tiktoken cl100k_base)
> SQL~est tokens: ~54 (observed Cortex Analyst output)
> SQL/NL = 54 ÷ 9 = **6.0×** — Cortex did 6× the token work you typed

---

## Column legend

```
  NL tok      tokens in your natural language intent (SNOWFLAKE.CORTEX.COUNT_TOKENS or tiktoken)
  Trad ops    traditional manual ops this intent replaces (SQL + bash + Python + API calls)
  SQL~est     estimated tokens in the SQL Cortex Analyst generates (~approximation)
  SQL/NL tok  output amplification — SQL tokens generated per NL intent token (higher = better)
              e.g. 9 NL tokens → 54 SQL tokens = 6.0×  (Cortex did 6× the token work you typed)
  ICR score   int(trad_ops × 1000 ÷ NL tokens) — ops per intent token, higher = better (icr-lab)
```

---

## Per-step Infrastructure ICR

Each step is invoked with one `$streetlights-demo step N` intent.
ICR = traditional_ops ÷ 1 invocation = traditional_ops (whole integer).

| Step | Title | Trad ops (baseline) | Step ICR |
|------|-------|---------------------|----------|
| 1 | Generate Data | 6 | 6 |
| 2 | PG Instance | 12 | 12 |
| 3 | Schema + Load | 10 | 10 |
| 4 | CLD | 8 | 8 |
| 5 | Semantic View | 8 | 8 |
| 6 | Cortex Search | 8 | 8 |
| 7 | Agent | 8 | 8 |
| 8 | ML Forecast | 10 | 10 |
| 9 | Deploy SiS | 7 | 7 |
| 10 | Validate | 6 | 6 |
| **Total / Avg** | | **83** | **8** |

*Avg = floor(83 ÷ 10) = 8.  "Traditional ops" counts SQL statements + bash commands + Python scripts + API calls + config files a developer would write manually.*

---

## Query ICR scores

NL token counts via tiktoken cl100k_base (run `uv run idd-metrics` for Cortex exact values).

| Intent | Routes to | NL tok | Trad ops | SQL~est | SQL/NL | ICR |
|--------|-----------|-------:|----------|--------:|-------:|----:|
| How many street lights are currently faulty? | Analyst | 8 | 5 | ~42 | 5.3 | 625 |
| Which neighborhoods have the highest energy consumption? | Analyst | 8 | 5 | ~58 | 7.3 | 625 |
| What is the average repair cost by maintenance type? | Analyst | 10 | 5 | ~54 | 5.4 | 500 |
| Show me the top 5 neighborhoods by maintenance frequency | Analyst | 10 | 4 | ~50 | 5.0 | 400 |
| Predict energy consumption for the next 30 days | Analyst (Forecast) | 9 | 5 | ~48 | 5.3 | 555 |
| Find maintenance reports about exposed wires or sparking | Search | 8 | 4 | ~38 | 4.8 | 500 |
| What does the maintenance history say about pole integrity? | Search | 10 | 3 | ~35 | 3.5 | 300 |
| Tell me about maintenance issues in the busiest neighborhood | Analyst+Search | 9 | 8 | ~85 | 9.4 | 888 |
| What's the repair status for flickering light reports? | Analyst+Search | 11 | 7 | ~78 | 7.1 | 636 |
| **Averages (floor)** | | **9** | **5** | **~54** | **5.9** | **558** |

*SQL/NL avg = total SQL tokens (488) ÷ total NL tokens (83) = 5.9.*
*ICR avg = floor(sum of ICR scores ÷ 9) = floor(5029 ÷ 9) = 558.*

---

## Combined IDD Picture

| Dimension | Intents expressed | Trad ops replaced | ICR |
|-----------|:-----------------:|:-----------------:|----:|
| Infrastructure (steps 1–10) | 10 | 83 | 8 avg per step |
| Query analytics (9 intents) | 9 | 46 | 558 avg (ICR-lab formula) |
| **Total** | **19** | **129** | — |
| **SQL output amplification** | — | — | **5.9× avg SQL/NL tok** |

---

## Q&A for the agent

**Q: Is a higher SQL/NL tok score better?**
A: Yes. A higher SQL/NL ratio means your intent was concise and Cortex Analyst did proportionally more SQL generation work. A score of 6.0 means you typed 1 token and got 6 tokens of SQL back — Cortex did 6× the token work you typed.

**Q: What is the average SQL leverage for this demo?**
A: 5.9× (total ~488 SQL tokens generated across 9 demo queries ÷ 83 NL intent tokens).

**Q: What is the average Query ICR score?**
A: 558 (floor average across 9 demo intents, using ICR-lab formula: int(trad_ops × 1000 ÷ NL_tokens)).

**Q: What is the average Infrastructure ICR?**
A: 8 (floor(83 traditional ops ÷ 10 steps); each step is one intent invocation).

**Q: How many traditional ops does this demo replace in total?**
A: 129 — 83 infrastructure ops (manual SQL/bash/Python/API work across 10 steps) + 46 query ops (what a developer would write manually for 9 analytics queries).

**Q: What is the ICR formula?**
A: Infrastructure ICR: `traditional_ops ÷ 1 invocation` (per step).
   Query ICR (icr-lab): `int(traditional_ops × 1000 ÷ NL_tokens)`.

**Q: Why does Query ICR use × 1000?**
A: To produce readable whole integers instead of tiny fractions. It is a scaled ratio — compare scores relative to each other, not as absolute percentages.
