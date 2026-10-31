"""Groq LLM client for conversational answers. Reads GROQ_API_KEY from env or .env file."""
import json
import os
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(HERE, ".env")
MODEL = "llama-3.1-70b-versatile"


def _load_key():
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key
    if os.path.exists(ENV_FILE):
        for line in open(ENV_FILE):
            line = line.strip()
            if line.startswith("GROQ_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def chat(question: str, context: dict) -> str:
    """Send shop context + owner question to Groq LLM, return answer string."""
    key = _load_key()
    if not key:
        return None  # caller falls back to keyword routing

    system_prompt = f"""You are Sahayak, a friendly AI assistant for a small Indian shop owner named Sunita who runs a kirana store.

Here is her shop data:
- {context.get('explanation', 'No trend data available')}
- Peak business hours: {context.get('peak_text', 'unknown')}
- Suggestion: {context.get('suggestion', 'none')}
- Owner's decision: {context.get('decision') or 'not decided yet'}
- Test result: {context.get('measure_text', 'no test run yet')}

Rules:
1. Answer in 1-3 short sentences. Be warm and friendly.
2. Use simple Hindi-English mix naturally (like "Bhaiya" or "accha").
3. Only talk about what the DATA shows. Never make up numbers.
4. If asked something not in the data, say you can only help with sales trends and suggestions.
5. If the owner hasn't approved yet, gently remind them.
6. Never use technical jargon. Talk like a helpful neighbor.
7. Always mention specific numbers from the data when relevant.
8. End with a short actionable suggestion or question when appropriate."""

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                "temperature": 0.7,
                "max_tokens": 200,
            },
            timeout=15,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[Groq error] {e}")
        return None  # fall back to keyword routing
