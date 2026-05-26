# 🛡️ Autonomous AI Security Monitoring Agent

An autonomous AI agent that continuously monitors websites for security issues,
reasons about findings with an LLM, decides what to do, and acts — all on a $0
free-tier stack.

> **Loop:** Observe → Analyze → Decide → Act → Save Memory → Repeat

## ✨ Features

- **Modular scanners**: HTTP reachability, TLS cert health, exposed `.git`, security headers
- **AI reasoning** (Gemini): turns raw findings into human-readable severity / risk / mitigation
- **Deterministic severity floor** — LLM cannot fabricate or escalate beyond rule-detected facts
- **Autonomous decisions**: notify on HIGH+, generate report on change/HIGH+, anchor hash on CRITICAL
- **Memory & diffing**: SQLite history per target, change detection between scans
- **Scheduler**: APScheduler runs the full agent loop every N minutes
- **Dashboard**: lightweight Jinja2 + HTMX UI, no SPA build step
- **Action stubs**: Telegram alerts + Solana devnet proof-of-report (toggleable)

## 🏗 Architecture (modular monolith)

```
app/
├── main.py              FastAPI app + lifecycle + routes
├── config.py            pydantic-settings
├── agents/core.py       Observe → Analyze → Decide → Act
├── tools/               Scanners (http, ssl, git, headers) + SSRF guard
├── ai/analyzer.py       Rules + Gemini, returns validated AnalysisResult
├── actions/             telegram.py · reports.py · alerts.py (decision engine)
├── blockchain/          solana_proof.py (devnet stub)
├── database/            SQLAlchemy models + session
├── scheduler/jobs.py    APScheduler
├── templates/ static/   Jinja2 + HTMX dashboard
```

## 🚀 Quick start (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # add GEMINI_API_KEY (optional — fallback is rules-only)
python -m app.seed         # add demo targets
uvicorn app.main:app --reload
```

Open <http://localhost:8000>.

Get a free Gemini key at <https://aistudio.google.com/apikey>.

## 🧪 Tests

```bash
pytest -q
```

## ☁️ Deploy to Railway (free)

1. Push repo to GitHub
2. New project → Deploy from GitHub → select repo
3. Add env vars from `.env.example` (`GEMINI_API_KEY` minimum)
4. Railway picks up `Dockerfile` + `railway.json` automatically

Demo URL: `https://<your-project>.up.railway.app`

## 🎬 Demo script (60 seconds)

1. Show dashboard with 3 seeded targets
2. Click **Scan now** on `expired.badssl.com` → wait ~5s
3. Click the row → scan detail page
   → shows `CRITICAL` badge, AI reasoning paragraph, mitigation steps, action log
4. Show `/scans/{id}/report` → markdown report with SHA256 hash line
5. Show terminal logs: `scheduler started: every 15 min` + `decision for ...`

## 🔐 Security considerations

- **SSRF**: `app/tools/_safety.py::normalize_url` blocks userinfo, non-http(s) schemes;
  `assert_public_host()` available for stricter prod use (resolves & blocks private IPs)
- **AI hallucination**: severity is rules-derived first; LLM only writes prose, bounded
  by Pydantic schema; LLM cannot raise severity above evidence
- **Prompt injection**: raw scan JSON is escaped & length-capped before insertion
- **Secrets**: only in `.env` / Railway secret manager, never committed
- **Timeouts**: every outbound request has a hard timeout; SSL check is sync but
  thread-offloaded so the event loop stays responsive

## 📋 Roadmap

- [ ] Implement Solana memo program send (`app/blockchain/solana_proof.py`)
- [ ] Subdomain discovery (crt.sh)
- [ ] Per-target custom check intervals
- [ ] Email digest reports
- [ ] Multi-user auth + RBAC

## 🪪 License

MIT
