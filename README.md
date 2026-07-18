# 🛠️ Multi-Tool Agent

[![Streamlit App](https://img.shields.io/badge/Streamlit-Live-FF4B4B?logo=streamlit&logoColor=white)](https://week-3-task-fbt3ndganj9pbmmaevfxnh.streamlit.app/)

A multi-tool AI agent powered by **OpenAI Agents SDK** + **Google Gemini 3.1 Flash Lite Preview** + **Tavily Search**, with a FastAPI backend and Streamlit frontend.

Built for **Week 3** of the AlgoHub AI Agents & Automation Internship.

## Features

| Tool | Description |
|------|-------------|
| 🌐 **Web Search** | Search the web for current information via Tavily |
| 🧮 **Calculator** | Safe math expression evaluation (AST-based, no eval) |
| 📄 **File Reader** | Read files from the project directory with line range |
| 🐍 **Code Executor** | Execute Python code in a sandboxed subprocess |

- **Tool chaining**: Agent can combine multiple tools to solve complex tasks
- **Streaming UI**: Watch reasoning steps unfold in real-time
- **SSE streaming**: Backend supports Server-Sent Events for live updates
- **Error handling**: Graceful recovery from tool failures

## Tech Stack

| Category | Choice |
|---|---|
| Agent Framework | [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) v0.18.3 |
| LLM | Google Gemini 3.1 Flash Lite Preview (via OpenAI-compatible endpoint) |
| Search | [Tavily Search API](https://tavily.com/) |
| Backend | FastAPI (async, SSE streaming) |
| Frontend | Streamlit |
| Python | 3.10+ |

## Project Structure

```
.
├── agent.py              # OpenAI Agents SDK agent setup
├── api.py                # FastAPI server (REST + SSE endpoints)
├── app.py                # Streamlit chat UI
├── config.py             # API key loading (env / secrets)
├── tools/
│   ├── __init__.py       # Tool exports
│   ├── web_search.py     # Tavily search tool
│   ├── calculator.py     # Safe math evaluator
│   ├── file_reader.py    # File reader tool
│   └── code_executor.py  # Sandboxed Python executor
├── pyproject.toml        # Dependencies
├── .env                  # API keys (not committed)
└── README.md
```

## Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- API keys for:
  - [Google AI Studio](https://aistudio.google.com/app/apikey) (Gemini)
  - [Tavily](https://tavily.com/) (Search)

## Setup

1. **Clone and enter the project:**
   ```bash
   cd week-3
   ```

2. **Set up API keys in `.env`:**
   ```env
   GEMINI_API_KEY=your-gemini-api-key
   TAVILY_API_KEY=your-tavily-api-key
   ```

3. **Install dependencies:**
   ```bash
   uv sync
   ```
   Or with pip:
   ```bash
   pip install -r requirements.txt
   ```

## Running

### Streamlit-only (recommended — works locally and on Streamlit Cloud):
```bash
uv run streamlit run app.py
```

The app will open at `http://localhost:8501`. The Streamlit frontend calls the agent directly — no separate backend needed.

### With FastAPI backend (optional — for API access):
```bash
# Terminal 1: Start the backend
uvicorn api:app --reload --port 8000

# Terminal 2: Start the frontend
streamlit run app.py
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/agent/run` | Run agent (request-response) |
| GET | `/agent/stream` | Run agent with SSE streaming |

### Example: POST /agent/run
```bash
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"query": "What is sqrt(144) + 10?"}'
```

### Example: GET /agent/stream
```bash
curl -N "http://localhost:8000/agent/stream?query=What%20is%2025*4"
```

## Example Queries

- **Calculator:** "What is 2^10 + 5*3?"
- **Web search:** "What's the latest Python version?"
- **File reader:** "Read the config.py file"
- **Code executor:** "Write Python code to print the first 10 Fibonacci numbers and run it"
- **Multi-tool:** "Search for the latest Python version and calculate 20% of the minor version number"

## Architecture

```
┌───────────────────┐     OpenAI Agents SDK     ┌──────────┐
│    Streamlit       │ ────────────────────────> │  Gemini   │
│    (app.py)        │ <──────────────────────── │  3.1 Flash Lite Preview │
└────────┬──────────┘                            └──────────┘
         │
    ┌────┼────┐────────┐────────┐
    ▼    ▼    ▼        ▼        ▼
 Tavily  Safe  File   Sandboxed
 Search  Math  Reader  Python
          Eval          Executor
```

**Local development:** The Streamlit app calls the agent directly (no FastAPI needed).
**Alternative:** Run `api.py` separately if you need REST/SSE API endpoints.

## Streamlit Cloud Deployment

1. **Push this folder to a GitHub repository.**

2. **Go to [share.streamlit.io](https://share.streamlit.io) and deploy:**
   - Repository: your repo path
   - Branch: `main` (or your branch)
   - Main file path: `week-3/app.py`

3. **Set secrets in the Streamlit Cloud dashboard:**
   Navigate to **Settings → Secrets** and add:
   ```toml
   GEMINI_API_KEY = "your-gemini-api-key"
   TAVILY_API_KEY = "your-tavily-api-key"
   ```

4. **Deploy!** Streamlit Cloud auto-detects `requirements.txt` and installs dependencies.

> **Note:** The app runs entirely within Streamlit — no FastAPI backend is needed on Streamlit Cloud. All agent execution happens in-process.
>
> See `.streamlit/secrets.toml.example` for a template.

```
┌─────────────┐     HTTP/SSE     ┌──────────────┐     OpenAI SDK     ┌──────────┐
│  Streamlit   │ ──────────────> │   FastAPI    │ ────────────────> │  Gemini  │
│  (app.py)   │ <────────────── │   (api.py)   │ <──────────────── │  3.1 Flash Lite Preview │
└─────────────┘                 └──────┬───────┘                   └──────────┘
                                       │
                              ┌────────┼────────┐────────┐
                              ▼        ▼        ▼        ▼
                         Tavily    Safe     File    Sandboxed
                         Search    Math     Reader  Python
                                   Eval             Executor
```

The OpenAI Agents SDK uses Gemini 3.1 Flash Lite Preview via its OpenAI-compatible endpoint (`generativelanguage.googleapis.com/v1beta/openai/`). The agent runs a think-act-observe loop, deciding which tool to call based on the user's request. Tracing is disabled since we use Gemini, not OpenAI.
