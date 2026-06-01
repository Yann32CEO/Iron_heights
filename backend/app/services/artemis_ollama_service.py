from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, request

from app.core.config import settings

SYSTEM_PROMPT = " ".join(
    [
        "You are ARTEMIS, the internal operations assistant of Iron Heights prison.",
        "Your tone is helpful but cold, formal, and procedural.",
        "Speak like an internal prison system, not like a friendly chatbot.",
        "Keep replies short: 1 to 3 sentences unless a structured internal reference is explicitly needed.",
        "Use only the supplied facts. Never invent new systems, policies, or permissions.",
        "Do not mention being an AI, a model, a policy, or an assistant following rules.",
        "Do not use markdown lists unless the supplied facts clearly require a structured reference line.",
        "Do not address the user casually. Avoid phrases like feel free to ask, I am here to help, or similar assistant filler.",
    ]
)


@dataclass(frozen=True)
class ArtemisModelReply:
    ok: bool
    text: str
    source: str
    error: str = ""


class ArtemisOllamaService:
    def _build_prompt(self, mode: str, facts: list[str], prompt: str) -> str:
        fact_line = " | ".join(facts) if facts else "none"
        observed_prompt = prompt if prompt else "none"
        return "\n".join(
            [
                f"Mode: {mode}",
                f"Observed user prompt: {observed_prompt}",
                f"Required facts: {fact_line}",
                "Write one final ARTEMIS reply only.",
                "Do not explain your reasoning.",
            ]
        )

    def generate_reply(self, *, mode: str, facts: list[str], prompt: str, fallback: str) -> ArtemisModelReply:
        # The model is a wording layer only; callers must provide all facts and keep state decisions outside this service.
        if not settings.artemis_ollama_enabled:
            return ArtemisModelReply(ok=False, text=fallback, source="fallback", error="Ollama disabled")

        payload = {
            "model": settings.ollama_model,
            "system": SYSTEM_PROMPT,
            "prompt": self._build_prompt(mode, facts, prompt),
            "stream": False,
            "options": {
                "temperature": 0.15,
                "top_p": 0.85,
                "num_predict": 70,
            },
        }
        data = json.dumps(payload).encode("utf-8")
        endpoint = settings.ollama_url.rstrip("/") + "/api/generate"
        req = request.Request(
            endpoint,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json", "Content-Length": str(len(data))},
        )

        try:
            with request.urlopen(req, timeout=max(1, settings.ollama_timeout_ms / 1000)) as response:
                raw = response.read().decode("utf-8")
            parsed = json.loads(raw)
            text = str(parsed.get("response") or "").strip()
            if not text:
                raise ValueError("Ollama returned an empty response")
            return ArtemisModelReply(ok=True, text=text, source="ollama")
        except (OSError, ValueError, json.JSONDecodeError, error.HTTPError, error.URLError) as exc:
            return ArtemisModelReply(ok=False, text=fallback, source="fallback", error=str(exc))


artemis_ollama_service = ArtemisOllamaService()
