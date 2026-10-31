"""Sahayak API: voice and text questions, and the owner's decision. Run with: uvicorn server:app"""
import base64
import datetime as dt
import os
import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

import planner
import sarvam
from answers import answer
from credit_score import compute_credit_signal
from data_gen import SHOP_ID, START, generate
from explainer import explain
from festivals import festive_comparison, upcoming_festival
from merchant_types import get_suggestion, list_categories, get_category_label
from trend import detect

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "sahayak.db")
AS_OF = START + dt.timedelta(days=41)
state = {}


@asynccontextmanager
async def lifespan(app):
    if not os.path.exists(DB):
        generate(DB)
    conn = sqlite3.connect(DB, check_same_thread=False)
    planner.init(conn)
    finding = detect(conn, SHOP_ID, AS_OF)
    action = planner.propose(conn, SHOP_ID, finding, AS_OF)
    state.update(conn=conn, finding=finding, action=action, decision=None, cap=action["budget_cap"],
                 category="kirana")  # default shop category
    yield
    conn.close()


app = FastAPI(title="Sahayak", lifespan=lifespan)


@app.get("/demo", response_class=HTMLResponse)
def demo_page():
    html = os.path.join(HERE, "demo_page.html")
    if os.path.exists(html):
        return FileResponse(html, media_type="text/html")
    raise HTTPException(404, "demo_page.html not found")


@app.get("/showcase", response_class=HTMLResponse)
def showcase_page():
    html = os.path.join(HERE, "showcase.html")
    if os.path.exists(html):
        return FileResponse(html, media_type="text/html")
    raise HTTPException(404, "showcase.html not found")


def _context():
    f = state["finding"]
    measure = None
    if state["decision"] == "approved":
        measure = planner.measure(state["conn"], SHOP_ID, state["action"]["id"])
        if isinstance(measure, str):
            measure = None
    suggestion = (f"Try a tea-and-snacks bundle offer on Thursdays for three weeks. "
                  f"Maximum budget ₹{state['cap']:,}.")
    return {
        "explanation": explain(f),
        "peak": f["peak_hours"],
        "suggestion": suggestion,
        "decision": state["decision"],
        "measure": measure,
        "note": "Sales only. Profit and actual spend are not measured in this prototype.",
    }


class Question(BaseModel):
    question: str


class Decision(BaseModel):
    decision: str  # approve | change | skip
    cap: int | None = None


@app.get("/api/status")
def status():
    f = state["finding"]
    measure = None
    if state["decision"] == "approved":
        m = planner.measure(state["conn"], SHOP_ID, state["action"]["id"])
        if not isinstance(m, str):
            measure = m
    weak_day = f["flagged"][0]["weekday"] if f.get("flagged") else "Thursday"
    suggestion = get_suggestion(state["category"], weak_day, state["cap"])
    return {
        "decision": state["decision"],
        "cap": state["cap"],
        "max_cap": planner.MAX_CAP,
        "explanation": explain(f),
        "peak_hours": f["peak_hours"],
        "suggestion": suggestion,
        "measure": measure,
        "weak_weekday": weak_day,
        "drop_pct": round(abs(f["flagged"][0]["change"]) * 100, 1) if f.get("flagged") else 0,
        "category": state["category"],
        "category_label": get_category_label(state["category"]),
    }


@app.post("/api/decision")
def decide(d: Decision):
    if d.decision == "change":
        if d.cap is None or d.cap < 100 or d.cap > planner.MAX_CAP:
            raise HTTPException(400, f"Budget must be between ₹100 and ₹{planner.MAX_CAP:,}.")
        state["cap"] = d.cap
        planner.decide(state["conn"], state["action"]["id"], "change", d.cap)
        state["decision"] = "approved"
    elif d.decision in ("approve", "skip"):
        planner.decide(state["conn"], state["action"]["id"], d.decision)
        state["decision"] = "approved" if d.decision == "approve" else "skipped"
    else:
        raise HTTPException(400, "decision must be approve, change or skip")
    return {"decision": state["decision"], "cap": state["cap"]}


@app.post("/api/ask-text")
def ask_text(q: Question):
    return {"answer": answer(q.question, _context())}


@app.post("/api/ask-voice")
async def ask_voice(audio: UploadFile = File(...)):
    """Audio in, transcript + answer + spoken answer (WAV, base64) out."""
    data = await audio.read()
    if not data:
        raise HTTPException(400, "No audio received.")
    try:
        transcript = sarvam.speech_to_text(data, audio.filename or "audio.wav")
        text = answer(transcript, _context())
        speech = sarvam.text_to_speech(text, "en-IN")
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    except Exception as e:
        raise HTTPException(502, f"Sarvam request failed: {e}")
    return {"transcript": transcript, "answer": text,
            "audio_wav_base64": base64.b64encode(speech).decode("ascii")}


# ---- Phase 2 APIs ----

class CategoryUpdate(BaseModel):
    category: str


@app.get("/api/categories")
def categories():
    """List all supported merchant categories."""
    return {"categories": list_categories(), "current": state["category"]}


@app.post("/api/category")
def set_category(c: CategoryUpdate):
    """Change the shop category — suggestion updates automatically."""
    state["category"] = c.category
    return {"category": c.category, "label": get_category_label(c.category)}


@app.get("/api/festival")
def festival():
    """Check for upcoming festivals and year-over-year comparison."""
    fest = festive_comparison(state["conn"], SHOP_ID, AS_OF)
    upcoming = upcoming_festival(AS_OF)
    return {"upcoming": upcoming, "comparison": fest}


@app.get("/api/credit-score")
def credit_score():
    """AI-generated credit signal from transaction patterns."""
    return compute_credit_signal(state["conn"], SHOP_ID, AS_OF)
