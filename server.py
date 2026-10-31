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
from data_gen import SHOP_ID, START, generate
from explainer import explain
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
    state.update(conn=conn, finding=finding, action=action, decision=None, cap=action["budget_cap"])
    yield
    conn.close()


app = FastAPI(title="Sahayak", lifespan=lifespan)


@app.get("/demo", response_class=HTMLResponse)
def demo_page():
    html = os.path.join(HERE, "demo_page.html")
    if os.path.exists(html):
        return FileResponse(html, media_type="text/html")
    raise HTTPException(404, "demo_page.html not found")


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
    return {"decision": state["decision"], "cap": state["cap"], "explanation": explain(state["finding"])}


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
