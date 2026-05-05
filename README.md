# AEO Diagnostic

**Does AI recommend your product?**

AEO Diagnostic simulates how ChatGPT, Gemini, and Perplexity respond to real shopper queries — and tells you exactly where your product ranks vs competitors.

## What it does

1. Takes a product name, description, and a shopper query (e.g. *"best magnesium supplement for sleep"*)
2. Fetches real competitors from the web using **Serper API**
3. Simulates responses from 3 AI engines using **Groq API** (Llama 3.3 70b, Mixtral 8x7b, Llama 3.1 8b)
4. Scores your product on mention rate, average rank, visibility, and trust
5. Returns a full report card with competitor rankings and prioritized fixes

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| AI engine simulation | Groq API — Llama 3.3 70b, Mixtral 8x7b, Llama 3.1 8b |
| Competitor research | Serper API (Google Search) |
| Frontend | Vanilla HTML/CSS/JS (no build step) |
| Deployment | Render (backend) + Netlify (frontend) |

## APIs used

- **Groq API** — free, runs 3 different models to simulate GPT, Gemini, and Perplexity responses + scoring
- **Serper API** — free tier (2500 queries/month), fetches real competitor names from Google Search

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/aeo-diagnostic.git
cd aeo-diagnostic
```

### 2. Backend setup

```bash
cd backend
cp .env.example .env
# Add your API keys to .env
pip install -r requirements.txt
uvicorn main:app --reload
```

Your `.env` should look like:
```
GROQ_API_KEY=your_groq_api_key_here
SERPER_API_KEY=your_serper_api_key_here
```

Get your keys:
- Groq: https://console.groq.com (free)
- Serper: https://serper.dev (free, 2500 queries/month)

### 3. Frontend setup

Open `frontend/index.html` in your browser. For local development, the frontend automatically points to `http://localhost:8000`.

For production, update this line in `index.html`:
```js
: 'https://your-backend-url.onrender.com'
```


## Project structure

```
aeo-diagnostic/
├── backend/
│   ├── main.py        # FastAPI app, /diagnose endpoint
│   ├── engines.py     # Groq API calls, 3-engine simulation
│   ├── search.py      # Serper API, competitor fetching
│   ├── scorer.py      # Scoring logic + report card generation
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── index.html     # Full UI, no build step required
└── README.md
```

## Architecture

```
User input
    │
    ▼
FastAPI /diagnose
    │
    ├── Serper API ──────────── fetch real competitors from Google
    │
    ├── Groq (Llama 3.3 70b) ── query 1: large capable model
    ├── Groq (Mixtral 8x7b) ─── query 2: mixture-of-experts model
    ├── Groq (Llama 3.1 8b) ─── query 3: smaller, faster model
    │         (all 3 run in parallel via asyncio.gather)
    │
    └── Groq (Llama 3.3 70b) ── analyze all 3 responses, generate report card
            │
            ▼
        Report card → Frontend
```
