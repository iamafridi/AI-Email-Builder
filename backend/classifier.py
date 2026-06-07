import json
import os
import re
import logging

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """You are an email triage AI. Analyze the email and return ONLY valid JSON with this exact schema:
{
  "important": true | false,
  "priority": "HIGH" | "MEDIUM" | "LOW",
  "category": "PAYMENT_ISSUE" | "CLIENT_COMPLAINT" | "SERVER_DOWN" | "URGENT_REQUEST" | "SUBSCRIPTION" | "SPAM" | "NEWSLETTER" | "OTHER",
  "reason": "one clear sentence explaining the decision"
}

Flag as important: client complaints, urgent customer requests, payment failures, billing issues, server/infrastructure alerts, security alerts, subscription emails.
Flag as NOT important: newsletters, marketing, social media notifications, spam."""


def _default_result():
    return {
        "important": False,
        "priority": "LOW",
        "category": "OTHER",
        "reason": "No classifier available — defaulting to not important.",
    }


def classify(email: dict) -> dict:
    text = f"Subject: {email['subject']}\nBody: {email['body']}"
    provider = _resolve_provider()
    logger.info("Using classifier provider: %s", provider)

    try:
        if provider == "claude":
            return _classify_claude(text)
        elif provider == "openai":
            return _classify_openai(text)
        elif provider == "gemini":
            return _classify_gemini(text)
        elif provider == "ollama":
            return _classify_ollama(text)
        else:
            return _classify_rules(email)
    except Exception as e:
        logger.error("Provider %s failed: %s — falling back to rules", provider, e)
        return _classify_rules(email)


def _resolve_provider() -> str:
    if os.getenv("ANTHROPIC_API_KEY"):
        return "claude"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    if os.getenv("OLLAMA_HOST", "http://localhost:11434"):
        try:
            import urllib.request
            urllib.request.urlopen(os.getenv("OLLAMA_HOST"), timeout=2)
            return "ollama"
        except Exception:
            pass
    return "rules"


def _parse_json_response(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()
    return json.loads(cleaned)


def _classify_claude(text: str) -> dict:
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system=CLASSIFICATION_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    return _parse_json_response(response.content[0].text)


def _classify_gemini(text: str) -> dict:
    from google import genai
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    response = client.models.generate_content(
        model=model,
        contents=f"{CLASSIFICATION_PROMPT}\n\n{text}",
    )
    return _parse_json_response(response.text)


def _classify_openai(text: str) -> dict:
    from openai import OpenAI
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        max_tokens=500,
        messages=[
            {"role": "system", "content": CLASSIFICATION_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    return _parse_json_response(response.choices[0].message.content)


def _classify_ollama(text: str) -> dict:
    import urllib.request
    import json as json_module

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    payload = json_module.dumps({
        "model": os.getenv("OLLAMA_MODEL", "llama3.2"),
        "system": CLASSIFICATION_PROMPT,
        "prompt": text,
        "stream": False,
    }).encode()
    req = urllib.request.Request(f"{host}/api/generate", data=payload, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=30)
    data = json_module.loads(resp.read())
    return _parse_json_response(data["response"])


def _classify_rules(email: dict) -> dict:
    text = f"{email['subject']} {email['body']}".lower()

    high_patterns = [
        (r"payment\s*fail|card.*declin|invoice\s*overdue|billing\s*error", "PAYMENT_ISSUE"),
        (r"disappointed|chargeback|data loss|complain|refund\s*request", "CLIENT_COMPLAINT"),
        (r"server\s*down|database\s*unreachable|cpu.*threshold|alert|outage|incident", "SERVER_DOWN"),
        (r"urgent|asap|critical|emergency|immediate", "URGENT_REQUEST"),
    ]

    medium_patterns = [
        (r"receipt|subscription|renewed|your.*statement", "SUBSCRIPTION"),
    ]

    low_patterns = [
        (r"unsubscribe|newsletter|weekly\s*digest|you won|prize|spam", "SPAM"),
    ]

    for pattern, category in high_patterns:
        if re.search(pattern, text):
            return {
                "important": True,
                "priority": "HIGH",
                "category": category,
                "reason": f"Matched keyword pattern '{pattern}' indicating {category}.",
            }

    for pattern, category in medium_patterns:
        if re.search(pattern, text):
            return {
                "important": True,
                "priority": "MEDIUM",
                "category": category,
                "reason": f"Matched keyword pattern '{pattern}' indicating {category}.",
            }

    for pattern, category in low_patterns:
        if re.search(pattern, text):
            return {
                "important": False,
                "priority": "LOW",
                "category": category,
                "reason": f"Matched keyword pattern '{pattern}' indicating {category}.",
            }

    return {
        "important": False,
        "priority": "LOW",
        "category": "OTHER",
        "reason": "No important keywords detected.",
    }
