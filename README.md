# 🛒 Sahayak — Merchant Growth AI

> **Paytm AI Innovation Challenge 2026 · Track 1 · Finale Entry**

Sahayak is an AI copilot for India's 10M+ small shop owners using Paytm Soundbox. It watches payment trends, explains what the data shows in plain language, suggests one small capped experiment, waits for the owner's approval, and measures the result — all through voice in Hindi and English.

**No dashboards. No jargon. Just a soundbox that talks.**

---

## 🎯 Problem

Small merchants collect ₹500–₹5,000/day digitally. They see totals on a screen — but never spot a slow Thursday, a peak hour, or a trend that's costing them money. Existing analytics tools are built for large businesses with analysts on staff.

## 💡 Solution

Sahayak turns the Paytm Soundbox into a growth advisor:

| Step | What happens | Owner involvement |
|------|-------------|-------------------|
| **1. Notice** | Detects Thursday sales dropped 15% over 3 weeks | None — automatic |
| **2. Explain** | "Thursday collections are down compared to other days" | Listens via soundbox |
| **3. Suggest** | "Try a tea-and-snacks bundle, max ₹1,000 budget" | Hears the suggestion |
| **4. Decide** | Owner says "haan" (approve) or "nahi" (skip) | **Voice approval required** |
| **5. Measure** | After 3 weeks: "Thursday sales up 12% — the test worked" | Hears the result |

**Nothing happens without the owner's voice approval. Budget is always capped.**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   SAHAYAK SYSTEM                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐    ┌───────────┐    ┌──────────────┐  │
│  │ Soundbox  │◄──►│  Sarvam   │◄──►│   Sahayak    │  │
│  │ (Voice)   │    │  AI API   │    │   Engine     │  │
│  │           │    │           │    │              │  │
│  │ Owner     │    │ STT: Hindi│    │ trend.py     │  │
│  │ speaks /  │    │ & English │    │ explainer.py │  │
│  │ listens   │    │           │    │ planner.py   │  │
│  │           │    │ TTS: Reply│    │ answers.py   │  │
│  └──────────┘    └───────────┘    └──────┬───────┘  │
│                                          │          │
│                                   ┌──────▼───────┐  │
│                                   │  Paytm Data  │  │
│                                   │  (SQLite DB) │  │
│                                   │              │  │
│                                   │ Transactions │  │
│                                   │ by weekday,  │  │
│                                   │ hour, amount │  │
│                                   └──────────────┘  │
└─────────────────────────────────────────────────────┘
```

## 🔄 Agent Workflow

```
    ┌─────────────────┐
    │  Transaction DB  │
    │  (daily ingest)  │
    └────────┬────────┘
             ▼
    ┌─────────────────┐
    │   TREND DETECT   │  Compare last 3 weeks vs prior 3 weeks
    │   (trend.py)     │  Flag if weekday drops ≥ 10% & ≥ 2/3 weeks lower
    └────────┬────────┘  Check "others stable" (≤ 8% change)
             ▼
    ┌─────────────────┐
    │    EXPLAIN       │  Generate plain-language explanation
    │  (explainer.py)  │  "Thursday sales down 15%..."
    └────────┬────────┘  Include peak hours, comparison data
             ▼
    ┌─────────────────┐
    │    PROPOSE       │  Suggest action with capped budget
    │  (planner.py)    │  "Tea-and-snacks bundle, max ₹1,000"
    └────────┬────────┘
             ▼
    ┌─────────────────┐
    │  OWNER DECISION  │  ◄── Voice: "haan" / "nahi" / "change to 500"
    │   (server.py)    │  Nothing executes without approval
    └────────┬────────┘
             ▼
    ┌─────────────────┐
    │    MEASURE       │  After test period:
    │  (planner.py)    │  Compare test weeks vs baseline
    └────────┬────────┘  Report: "sales up 12%" or "no change"
             ▼
    ┌─────────────────┐
    │   VOICE Q&A      │  Owner can ask anytime:
    │  (answers.py)    │  "Why are Thursday sales down?"
    │  (sarvam.py)     │  "When is my busiest time?"
    └─────────────────┘  "How did the test go?"
```

## 📁 Project Structure

```
sahayak/
├── server.py          # FastAPI server — all API endpoints
├── trend.py           # Weekday trend detector (statistical, no ML)
├── explainer.py       # Natural-language explanation generator
├── planner.py         # Action proposal → decision → measurement
├── answers.py         # Keyword-routing Q&A engine
├── sarvam.py          # Sarvam AI STT/TTS client
├── data_gen.py        # Synthetic transaction data generator
├── demo_page.html     # Single-file demo UI (SVG chart, voice, decisions)
├── main.py            # CLI end-to-end demo
├── start.bat          # One-click Windows launcher
├── .env               # API key (not committed)
└── .gitignore
```

## 🛠️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Backend** | Python 3, FastAPI | Lightweight, async-ready, auto-docs |
| **Database** | SQLite | Zero-config, single-file, perfect for edge deployment |
| **Voice AI** | Sarvam AI (STT: saaras:v4, TTS: bulbul:v4-flash) | Built for Indian languages, ₹0.49/min STT |
| **Frontend** | Vanilla HTML/JS, inline SVG | No build step, works on any browser |
| **Detection** | Statistical weekday comparison | Interpretable, no training data needed |
| **Deployment** | Single folder, one-click start | Shop owner or Paytm field agent can set up |

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/devanshudhoble/Sahayak-.git
cd Sahayak-

# 2. Add your Sarvam AI key
echo SARVAM_API_KEY=your_key_here > .env

# 3. Run
start.bat          # Windows — installs deps automatically
# OR
pip install fastapi uvicorn requests python-multipart
uvicorn server:app --host 127.0.0.1 --port 8000 --reload

# 4. Open demo
# http://127.0.0.1:8000/demo
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/demo` | GET | Interactive demo page |
| `/api/status` | GET | Current trend finding & decision state |
| `/api/decision` | POST | Owner approves/changes/skips suggestion |
| `/api/ask-text` | POST | Text question → text answer |
| `/api/ask-voice` | POST | Audio upload → transcript + answer + spoken reply |
| `/docs` | GET | Auto-generated Swagger UI |

## 🔑 Key Design Principles

1. **Owner is always in control** — Nothing executes without voice/click approval
2. **Budget is always capped** — Maximum spend is set before any test begins
3. **Explain before suggest** — Data first, then recommendation
4. **Measure everything** — Every suggestion is tracked and reported back
5. **Voice-first** — Designed for shop owners, not analysts

## 🎤 Sarvam AI Integration

- **Speech-to-Text:** `saaras:v4` — Supports Hindi, English, and code-mixed input
- **Text-to-Speech:** `bulbul:v4-flash` with `simran_en_customer` speaker
- **Fallback:** Browser Web Speech API when Sarvam key is not configured
- **Cost:** ₹0.49/min STT + ₹1/1000 chars TTS (₹100 free credit included)

---

**Built for the Paytm AI Innovation Challenge 2026 Finale**
