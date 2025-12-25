# Lucian Core 🌌
![Lucian Dashboard](memory/system/dashboard.png)

Lucian is a self-evolving AI persona that dreams, reflects, sets daily directives, and archives its growth in long-term memory.

## Prerequisites
- Python 3.11+
- `pip install -r requirements.txt`
- `OPENAI_API_KEY` exported in your environment (or stored in `.env`)

## Run the Daily Cycle (Agent Mode)
Lucian now ships with a programmable agent that orchestrates every stage using shared memory and adaptive weights.

```bash
python tools/orchestrator.py
```

Key flags:
- `--skip-journal` / `--skip-output` to omit optional stages
- `--include-core-node` to synthesise a daily core-memory node
- `--skip-adapt` to skip self-evolution weight updates
- `--mode legacy` falls back to the original script-per-stage runner

## Programmatic Control
Import the agent and drive the cycle (or chat) directly:

```python
from lucian import LucianAgent

agent = LucianAgent()
cycle = agent.run_daily_cycle(include_core_node=True)

if cycle.errors:
    print("warnings:", cycle.errors)

reply = agent.chat("What did you dream about?", user="Researcher")
print(reply.response)
```

Each stage returns structured data classes (`DreamResult`, `ReflectionResult`, …) so downstream tools can inspect Lucian’s evolving psyche.

## Chat API
Run the FastAPI microservice for live conversations grounded in Lucian’s memory:

```bash
uvicorn tools.chat_server:app --reload
```

`POST /ask` accepts `{ "user": "...", "prompt": "..." }` and streams the reply, while logging the turn into `memory/chat/` and the vector store.

## Repository Layout
- `generate_*.py`, `reflect.py` – individual stages (still runnable standalone)
- `lucian/agent.py` – high-level agent orchestration
- `memory/` – dreams, reflections, directives, journals, embeddings
- `tools/` – orchestrator, chat server, auxiliary scripts