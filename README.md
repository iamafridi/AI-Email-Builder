# AI Email Agent

A real-time dashboard that reads incoming emails, classifies them by importance using AI (or rule-based fallback), and displays flagged notifications. Runs entirely via Docker Compose.

## Live Demo

> [ai-email-builder-production.up.railway.app](https://ai-email-builder-production.up.railway.app)

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Email      │     │  Backend          │     │  Frontend    │
│  Source     │────▶│  (FastAPI)        │────▶│  (React)     │
│  (Mock/     │     │                   │     │              │
│   IMAP)     │     │  ┌─ agent.py ───┐ │     │  Dashboard   │
└─────────────┘     │  │ poll loop    │ │     │  polls /api  │
                    │  │ classify()   │ │     │  every 10s   │
                    │  │ save()       │ │     └──────────────┘
                    │  └──────────────┘ │
                    │  ┌─ classifier ─┐ │
                    │  │ Claude /     │ │
                    │  │ OpenAI /     │ │
                    │  │ Ollama /     │ │
                    │  │ Rules        │ │
                    │  └──────────────┘ │
                    │  ┌─ SQLite ─────┐ │
                    │  │ notifications│ │
                    │  │ processed    │ │
                    │  └──────────────┘ │
                    └──────────────────┘
```

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

Open http://localhost:3000

No API keys required — the system runs with a rule-based classifier by default.

## How AI Classification Works

Each incoming email is passed to a classifier that returns a structured JSON object:

```json
{
  "important": true,
  "priority": "HIGH",
  "category": "PAYMENT_ISSUE",
  "reason": "Payment failure detected in email subject"
}
```

The classifier supports multiple providers, selected automatically by environment variable priority:

| Provider | Env Variable | Requirement |
|----------|-------------|-------------|
| Claude | `ANTHROPIC_API_KEY` | Paid Anthropic account |
| OpenAI-compatible | `OPENAI_API_KEY` + `OPENAI_BASE_URL` | Works with OpenAI, Groq, etc. |
| Gemini | `GEMINI_API_KEY` | Free tier via Google AI Studio |
| Ollama | `OLLAMA_HOST` (default: http://localhost:11434) | Local Ollama instance |
| Rule-based (fallback) | — | Always available, no deps needed |

### Rule-based fallback

If no API keys are set, the system uses keyword matching on subject and body. Patterns are grouped by category:

- **HIGH priority**: payment failures, client complaints, server alerts, urgent requests
- **LOW priority**: newsletters, spam, subscriptions, receipts
- Everything else is marked as not important

## How the Dashboard Works

The frontend polls two endpoints every 10 seconds:

- `GET /api/notifications` — returns all flagged emails (newest first)
- `GET /api/stats` — returns counts by priority

The backend agent polls the email source every 30 seconds (configurable via `POLL_INTERVAL_SECONDS`). Each email is checked against the `processed_emails` table for deduplication, classified, and if important, saved to the `notifications` table.

### Filters

- **Priority filter**: ALL / HIGH / MEDIUM / LOW
- **Category filter**: PAYMENT_ISSUE, CLIENT_COMPLAINT, SERVER_DOWN, URGENT_REQUEST, SUBSCRIPTION, SPAM, NEWSLETTER, OTHER

### Dismissal

Click the × button on any notification to dismiss it (calls `DELETE /api/notifications/{id}`).

## Mock Data

The dataset in `backend/mock_emails.json` contains 22 emails across all categories:

| Category | Count | Priority |
|----------|-------|----------|
| PAYMENT_ISSUE | 3 | HIGH |
| CLIENT_COMPLAINT | 3 | HIGH |
| SERVER_DOWN | 2 | HIGH |
| URGENT_REQUEST | 2 | MEDIUM |
| SUBSCRIPTION | 3 | LOW |
| SPAM / NEWSLETTER | 4 | LOW |
| OTHER | 5 | LOW |

Emails are delivered 2 at a time per poll cycle to simulate realistic arrival.

A matching `mock_emails.csv` file is also provided. To use CSV mode, set `EMAIL_MODE=csv` in `.env`.

To add more emails, append objects to the JSON array or rows to the CSV with the same schema:

```json
{
  "id": "mock_023",
  "sender": "example@domain.com",
  "subject": "Email subject",
  "body": "Email body text",
  "received_at": "2026-06-07T12:00:00Z"
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Claude API key for AI classification |
| `OPENAI_API_KEY` | — | OpenAI-compatible API key |
| `OPENAI_BASE_URL` | https://api.openai.com/v1 | Base URL for OpenAI-compatible API |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `GEMINI_MODEL` | gemini-2.0-flash | Gemini model name |
| `OLLAMA_HOST` | http://localhost:11434 | Ollama server URL |
| `EMAIL_MODE` | mock | Email source: `mock`, `csv`, or `imap` |
| `CSV_MOCK_FILE` | backend/mock_emails.csv | Path to CSV file (when `EMAIL_MODE=csv`) |
| `POLL_INTERVAL_SECONDS` | 30 | How often to poll for new emails |
| `IMAP_HOST` | imap.gmail.com | IMAP server hostname |
| `IMAP_PORT` | 993 | IMAP server port |
| `IMAP_USER` | — | IMAP username |
| `IMAP_PASSWORD` | — | IMAP password |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/health | Health check |
| GET | /api/notifications | List all notifications |
| GET | /api/notifications/{id} | Get single notification |
| DELETE | /api/notifications/{id} | Dismiss notification |
| DELETE | /api/notifications | Clear all notifications |
| GET | /api/stats | Priority counts + last polled |
| POST | /api/poll | Trigger immediate poll |

## Limitations

- **Mock mode only** is tested by default. IMAP mode requires a valid app password and has only been lightly tested.
- **No authentication** on the dashboard — all endpoints are open. Not recommended for production deployment without adding auth.
- **IMAP polling** uses basic `imaplib` and does not handle all email encodings or attachments.
- **LLM providers** require network access to their respective APIs. The rule-based fallback works offline.
- **SQLite** is used for simplicity; a production deployment would benefit from PostgreSQL or similar.
