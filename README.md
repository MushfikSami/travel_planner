# Travel Planner

> An AI-powered multi-agent travel itinerary generator that produces detailed 7-day travel plans tailored to your city, interests, and budget.

## Overview

Travel Planner leverages **CrewAI**'s multi-agent framework to automate the travel planning process. Instead of a single monolithic AI call, two specialized AI agents collaborate sequentially:

1. **Global Context Researcher** — Deep-dives into a destination using **Tavily Search** and **Wikipedia**, gathering historical context, current trends, and venue recommendations filtered by the user's budget tier.
2. **Travel Storyteller & Budget Analyst** — Transforms raw research into an engaging day-by-day Markdown itinerary with **exact cost estimates** (both USD and BDT) for every activity, meal, and transport.

All LLM inference is routed to a **local vLLM server** (`qwen36` model at `localhost:5000`), keeping inference costs near zero and data private.

## Architecture

```
┌─────────────┐     POST /plan_trip      ┌──────────────────┐
│  Streamlit  │ ──────────────────────►  │    FastAPI         │
│  Frontend   │                          │    Backend         │
│  (:8501)    │                          │    (:8000)         │
└─────────────┘                          └────────┬───────────┘
                                                  │
                                      ┌───────────▼────────────┐
                                      │     CrewAI Agents       │
                                      │                          │
                                      │  1. Researcher (Tavily   │
                                      │     + Wikipedia)         │
                                      │  2. Writer (Budget       │
                                      │     Analyst)             │
                                      └───────────┬────────────┘
                                                  │
                                      ┌───────────▼────────────┐
                                      │   Local vLLM Server     │
                                      │   (qwen36, :5000)       │
                                      └────────────────────────┘
```

## Features

- **Multi-agent collaboration** — Two CrewAI agents work sequentially: one researches, the other writes and budgets.
- **Budget-aware planning** — Three budget tiers ensure recommendations match spending capacity:
  - 🎒 **Backpacker** — Max ~$25 USD / 3,000 BDT per day
  - 🧳 **Standard** — ~$75 USD / 9,000 BDT per day
  - 🥂 **Luxury** — $250+ USD / 30,000+ BDT per day
- **Dual-currency pricing** — Every recommendation includes estimated costs in both USD and BDT.
- **7-day itineraries** — Full week plans with day-by-day breakdowns and "Daily Ledger" cost summary tables.
- **Rich research** — Combines real-time web search (Tavily) with encyclopedic knowledge (Wikipedia).
- **Local LLM** — Uses vLLM for local inference, avoiding API costs and ensuring data privacy.
- **Observability** — Prometheus metrics (`/metrics`) expose agent execution time and trip generation count.
- **Containerized** — Full Docker + docker-compose setup for effortless deployment.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Streamlit |
| **Backend API** | FastAPI + uvicorn |
| **Multi-Agent** | CrewAI |
| **LLM** | qwen36 via vLLM (`openai/qwen36`) |
| **Search** | Tavily Search API, Wikipedia (via LangChain) |
| **Observability** | Prometheus |
| **Packaging** | Docker + docker-compose |

## Prerequisites

- Python 3.12+
- [Docker](https://docs.docker.com/get-docker/) & [docker-compose](https://docs.docker.com/compose/install/)
- [vLLM](https://docs.vllm.ai/) running locally with the `qwen36` model served at `http://localhost:5000/v1`
- A [Tavily API key](https://app.tavily.com/) (free tier available)

## Quick Start (Docker)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/travel_planner.git
   cd travel_planner
   ```

2. **Configure API keys:**
   Edit `backend/.env` with your keys:
   ```env
   TAVILY_API_KEY=tvly-your-key-here
   OPENAI_API_KEY=no-key
   ```

3. **Start the stack:**
   ```bash
   docker-compose up --build
   ```

4. **Open the app:**
   - **Frontend:** http://localhost:8501
   - **Backend API:** http://localhost:8000
   - **Prometheus metrics:** http://localhost:8000/metrics

## Quick Start (Local / No Docker)

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set up `.env`:**
   ```bash
   cd backend
   # Edit .env with your TAVILY_API_KEY
   ```

3. **Start the backend:**
   ```bash
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

4. **Start the frontend:**
   ```bash
   cd frontend
   streamlit run app.py --server.port=8501
   ```

5. **Open:** http://localhost:8501

## Usage

1. Enter the **destination city** (e.g., `Dhaka`, `Paris`, `Kyoto`).
2. Enter your **interest** (e.g., `culture`, `food`, `nature`, `adventure`).
3. Select your **budget tier**.
4. Click **"Plan My Trip"** — your 7-day itinerary is generated in Markdown.

### API Reference

```
POST /plan_trip
Content-Type: application/json

{
  "city": "Dhaka",
  "interest": "history",
  "budget": "Backpacker (Max $25 USD per day)"
}

Response:
{
  "itenary": "## Day 1\nVisit Ahsan Manzil **[Cost: $1 / 120 BDT]**\n..."
}
```

## Project Structure

```
travel_planner/
├── backend/
│   ├── Dockerfile       # Backend Docker image
│   ├── crew.py          # CrewAI agents, tasks, and workflow
│   ├── main.py          # FastAPI application & API endpoint
│   ├── requirements.txt # Python dependencies
│   └── .env             # API keys (gitignored)
├── frontend/
│   ├── Dockerfile       # Frontend Docker image
│   └── app.py           # Streamlit UI
├── docker-compose.yml   # Orchestration (backend + frontend)
├── requirements.txt     # (shared reference)
└── README.md
```

## Observability

The backend exposes Prometheus metrics at `/metrics`:

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `agent_execution_time_seconds` | Histogram | Time taken for agent execution | `agent_role` |
| `trip_generation_count` | Counter | Total trips generated | — |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| 401 errors from vLLM | Ensure `base_url` in `crew.py` points to your running vLLM server and `api_key` matches |
| Agents hang mid-conversation | `allow_delegation=False` prevents CrewAI's delegation system from stalling the flow |
| Container can't reach host vLLM | `extra_hosts: ["host.docker.internal:host-gateway"]` in `docker-compose.yml` resolves the Docker networking gap on Linux |
| LLM returns incomplete itineraries | The `qwen36` model may need a higher `temperature` or `max_tokens` in your vLLM config |
