<div align="center">

# 🔎 Sodh Sahayak (शोध सहायक)
### An Autonomous, Self-Correcting Multi-Agent Deep Research System

*"Sodh Sahayak" (Hindi for "Research Assistant") turns a single natural-language question into a fully-cited, iteratively-refined research report — orchestrated by a supervisor agent, backed by parallel researcher sub-agents, and hardened by an adversarial self-critique loop.*

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-1c3c3c)
![LangChain](https://img.shields.io/badge/Framework-LangChain-1c3c3c)
![LLM](https://img.shields.io/badge/LLM-Groq%20%7C%20Mistral-orange)
![Search](https://img.shields.io/badge/Search-Tavily-8A2BE2)
![Interfaces](https://img.shields.io/badge/Interfaces-CLI%20%7C%20FastAPI%20%7C%20Streamlit-informational)

</div>

---

##  Overview

**Sodh Sahayak** is a production-minded implementation of the *"deep research agent"* pattern — the same category of system behind products like OpenAI's Deep Research or Perplexity's research mode — built entirely on **open, free-tier-friendly LLMs** (Groq and Mistral) and **LangGraph** as the agentic orchestration layer.

Rather than a single LLM call with a search tool bolted on, Sodh Sahayak treats research as an **iterative, adversarially-checked refinement process**, conceptually similar to a diffusion model: a rough, "noisy" draft report is generated first, and then repeatedly **denoised** — refined against real search evidence, critiqued by an adversarial Red Team agent, scored by an LLM judge, and distilled into a structured, source-attributed knowledge base — until the supervisor is satisfied or the iteration budget runs out.

The result is a system that:

- Clarifies ambiguous questions before spending any research budget
- Fans out research sub-tasks to parallel worker agents that browse the web (Tavily) and compress findings
- Runs a genuine **self-correction loop** (adversarial critique + quality scoring + fact/knowledge-base pruning)
- Produces a polished, cited **Markdown report**, not a raw chat transcript
- Ships with **three ready-to-use interfaces** (CLI, REST API, Streamlit web UI) and an **automated evaluation harness**

---

##  Architecture at a Glance

<img src="<img width="1024" height="1536" alt="architecture" src="https://github.com/user-attachments/assets/b94d8ed6-14a4-4eec-b28f-6fae604020b1" />


The system is organized as three nested LangGraph `StateGraph`s:

| Layer | Graph | Responsibility |
|---|---|---|
| **Outer** | `master_graph.py` (`deep_researcher_builder`) | End-to-end pipeline: scoping → supervised research → final report |
| **Middle** | `supervisor_graph.py` (`supervisor_builder`) | The orchestrator "brain" — plans research, delegates work, runs the self-correction loop, decides when to stop |
| **Inner** | `researcher_graph.py` (`agent_builder`) | A single ReAct-style worker: search → reflect → search again → compress findings into a cited summary |

### Full pipeline & data flow

<div align="center">
<img src="assets/pipeline-flow.png" alt="Detailed pipeline flow diagram" width="950"/>
</div>

---

## 🧠 How the Pipeline Works

### 1. Scoping (`scoping_nodes.py`, `scoping_graph.py`)
| Node | Purpose |
|---|---|
| `clarify_with_user` | A gatekeeper LLM call decides whether the user's request is specific enough to research. If not, it **halts the graph** and returns a clarifying question instead of guessing. |
| `write_research_brief` | Converts the (now-clarified) conversation into a single, detailed, first-person research brief. |
| `write_draft_report` | Generates an intentionally rough, **unresearched** initial draft — the "noisy" starting point that the rest of the system will refine. |

### 2. Supervised Research Loop (`supervisor_nodes.py`, `supervisor_graph.py`)
The **Supervisor** is the central orchestrator. On each turn it can call:

| Tool | Effect |
|---|---|
| `ConductResearch` | Delegates a self-contained research topic to a parallel `researcher_graph` sub-agent (fanned out via `asyncio.gather`) |
| `think_tool` | Forces a deliberate strategic-reflection pause before the next action |
| `refine_draft_report` | Synthesizes all findings + the confirmed knowledge base into an updated draft, then **immediately scores it** with an LLM judge (`evaluate_draft_quality`) |
| `ResearchComplete` | Signals the loop is done |

If the judge's average score drops below **7/10**, the supervisor is told to prioritize finding and citing new sources on its very next turn — a built-in quality gate, not just a suggestion.

### 3. Researcher Sub-Agent (`researcher_nodes.py`, `researcher_graph.py`)
A minimal ReAct loop per delegated topic: `llm_call → tool_node (Tavily search) → llm_call → … → compress_research`. Final output is a **compressed, citation-preserving summary** plus raw notes, returned to the supervisor as a tool result.

### 4. Self-Correction ("Diffusion") Loop (`self_correction_nodes.py`)
This is what elevates Sodh Sahayak beyond a typical search-augmented chatbot:

- 🛡️ **Red Team Critic** — an adversarial LLM whose only goal is to find unsupported claims, logical leaps, and missing viewpoints in the current draft. Genuine issues get surfaced back to the supervisor as `CRITICAL INTERVENTION REQUIRED` system messages.
- 📊 **Quality Evaluator** — an LLM-as-judge that scores comprehensiveness, accuracy/grounding, and coherence (0–10 each) with actionable, specific critique.
- ✂️ **Context Pruner** — extracts atomic, **structured facts** (`Fact{content, source_url, confidence_score, is_disputed}`) from raw research notes, appends them to a durable knowledge base, and clears the temporary notes buffer. This is deliberate **context engineering**: the supervisor's working memory stays clean and fact-grounded instead of accumulating raw scratch text turn after turn.

Both the Red Team and Context Pruner run **in parallel** after each research step and feed back into the next supervisor turn — closing the loop.

### 5. Final Report Generation (`final_report.py`)
Once the supervisor signals completion (or the iteration cap is hit), all curated findings, the confirmed knowledge base, and the final draft are synthesized into a polished, **cited Markdown report** — with a graceful degradation path: if the provider call fails repeatedly (e.g. an exhausted free-tier quota), the best available draft is returned with a clear note instead of crashing the run.

---

## ✨ Key Engineering Highlights

- **🎚️ Dual operating modes, tuned end-to-end** — `speed` mode (Groq, single researcher, no self-correction, ~15–20s) for demos, and `depth` mode (Mistral, parallel iterations, full Red Team + Judge + Pruner loop, ~60–90s) for genuinely thorough output. Every knob — concurrency, iteration caps, summarization char limits, writer token budgets — is re-tuned per mode in `config.py`.
- **🔌 Provider-agnostic model layer** — swap between Groq (`llama-3.3-70b-versatile`) and Mistral (`mistral-large`/`mistral-small`) via a single env var, with per-provider call throttling to respect free-tier rate limits.
- **♻️ Rate-limit-aware retry/backoff** — `utils.py` parses provider error strings (e.g. *"try again in 4.2s"*) to compute precise backoff windows, distinguishes retryable rate limits from unrecoverable quota exhaustion, and fails gracefully rather than looping forever.
- **🧩 Structured, typed state everywhere** — every graph node reads/writes strongly-typed `TypedDict`/Pydantic state (`AgentState`, `SupervisorState`, `ResearcherState`, `Fact`, `Critique`, `QualityMetric`), keeping a complex multi-agent system auditable and easy to extend.
- **🔐 Zero server-side key storage** — the FastAPI and Streamlit surfaces spawn an **isolated subprocess per request** (`worker.py`) with only that caller's API keys injected into its environment, so concurrent users' keys and quotas can never leak or collide.
- **📏 Built-in evaluation harness** (`evaluate.py`) — runs fixed benchmark questions across provider/mode combinations, scores reports with a fixed independent judge model, and computes **self-consistency** across repeated runs (mean/median/stdev) rather than trusting a single n=1 result.
- **🌐 Language-faithful by design** — every generation prompt explicitly instructs the model to respond in the same language as the user's original query.

---

## 📁 Project Structure

```text
sodh-sahayak/
├── main.py                    # CLI entry point
├── api.py                     # FastAPI service (per-request isolated subprocess)
├── worker.py                  # Subprocess entry point invoked by the API
├── streamlit_app.py           # Streamlit web UI
├── evaluate.py                # LLM-judged evaluation / benchmarking harness
│
├── master_graph.py            # Outer graph: scoping → supervisor → final report
├── scoping_graph.py           # Clarify → research brief → draft report
├── scoping_nodes.py
├── supervisor_graph.py        # Supervisor + tools + self-correction subgraph
├── supervisor_nodes.py
├── researcher_graph.py        # Per-topic ReAct researcher sub-agent
├── researcher_nodes.py
├── self_correction_nodes.py   # Red Team critic, Quality Evaluator, Context Pruner
├── final_report.py            # Final polished report synthesis
│
├── tools.py                   # ConductResearch, ResearchComplete, think_tool, tavily_search, refine_draft_report
├── search_utils.py            # Tavily search, dedup, webpage summarization
├── model_bindings.py          # Tool-bound model instances per provider
├── config.py                  # Speed/Depth mode tuning, model instantiation
├── schemas.py                 # Pydantic I/O schemas for structured LLM outputs
├── state.py                   # LangGraph state definitions (Fact, Critique, AgentState, ...)
├── prompts.py                 # All system/human prompt templates
├── utils.py                   # Retry/backoff, message helpers, date formatting
│
└── DEPLOYMENT.md               # Deployment guide (local, Streamlit Cloud, Render/Railway)
```

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| Agent orchestration | **LangGraph** (nested `StateGraph`s, `Command` routing, parallel fan-out via `asyncio.gather`) |
| LLM framework | **LangChain** (`init_chat_model`, structured output, tool binding) |
| LLM providers | **Groq** (`llama-3.3-70b-versatile`) · **Mistral** (`mistral-large-latest` / `mistral-small-latest`) |
| Web search | **Tavily Search API** |
| API service | **FastAPI** + Uvicorn |
| Web UI | **Streamlit** |
| Terminal UX | **Rich** (Markdown rendering in the CLI) |
| Validation | **Pydantic v2** |

---

## 🚀 Getting Started

### 1. Install dependencies

```bash
pip install langgraph langchain langchain-groq langchain-mistralai tavily-python \
            fastapi uvicorn streamlit rich python-dotenv pydantic
```

> A pinned `requirements.txt` is recommended for production use — see the [Deployment Guide](DEPLOYMENT.md) for provider-specific setup notes.

### 2. Get free API keys

| Key | Needed for | Get it at |
|---|---|---|
| `GROQ_API_KEY` | Speed mode | https://console.groq.com/keys |
| `MISTRAL_API_KEY` | Depth mode | https://console.mistral.ai/api-keys |
| `TAVILY_API_KEY` | Web search (always required) | https://app.tavily.com |

### 3. Run it

**CLI** (interactive, prompts for keys if not set):
```bash
python main.py
```

**Streamlit Web UI** (great for sharing with non-technical users — everyone brings their own keys):
```bash
streamlit run streamlit_app.py
```

**FastAPI service**:
```bash
uvicorn api:app --reload
```
```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{
        "query": "Compare TSMC and Intel chip strategy for 2026-2028",
        "llm_provider": "mistral",
        "mistral_api_key": "YOUR_OWN_KEY",
        "tavily_api_key": "YOUR_OWN_KEY"
      }'
```

---

## ⚙️ Configuration: Speed vs. Depth Mode

`RESEARCH_MODE` (auto-selected from `LLM_PROVIDER` if unset) controls a full set of tuned parameters:

| Parameter | `speed` (Groq) | `depth` (Mistral) |
|---|---|---|
| Concurrent researchers | 1 | 1 |
| Max researcher iterations | 2 | 2 |
| Tavily results per query | 1 | 2 |
| Summarization input chars | 1,500 | 3,500 |
| Final writer token budget | 1,500 | 2,000 |
| Red Team adversarial critique | ❌ off | ✅ on |
| Context Pruner (fact extraction) | ❌ off | ✅ on |
| Target latency | ~15–20s | ~60–90s |

Both providers also get a small **pre-call pace limiter** (`LLM_CALL_THROTTLE_SECONDS`, `SUMMARIZE_THROTTLE_SECONDS`) tuned to their respective free-tier per-second limits.

---

## 📊 Evaluation Harness

`evaluate.py` benchmarks report quality *independently* of the model producing it:

- Runs a fixed set of research questions against one or more provider/mode configurations
- Grades each resulting report with a **fixed, separate judge model** across `comprehensiveness`, `accuracy`, and `coherence`
- Supports `REPEATS_PER_QUESTION > 1` to measure **run-to-run self-consistency** (mean, median, standard deviation) rather than trusting a single sample
- Exports results to CSV for downstream comparison

```bash
python evaluate.py
```

---

## 🔒 Deployment & Security Model

Full details live in [`DEPLOYMENT.md`](DEPLOYMENT.md). The short version:

- Each API/Streamlit request spawns a **fresh, isolated subprocess** (`worker.py`) with only that caller's keys injected as environment variables.
- **No API keys are ever stored server-side** — hosted deployments (Streamlit Community Cloud, Render/Railway) require zero platform secrets, since every caller supplies their own free-tier keys at request time.
- One user's rate limit or quota exhaustion cannot affect another concurrent user's run.

---

## 🧭 Design Philosophy

Sodh Sahayak is deliberately built around a few core beliefs about agentic research systems:

1. **Don't research an ambiguous question.** Clarify first — wasted research budget is worse than one extra turn.
2. **A first draft is meant to be wrong.** Generate a rough draft immediately, then spend the iteration budget *refining* it against real evidence — analogous to denoising in diffusion models — rather than trying to get everything right in one shot.
3. **Self-critique should be adversarial, not cooperative.** The Red Team's only job is to find flaws — it is explicitly instructed *not* to be helpful.
4. **Context is an engineering problem.** Raw research notes are noisy and should not accumulate forever in a supervisor's context window; the Context Pruner exists specifically to compress them into durable, confidence-scored, source-attributed facts.
5. **Free-tier LLMs are production-viable** if you respect their rate limits explicitly, rather than hoping you won't hit them.

---

## 🗒️ License

This project is provided as-is for research and educational purposes. Add your preferred license (MIT/Apache-2.0/etc.) here.
