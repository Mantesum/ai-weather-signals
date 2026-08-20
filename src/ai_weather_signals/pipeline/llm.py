import json
import time
from hashlib import sha256
from typing import Any

import httpx

from ..config import Settings
from ..metrics import metrics
from ..schemas import LLMExtraction

PROMPT_VERSION = "weather-extraction-v2"
SYSTEM_PROMPT = """You classify a public message about actual weather. Return only schema-valid JSON.
An event is a candidate for a current personal/probable observation, a current official alert/report, or a
fresh publisher report describing a concrete weather event that has already happened or is happening now.
For source_kind=news use assertion_type=news, never official_report. For source_kind=official use
official_report when the item is a current alert or observation. A news item is corroboration, not proof.
Reject forecasts, future risks, old events, generic climate discussion, questions, negations, jokes,
metaphors, ads, spam and copies.
Copy an explicitly stated city or locality into place_name. Otherwise infer a place only when strongly implied
by source_region; use null when neither is available. Use ISO-8601 with timezone for observed_at.
The intensity, time_precision, and confidence fields are decimal scores from 0.0 to 1.0 only—never
percentages, durations, counts, or a 1-to-10 scale. time_precision measures certainty about observed_at:
1.0 means an exact time and 0.0 means a very uncertain time. rationale_code must be a short snake_case code,
not a sentence. Do not include personal data. /no_think"""


class LLMClassifier:
    prompt_version = PROMPT_VERSION

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self.settings = settings
        self.client = client or httpx.Client(timeout=90)

    @property
    def prompt_hash(self) -> str:
        return sha256(SYSTEM_PROMPT.encode()).hexdigest()

    def classify(
        self,
        text: str,
        source_region: str | None,
        published_at: str,
        source_kind: str = "social",
        timeout_seconds: float | None = None,
    ) -> LLMExtraction:
        schema = LLMExtraction.model_json_schema()
        messages: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "text": text[: self.settings.llm_max_input_chars],
                        "source_region": source_region,
                        "source_kind": source_kind,
                        "published_at": published_at,
                    },
                    ensure_ascii=False,
                ),
            },
        ]
        if self.settings.llm_provider == "ollama":
            url = f"{self.settings.llm_base_url.rstrip('/').removesuffix('/v1')}/api/chat"
            payload: dict[str, Any] = {
                "model": self.settings.llm_model,
                "messages": messages,
                "stream": False,
                "think": False,
                "keep_alive": "15m",
                "format": schema,
                "options": {
                    "temperature": 0.1,
                    "seed": 42,
                    "num_predict": 160,
                    "num_ctx": self.settings.llm_context_length,
                },
            }
        else:
            url = f"{self.settings.llm_base_url.rstrip('/')}/chat/completions"
            payload = {
                "model": self.settings.llm_model,
                "messages": messages,
                "temperature": 0.1,
                "seed": 42,
                "max_tokens": 160,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"name": "weather_signal", "strict": True, "schema": schema},
                },
            }
        headers = (
            {"Authorization": f"Bearer {self.settings.llm_api_key}"} if self.settings.llm_api_key else {}
        )
        deadline = time.monotonic() + timeout_seconds if timeout_seconds is not None else None
        last_error: Exception | None = None
        for _attempt in range(2):
            remaining = deadline - time.monotonic() if deadline is not None else None
            if remaining is not None and remaining <= 0:
                break
            try:
                response = self.client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=min(self.settings.llm_timeout_seconds, remaining)
                    if remaining is not None
                    else self.settings.llm_timeout_seconds,
                )
                response.raise_for_status()
                body = response.json()
                content = (
                    body["message"]["content"]
                    if self.settings.llm_provider == "ollama"
                    else body["choices"][0]["message"]["content"]
                )
                return LLMExtraction.model_validate_json(content)
            except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
                last_error = error
                metrics.inc("llm_invalid_or_failed_responses")
                if isinstance(error, httpx.TimeoutException):
                    break
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Previous output was invalid. Return one schema-valid JSON object only. "
                            "All score fields must be decimal numbers between 0.0 and 1.0."
                        ),
                    }
                )
                payload["messages"] = messages
        metrics.inc("llm_exhausted_retries")
        raise RuntimeError(f"LLM returned no valid extraction: {last_error}")
